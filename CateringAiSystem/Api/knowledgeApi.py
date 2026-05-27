import logging
from typing import Optional

from fastapi import APIRouter, Request, Query, UploadFile, File, Form

from CateringAiSystem.Service.knowledgeService import KnowledgeService
from CateringAiSystem.Utils.rbacUtils import get_current_user, require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/knowledge", tags=["知识库管理"])


@router.post("/upload")
@require_permission("knowledge:upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form(""),
    permission_scope: str = Form("all"),
    chunk_strategy: str = Form("fixed"),
    remark: str = Form(""),
):
    """上传知识文档"""
    user = get_current_user(request)
    if not file.filename:
        return {"code": 400, "msg": "文件不能为空", "data": None}

    doc_id = KnowledgeService.upload(
        file=file,
        title=title,
        category=category,
        permission_scope=permission_scope,
        chunk_strategy=chunk_strategy,
        operator_id=user["user_id"],
        remark=remark,
    )
    if doc_id is None:
        return {"code": 500, "msg": "上传失败", "data": None}
    return {"code": 200, "msg": "上传成功", "data": {"id": doc_id}}


@router.get("/list")
@require_permission("knowledge:list")
def list_documents(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    title: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[int] = None,
):
    """文档列表"""
    data = KnowledgeService.get_list(page, page_size, title, category, status)
    return {"code": 200, "msg": "success", "data": data}


@router.get("/{doc_id}")
@require_permission("knowledge:list")
def get_document(doc_id: int, request: Request):
    """文档详情"""
    data = KnowledgeService.get_detail(doc_id)
    if data is None:
        return {"code": 404, "msg": "文档不存在", "data": None}
    return {"code": 200, "msg": "success", "data": data}


@router.put("/{doc_id}")
@require_permission("knowledge:edit")
def update_document(doc_id: int, data: dict, request: Request):
    """编辑文档"""
    user = get_current_user(request)
    success = KnowledgeService.update(doc_id, data, operator_id=user["user_id"])
    if not success:
        return {"code": 404, "msg": "文档不存在或更新失败", "data": None}
    return {"code": 200, "msg": "更新成功", "data": None}


@router.delete("/{doc_id}")
@require_permission("knowledge:delete")
def delete_document(doc_id: int, request: Request):
    """删除文档"""
    success = KnowledgeService.delete(doc_id)
    if not success:
        return {"code": 404, "msg": "文档不存在或删除失败", "data": None}
    return {"code": 200, "msg": "删除成功", "data": None}


@router.post("/{doc_id}/preview")
@require_permission("knowledge:preview")
def preview_chunks(doc_id: int, request: Request):
    """分块预览（解析文档并返回分块列表供确认）"""
    chunks = KnowledgeService.parse_and_chunk(doc_id)
    if chunks is None:
        return {"code": 404, "msg": "文档不存在或解析失败", "data": None}
    return {"code": 200, "msg": "success", "data": {"chunks": chunks, "total": len(chunks)}}


@router.post("/{doc_id}/vectorize")
@require_permission("knowledge:vectorize")
def vectorize_document(doc_id: int, data: dict, request: Request):
    """确认向量化（可选指定 chunk_ids）"""
    chunk_ids = data.get("chunk_ids")
    success = KnowledgeService.confirm_vectorize(doc_id, chunk_ids)
    if not success:
        return {"code": 500, "msg": "向量化失败", "data": None}
    return {"code": 200, "msg": "向量化成功", "data": None}


@router.post("/search")
def search_knowledge(request: Request, data: dict):
    """知识库检索（RAG 检索，登录用户可用）"""
    user = get_current_user(request)
    query = data.get("query", "")
    top_k = data.get("top_k", 5)

    if not query:
        return {"code": 400, "msg": "查询内容不能为空", "data": None}

    # 权限范围：加盟商只能检索加盟商可见内容
    roles = user.get("roles", [])
    if "franchisee" in roles and "employee" not in roles and "admin" not in roles:
        permission_scope = "franchisee_only"
    elif "employee" in roles or "admin" in roles:
        permission_scope = "all"
    else:
        permission_scope = "all"

    results = KnowledgeService.search(query, permission_scope=permission_scope, top_k=top_k)
    return {"code": 200, "msg": "success", "data": {"results": results}}


@router.get("/{doc_id}/chunks")
@require_permission("knowledge:list")
def get_document_chunks(doc_id: int, request: Request):
    """获取文档的分块列表"""
    chunks = KnowledgeService.get_chunks(doc_id)
    return {"code": 200, "msg": "success", "data": {"chunks": chunks}}
