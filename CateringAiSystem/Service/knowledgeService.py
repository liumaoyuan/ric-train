import asyncio
import logging
import os
import re
from typing import Optional

from pymilvus import CollectionSchema, FieldSchema, DataType

from Base.Client.milvusClient import MilvusClientSingleton
from Base.Client.minioClient import default_minio_client
from Base.Config.setting import settings
from Base.RicUtils.pdfUtils import PDFTextExtractor
from CateringAiSystem.Models.knowledgeModels import KnowledgeDocument, KnowledgeChunk

logger = logging.getLogger(__name__)

# Milvus 常量
MILVUS_COLLECTION = "knowledge_chunks"
VECTOR_DIM = settings.milvus.vector_dim or 768
MINIO_BUCKET = "knowledge-docs"

# 简单分词（用于粗略估算 token 数：中文字符 / 1.5 + 英文单词）
def _estimate_tokens(text: str) -> int:
    chinese_chars = len(re.findall(r'[一-鿿]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    other = len(text) - chinese_chars - sum(len(w) for w in re.findall(r'[a-zA-Z]+', text))
    return int(chinese_chars / 1.5 + english_words + other * 0.25)


class KnowledgeService:
    """知识库服务：文档上传、解析、分块、向量化、检索"""

    # ==================== 文档上传 ====================

    @staticmethod
    def upload(file, title: str, category: str, permission_scope: str,
               chunk_strategy: str, operator_id: int, remark: str = "") -> Optional[int]:
        """上传文档到 MinIO 并创建文档记录"""
        try:
            # 解析文件信息
            file_name = file.filename
            file_ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
            file_type = file_ext if file_ext in ("pdf", "doc", "docx", "txt", "md") else "other"
            file_size = 0

            # 上传到 MinIO
            os.makedirs("temp_uploads", exist_ok=True)
            temp_path = os.path.join("temp_uploads", file_name)
            try:
                with open(temp_path, "wb") as f:
                    content = file.read()
                    f.write(content)
                    file_size = len(content)
            except Exception:
                content = file.read()
                file_size = len(content)
                with open(temp_path, "wb") as f:
                    f.write(content)

            minio_path = f"knowledge/{file_name}"
            stored_name = default_minio_client.upload_file(
                bucket_name=MINIO_BUCKET,
                object_name=minio_path,
                file_path=temp_path,
            )

            # 清理临时文件
            try:
                os.remove(temp_path)
            except Exception:
                pass

            if stored_name is None:
                logger.error(f"MinIO 上传失败: {file_name}")
                return None

            # 创建文档记录
            doc = KnowledgeDocument(
                title=title,
                file_name=file_name,
                file_path=stored_name,
                file_size=file_size,
                file_type=file_type,
                category=category,
                chunk_strategy=chunk_strategy,
                permission_scope=permission_scope,
                status=0,
                remark=remark or "",
                created_by=operator_id,
                updated_by=operator_id,
            )
            doc_id = doc.save()
            return doc_id if doc_id > 0 else None
        except Exception as e:
            logger.error(f"上传文档失败: {e}")
            return None

    # ==================== 文档解析与分块 ====================

    @staticmethod
    def parse_and_chunk(doc_id: int) -> Optional[list]:
        """解析文档并分块（返回分块列表供预览）"""
        try:
            doc = KnowledgeDocument.get_by_id(doc_id)
            if doc is None:
                logger.warning(f"文档不存在: {doc_id}")
                return None

            # 从 MinIO 下载临时文件
            os.makedirs("temp_uploads", exist_ok=True)
            temp_path = os.path.join("temp_uploads", f"tmp_{doc_id}_{doc.file_name}")
            dl_path = default_minio_client.download_file(
                bucket_name=MINIO_BUCKET,
                object_name=doc.file_path,
                file_path=temp_path,
            )
            if dl_path is None:
                logger.error(f"MinIO 下载失败: {doc.file_path}")
                return None

            # 提取文本
            raw_text = KnowledgeService._extract_text(temp_path, doc.file_type)
            try:
                os.remove(temp_path)
            except Exception:
                pass

            if not raw_text:
                logger.warning(f"文档内容为空: {doc.file_name}")
                doc.update(status=3)
                return None

            # 分块
            chunks = KnowledgeService._chunk_text(raw_text, doc.chunk_strategy)

            # 删除旧分块（如果存在）
            KnowledgeChunk.delete_by_doc_id(doc_id)

            # 写入数据库
            saved_chunks = []
            for i, chunk_text in enumerate(chunks):
                chunk_text = chunk_text.strip()
                if not chunk_text:
                    continue
                token_count = _estimate_tokens(chunk_text)
                chunk = KnowledgeChunk(
                    doc_id=doc_id,
                    chunk_index=i,
                    chunk_content=chunk_text,
                    token_count=token_count,
                    approved=0,
                )
                cid = chunk.save()
                if cid and cid > 0:
                    saved_chunks.append({
                        "id": cid,
                        "chunk_index": i,
                        "chunk_content": chunk_text[:200] + ("..." if len(chunk_text) > 200 else ""),
                        "chunk_content_full": chunk_text,
                        "token_count": token_count,
                        "approved": 0,
                    })

            # 更新文档状态
            doc.update(status=1, chunk_count=len(saved_chunks))
            return saved_chunks
        except Exception as e:
            logger.error(f"解析文档失败: {e}")
            try:
                KnowledgeDocument.get_by_id(doc_id).update(status=3)
            except Exception:
                pass
            return None

    @staticmethod
    def _extract_text(file_path: str, file_type: str) -> Optional[str]:
        """根据文件类型提取文本"""
        try:
            if file_type == "pdf":
                extractor = PDFTextExtractor()
                return extractor.extract_text(file_path)
            elif file_type in ("doc", "docx"):
                try:
                    from docx import Document
                    doc = Document(file_path)
                    paragraphs = [p.text for p in doc.paragraphs]
                    return "\n".join(paragraphs)
                except ImportError:
                    logger.error("python-docx 未安装，无法解析 Word 文档")
                    return None
            elif file_type in ("txt", "md"):
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            else:
                logger.warning(f"不支持的文件类型: {file_type}")
                return None
        except Exception as e:
            logger.error(f"文本提取失败: {e}")
            return None

    @staticmethod
    def _chunk_text(text: str, strategy: str = "fixed") -> list:
        """根据策略对文本进行分块"""
        if strategy == "paragraph":
            # 按自然段落切分（连续换行分隔）
            paragraphs = re.split(r"\n\s*\n", text)
            return [p.strip() for p in paragraphs if p.strip()]
        elif strategy == "recursive":
            # 递归分块：先按段落，再按句子，最后按固定长度
            return KnowledgeService._recursive_chunk(text, max_tokens=500)
        else:  # fixed (默认)
            return KnowledgeService._fixed_chunk(text, max_tokens=500, overlap=50)

    @staticmethod
    def _fixed_chunk(text: str, max_tokens: int = 500, overlap: int = 50) -> list:
        """固定长度分块"""
        # 按中英文混排的近似 token 数切分
        # 先按句子切分（句号、问号、感叹号、换行）
        sentences = re.split(r"(?<=[。！？\n])\s*", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        current_chunk = ""
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = _estimate_tokens(sentence)
            if current_tokens + sentence_tokens > max_tokens and current_chunk:
                chunks.append(current_chunk)
                # overlap：保留最后 overlap 字符
                overlap_chars = min(len(current_chunk), overlap * 3)
                current_chunk = current_chunk[-overlap_chars:] if overlap_chars > 0 else ""
                current_tokens = _estimate_tokens(current_chunk)

            if current_chunk:
                current_chunk += sentence
            else:
                current_chunk = sentence
            current_tokens += sentence_tokens

        if current_chunk:
            chunks.append(current_chunk)

        return chunks if chunks else [text]

    @staticmethod
    def _recursive_chunk(text: str, max_tokens: int = 500) -> list:
        """递归分块"""
        # 先按段落
        paragraphs = re.split(r"\n\s*\n", text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks = []
        for para in paragraphs:
            if _estimate_tokens(para) <= max_tokens:
                chunks.append(para)
            else:
                # 段落太大，按句子切分
                sentences = re.split(r"(?<=[。！？])\s*", para)
                temp = ""
                for sent in sentences:
                    if _estimate_tokens(temp + sent) > max_tokens and temp:
                        chunks.append(temp)
                        temp = sent
                    else:
                        temp += sent
                if temp:
                    chunks.append(temp)

        return chunks

    # ==================== 确认向量化 ====================

    @staticmethod
    def confirm_vectorize(doc_id: int, chunk_ids: Optional[list] = None) -> bool:
        """确认分块并向量化写入 Milvus"""
        try:
            doc = KnowledgeDocument.get_by_id(doc_id)
            if doc is None:
                logger.warning(f"文档不存在: {doc_id}")
                return False

            # 获取已确认的分块
            if chunk_ids:
                KnowledgeChunk.batch_approve(chunk_ids)

            chunks = KnowledgeChunk.get_by_doc_id(doc_id, approved_only=True)
            if not chunks:
                logger.warning(f"没有已确认的分块: {doc_id}")
                return False

            # 获取 Qwen Embedding
            try:
                from Base.Ai.llms.qwenLlm import QwenLlm
                llm = QwenLlm()
            except Exception:
                logger.error("无法初始化 QwenLlm")
                return False

            # 准备 Milvus 数据
            milvus_data = []
            for chunk in chunks:
                text = chunk.chunk_content
                if not text:
                    continue
                try:
                    vector = llm.embedding(text=text, dimensions=VECTOR_DIM)[0]
                except Exception as e:
                    logger.error(f"Embedding 失败 (chunk {chunk.id}): {e}")
                    continue

                milvus_data.append({
                    "embedding": vector,
                    "text": text[:65500],
                    "doc_id": doc_id,
                    "category": doc.category or "",
                    "permission_scope": doc.permission_scope or "all",
                    "chunk_index": chunk.chunk_index,
                })

            if not milvus_data:
                logger.warning("没有可向量化的分块")
                return False

            # 创建或确保 Milvus 集合存在
            KnowledgeService._ensure_milvus_collection()

            # 写入 Milvus
            milvus_client = MilvusClientSingleton()
            result = milvus_client.insert(collection_name=MILVUS_COLLECTION, data=milvus_data)
            if not result.get("success"):
                logger.error(f"Milvus 插入失败: {result}")
                return False

            # 更新文档状态
            doc.update(status=2, chunk_count=len(chunks))
            logger.info(f"文档向量化成功: {doc.title} ({len(chunks)} 个分块)")

            # 向量化完成后触发 RAGAS 评估（异步执行，失败不影响主流程）
            try:
                from CateringAiSystem.Agent.evaluation.ragas_eval import evaluate_after_vectorize
                import threading
                threading.Thread(
                    target=lambda: asyncio.run(evaluate_after_vectorize(doc_id)),
                    daemon=True,
                ).start()
            except Exception as eval_err:
                logger.warning(f"RAGAS 评估触发失败（不影响向量化）: {eval_err}")

            return True
        except Exception as e:
            logger.error(f"向量化失败: {e}")
            return False

    @staticmethod
    def _ensure_milvus_collection():
        """确保知识库 Milvus 集合存在"""
        client = MilvusClientSingleton()
        if client.get_client().has_collection(MILVUS_COLLECTION):
            if not client.get_client().get_load_state(collection_name=MILVUS_COLLECTION).get("state") == "Loaded":
                client.get_client().load_collection(collection_name=MILVUS_COLLECTION)
            return

        # 自定义 Schema
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=VECTOR_DIM),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65500),
            FieldSchema(name="doc_id", dtype=DataType.INT64),
            FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="permission_scope", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
        ]
        schema = CollectionSchema(fields, description="知识库文档向量集合")

        client.create_collection(
            collection_name=MILVUS_COLLECTION,
            schema=schema,
            description="知识库文档向量",
        )

    # ==================== RAG 检索 ====================

    @staticmethod
    def search(query: str, permission_scope: str = "all", top_k: int = 5) -> list:
        """知识库检索（基于 Milvus 向量相似度搜索）"""
        try:
            # 获取 query 的 embedding
            try:
                from Base.Ai.llms.qwenLlm import QwenLlm
                llm = QwenLlm()
                query_vector = llm.embedding(text=query, dimensions=VECTOR_DIM)[0]
            except Exception as e:
                logger.error(f"Query Embedding 失败: {e}")
                return []

            # Milvus 检索
            milvus_client = MilvusClientSingleton()
            if not milvus_client.get_client().has_collection(MILVUS_COLLECTION):
                logger.warning(f"Milvus 集合不存在: {MILVUS_COLLECTION}")
                return []

            # 权限过滤
            filter_expr = ""
            if permission_scope == "employee_only":
                filter_expr = 'permission_scope in ["all", "employee_only"]'
            elif permission_scope == "franchisee_only":
                filter_expr = 'permission_scope in ["all", "franchisee_only"]'
            elif permission_scope == "all":
                filter_expr = ""

            search_params = {
                "metric_type": "COSINE",
                "params": {"ef": 64},
            }
            results = milvus_client.search(
                collection_name=MILVUS_COLLECTION,
                data=[query_vector],
                anns_field="embedding",
                search_params=search_params,
                limit=top_k,
                filter_expr=filter_expr,
                output_fields=["text", "doc_id", "category", "chunk_index"],
            )

            # 格式化结果
            formatted = []
            for hits in results:
                for hit in hits:
                    formatted.append({
                        "id": hit["id"],
                        "score": hit["distance"],
                        "text": hit["entity"]["text"],
                        "doc_id": hit["entity"]["doc_id"],
                        "category": hit["entity"]["category"],
                        "chunk_index": hit["entity"]["chunk_index"],
                    })
            return formatted
        except Exception as e:
            logger.error(f"知识库检索失败: {e}")
            return []

    # ==================== 文档 CRUD ====================

    @staticmethod
    def get_list(page: int = 1, page_size: int = 20,
                 title: Optional[str] = None,
                 category: Optional[str] = None,
                 status: Optional[int] = None) -> dict:
        return KnowledgeDocument.get_paginated_list(page, page_size, title, category, status)

    @staticmethod
    def get_detail(doc_id: int) -> Optional[dict]:
        doc = KnowledgeDocument.get_by_id(doc_id)
        if doc is None:
            return None
        return {
            "id": doc.id,
            "title": doc.title,
            "file_name": doc.file_name,
            "file_path": doc.file_path,
            "file_size": doc.file_size,
            "file_type": doc.file_type,
            "category": doc.category,
            "chunk_strategy": doc.chunk_strategy,
            "permission_scope": doc.permission_scope,
            "status": doc.status,
            "chunk_count": doc.chunk_count,
            "remark": doc.remark,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at,
            "created_by": doc.created_by,
        }

    @staticmethod
    def update(doc_id: int, data: dict, operator_id: int = 0) -> bool:
        try:
            doc = KnowledgeDocument.get_by_id(doc_id)
            if doc is None:
                return False
            update_fields = {}
            for field in ["title", "category", "permission_scope", "remark"]:
                if field in data:
                    update_fields[field] = data[field]
            if "status" in data:
                update_fields["status"] = data["status"]
            update_fields["updated_by"] = operator_id
            return doc.update(**update_fields)
        except Exception as e:
            logger.error(f"更新文档失败: {e}")
            return False

    @staticmethod
    def delete(doc_id: int) -> bool:
        try:
            doc = KnowledgeDocument.get_by_id(doc_id)
            if doc is None:
                return False

            # 删除 MinIO 文件
            if doc.file_path:
                try:
                    default_minio_client.remove_object(MINIO_BUCKET, doc.file_path)
                except Exception as e:
                    logger.warning(f"MinIO 删除文件失败: {e}")

            # 删除 Milvus 向量
            try:
                milvus_client = MilvusClientSingleton()
                if milvus_client.get_client().has_collection(MILVUS_COLLECTION):
                    milvus_client.delete(
                        collection_name=MILVUS_COLLECTION,
                        filter=f"doc_id == {doc_id}",
                    )
            except Exception as e:
                logger.warning(f"Milvus 删除向量失败: {e}")

            # 删除数据库记录
            return KnowledgeDocument.delete_cascade(doc_id)
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False

    @staticmethod
    def get_chunks(doc_id: int) -> list:
        """获取文档的分块列表"""
        chunks = KnowledgeChunk.get_by_doc_id(doc_id)
        return [
            {
                "id": c.id,
                "chunk_index": c.chunk_index,
                "chunk_content": c.chunk_content,
                "token_count": c.token_count,
                "approved": c.approved,
            }
            for c in chunks
        ]
