import logging
from datetime import date, datetime
from typing import Optional, ClassVar

from pydantic import Field

from Base.Repository.models.defaultDbModel import DefaultDbModel
from .store import Store

logger = logging.getLogger(__name__)


class Review(DefaultDbModel):
    """评论表（风评分析）"""
    table_alias: ClassVar[str] = "review"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{table_alias}` (
        `id`            BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '评论ID',
        `store_id`      INT             NOT NULL                 COMMENT '门店ID',
        `platform`      VARCHAR(20)     NOT NULL                 COMMENT '平台: 美团/饿了么/大众点评',
        `rating`        TINYINT         NOT NULL                 COMMENT '评分: 1-5星',
        `content`       TEXT            NOT NULL                 COMMENT '评论内容',
        `review_date`   DATE            NOT NULL                 COMMENT '评论日期',
        `review_time`   DATETIME        NOT NULL                 COMMENT '评论时间',
        `tags`          VARCHAR(500)    DEFAULT NULL             COMMENT '标签(逗号分隔)',
        `is_replied`    TINYINT         DEFAULT 0                COMMENT '是否已回复',
        `reply_content` TEXT            DEFAULT NULL             COMMENT '回复内容',
        `is_positive`   TINYINT         DEFAULT 1                COMMENT '情感: 1正面 0中性 -1负面',
        `created_at`    DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        PRIMARY KEY (`id`),
        KEY `idx_review_date` (`review_date`),
        KEY `idx_store_rating` (`store_id`, `rating`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论表';
    """

    id: Optional[int] = Field(None, description="评论ID")
    store_id: int = Field(..., description="门店ID")
    platform: str = Field(..., description="平台")
    rating: int = Field(..., description="评分: 1-5星")
    content: str = Field(..., description="评论内容")
    review_date: date = Field(..., description="评论日期")
    review_time: datetime = Field(..., description="评论时间")
    tags: Optional[str] = Field(None, description="标签")
    is_replied: int = Field(0, description="是否已回复")
    reply_content: Optional[str] = Field(None, description="回复内容")
    is_positive: int = Field(1, description="情感: 1正面 0中性 -1负面")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    @classmethod
    def get_detail(cls, review_id: int) -> Optional[dict]:
        try:
            cls._ensure_table_exists()
            db = cls.get_db_connection()
            if db is None:
                return None

            review_table = cls.get_table_name_with_db()
            store_table = Store.get_table_name_with_db()
            sql = f"""SELECT r.*, s.`name` AS store_name
FROM {review_table} r
LEFT JOIN {store_table} s ON s.`id` = r.`store_id`
WHERE r.`id` = %s"""
            results = db.execute(sql, (review_id,))
            if not results:
                return None
            row = results[0]
            row_dict = dict(row)
            for k, v in row_dict.items():
                if hasattr(v, 'isocalendar'):
                    row_dict[k] = v.isoformat() if hasattr(v, 'isoformat') else str(v)
            return row_dict
        except Exception as e:
            logger.error(f"查询评论详情失败: {e}")
            return None

    @classmethod
    def get_paginated_list(cls, page: int = 1, page_size: int = 20,
                           store_id: Optional[int] = None,
                           platform: Optional[str] = None,
                           rating: Optional[int] = None,
                           is_positive: Optional[int] = None,
                           date_from: Optional[str] = None,
                           date_to: Optional[str] = None,
                           store_ids: Optional[list] = None) -> dict:
        try:
            cls._ensure_table_exists()
            db = cls.get_db_connection()
            if db is None:
                return {"total": 0, "page": page, "page_size": page_size, "data": []}

            table_name = cls.get_table_name_with_db()
            store_table = Store.get_table_name_with_db()
            where_clauses = []
            params = []

            if store_id is not None:
                where_clauses.append("r.`store_id` = %s")
                params.append(store_id)
            if store_ids is not None:
                placeholders = ",".join(["%s"] * len(store_ids))
                where_clauses.append(f"r.`store_id` IN ({placeholders})")
                params.extend(store_ids)
            if platform:
                where_clauses.append("r.`platform` = %s")
                params.append(platform)
            if rating is not None:
                where_clauses.append("r.`rating` = %s")
                params.append(rating)
            if is_positive is not None:
                where_clauses.append("r.`is_positive` = %s")
                params.append(is_positive)
            if date_from:
                where_clauses.append("r.`review_date` >= %s")
                params.append(date_from)
            if date_to:
                where_clauses.append("r.`review_date` <= %s")
                params.append(date_to)

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            count_sql = f"SELECT COUNT(*) AS total FROM {table_name} r {where_sql}"
            count_result = db.execute(count_sql, tuple(params))
            total = count_result[0]["total"] if count_result else 0

            offset = (page - 1) * page_size
            list_sql = f"""SELECT r.*, s.`name` AS store_name
FROM {table_name} r
LEFT JOIN {store_table} s ON s.`id` = r.`store_id`
{where_sql}
ORDER BY r.`review_time` DESC
LIMIT {offset}, {page_size}"""
            results = db.execute(list_sql, tuple(params))

            return {"total": total, "page": page, "page_size": page_size, "data": results or []}
        except Exception as e:
            logger.error(f"查询评论列表失败: {e}")
            return {"total": 0, "page": page, "page_size": page_size, "data": []}
