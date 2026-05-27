import logging
from datetime import datetime
from typing import Optional, ClassVar

from pydantic import Field

from Base.Repository.models.defaultDbModel import DefaultDbModel

logger = logging.getLogger(__name__)


class KnowledgeDocument(DefaultDbModel):
    """知识库文档表"""
    table_alias: ClassVar[str] = "knowledge_document"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{table_alias}` (
        `id`               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '文档ID',
        `title`            VARCHAR(200)    NOT NULL                 COMMENT '文档标题',
        `file_name`        VARCHAR(255)    NOT NULL                 COMMENT '原始文件名',
        `file_path`        VARCHAR(500)    NOT NULL                 COMMENT 'MinIO存储路径',
        `file_size`        BIGINT UNSIGNED NOT NULL DEFAULT 0       COMMENT '文件大小(字节)',
        `file_type`        VARCHAR(20)     NOT NULL DEFAULT ''      COMMENT '文件类型(pdf/doc/docx/txt/md)',
        `category`         VARCHAR(50)     NOT NULL DEFAULT ''      COMMENT '知识分类',
        `chunk_strategy`   VARCHAR(20)     NOT NULL DEFAULT 'fixed' COMMENT '分块策略(fixed/paragraph/recursive/qa)',
        `permission_scope` VARCHAR(30)     NOT NULL DEFAULT 'all'   COMMENT '权限范围(all/employee_only/franchisee_only)',
        `status`           TINYINT UNSIGNED NOT NULL DEFAULT 0      COMMENT '状态: 0=待处理 1=分块预览中 2=已向量化 3=失败',
        `chunk_count`      INT UNSIGNED    NOT NULL DEFAULT 0       COMMENT '分块数量',
        `remark`           VARCHAR(500)    DEFAULT NULL             COMMENT '备注',
        `created_at`       DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at`       DATETIME        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        `created_by`       BIGINT UNSIGNED DEFAULT NULL             COMMENT '创建人ID',
        `updated_by`       BIGINT UNSIGNED DEFAULT NULL             COMMENT '更新人ID',
        PRIMARY KEY (`id`),
        KEY `idx_category` (`category`),
        KEY `idx_status` (`status`),
        KEY `idx_created_at` (`created_at`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库文档表';
    """

    id: Optional[int] = Field(None, description="文档ID")
    title: str = Field(..., description="文档标题")
    file_name: str = Field(..., description="原始文件名")
    file_path: str = Field(..., description="MinIO存储路径")
    file_size: int = Field(0, description="文件大小(字节)")
    file_type: str = Field("", description="文件类型")
    category: str = Field("", description="知识分类")
    chunk_strategy: str = Field("fixed", description="分块策略")
    permission_scope: str = Field("all", description="权限范围")
    status: int = Field(0, description="状态: 0=待处理 1=分块预览中 2=已向量化 3=失败")
    chunk_count: int = Field(0, description="分块数量")
    remark: Optional[str] = Field(None, description="备注")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人ID")
    updated_by: Optional[int] = Field(None, description="更新人ID")

    @classmethod
    def get_paginated_list(cls, page: int = 1, page_size: int = 20,
                           title: Optional[str] = None,
                           category: Optional[str] = None,
                           status: Optional[int] = None) -> dict:
        """分页查询文档列表"""
        try:
            cls._ensure_table_exists()
            db = cls.get_db_connection()
            if db is None:
                return {"total": 0, "page": page, "page_size": page_size, "data": []}

            table_name = cls.get_table_name_with_db()
            where_clauses = []
            params = []

            if title:
                where_clauses.append("`title` LIKE %s")
                params.append(f"%{title}%")
            if category:
                where_clauses.append("`category` = %s")
                params.append(category)
            if status is not None:
                where_clauses.append("`status` = %s")
                params.append(status)

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            count_sql = f"SELECT COUNT(*) AS total FROM {table_name} {where_sql}"
            count_result = db.execute(count_sql, tuple(params))
            total = count_result[0]["total"] if count_result else 0

            offset = (page - 1) * page_size
            list_sql = f"""SELECT `id`, `title`, `file_name`, `file_size`, `file_type`,
`category`, `chunk_strategy`, `permission_scope`, `status`, `chunk_count`,
`remark`, `created_at`, `updated_at`, `created_by`
FROM {table_name}
{where_sql}
ORDER BY `created_at` DESC
LIMIT {offset}, {page_size}"""
            results = db.execute(list_sql, tuple(params))

            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "data": results or [],
            }
        except Exception as e:
            logger.error(f"查询知识库文档列表失败: {e}")
            return {"total": 0, "page": page, "page_size": page_size, "data": []}

    @classmethod
    def delete_cascade(cls, doc_id: int) -> bool:
        """删除文档及其分块记录"""
        try:
            cls._ensure_table_exists()
            db = cls.get_db_connection()
            if db is None:
                return False
            chunk_table = KnowledgeChunk.get_table_name_with_db()
            db.execute(f"DELETE FROM {chunk_table} WHERE `doc_id` = %s", (doc_id,), commit=True)
            return cls.delete_by_id(doc_id)
        except Exception as e:
            logger.error(f"删除知识库文档失败: {e}")
            return False


class KnowledgeChunk(DefaultDbModel):
    """知识库文档分块表"""
    table_alias: ClassVar[str] = "knowledge_chunk"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{table_alias}` (
        `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '分块ID',
        `doc_id`        BIGINT UNSIGNED NOT NULL                 COMMENT '文档ID',
        `chunk_index`   INT UNSIGNED    NOT NULL DEFAULT 0       COMMENT '分块序号',
        `chunk_content` TEXT            NOT NULL                 COMMENT '分块内容',
        `vector_id`     BIGINT          DEFAULT NULL             COMMENT 'Milvus向量ID',
        `token_count`   INT UNSIGNED    DEFAULT 0                COMMENT '预估token数',
        `approved`      TINYINT UNSIGNED NOT NULL DEFAULT 0      COMMENT '是否确认: 0=待确认 1=已确认',
        `created_at`    DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        PRIMARY KEY (`id`),
        KEY `idx_doc_id` (`doc_id`),
        KEY `idx_approved` (`approved`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库文档分块表';
    """

    id: Optional[int] = Field(None, description="分块ID")
    doc_id: int = Field(..., description="文档ID")
    chunk_index: int = Field(0, description="分块序号")
    chunk_content: str = Field(..., description="分块内容")
    vector_id: Optional[int] = Field(None, description="Milvus向量ID")
    token_count: int = Field(0, description="预估token数")
    approved: int = Field(0, description="是否确认: 0=待确认 1=已确认")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    @classmethod
    def get_by_doc_id(cls, doc_id: int, approved_only: bool = False) -> list:
        """获取文档的所有分块"""
        try:
            cls._ensure_table_exists()
            filters = {"doc_id": doc_id}
            if approved_only:
                filters["approved"] = 1
            return cls.find_by(**filters, order_by="chunk_index", order="ASC")
        except Exception as e:
            logger.error(f"查询文档分块失败: {e}")
            return []

    @classmethod
    def batch_approve(cls, chunk_ids: list) -> bool:
        """批量确认分块"""
        try:
            cls._ensure_table_exists()
            db = cls.get_db_connection()
            if db is None:
                return False
            table_name = cls.get_table_name_with_db()
            ids = ",".join([str(cid) for cid in chunk_ids])
            sql = f"UPDATE {table_name} SET `approved` = 1 WHERE `id` IN ({ids})"
            db.execute(sql, commit=True)
            return True
        except Exception as e:
            logger.error(f"批量确认分块失败: {e}")
            return False

    @classmethod
    def delete_by_doc_id(cls, doc_id: int) -> bool:
        """删除文档的所有分块记录"""
        try:
            cls._ensure_table_exists()
            db = cls.get_db_connection()
            if db is None:
                return False
            table_name = cls.get_table_name_with_db()
            db.execute(f"DELETE FROM {table_name} WHERE `doc_id` = %s", (doc_id,), commit=True)
            return True
        except Exception as e:
            logger.error(f"删除文档分块失败: {e}")
            return False
