import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, ClassVar

from pydantic import Field

from Base.Repository.models.defaultDbModel import DefaultDbModel
from .store import Store

logger = logging.getLogger(__name__)


class DailySummary(DefaultDbModel):
    """营业汇总表（每日每店一条记录）"""
    table_alias: ClassVar[str] = "daily_summary"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{{table_name}}` (
        `id`                BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '记录ID',
        `store_id`          INT             NOT NULL                 COMMENT '门店ID',
        `summary_date`      DATE            NOT NULL                 COMMENT '日期',
        `total_revenue`     DECIMAL(12,2)   NOT NULL DEFAULT 0.00    COMMENT '总营业额',
        `total_orders`      INT             NOT NULL DEFAULT 0       COMMENT '总订单数',
        `total_customers`   INT             NOT NULL DEFAULT 0       COMMENT '总顾客数',
        `avg_price`         DECIMAL(5,2)    NOT NULL DEFAULT 0.00    COMMENT '客单价',
        `dine_in_revenue`   DECIMAL(12,2)   NOT NULL DEFAULT 0.00    COMMENT '堂食收入',
        `takeout_revenue`   DECIMAL(12,2)   NOT NULL DEFAULT 0.00    COMMENT '外卖收入',
        `peak_hour_revenue` DECIMAL(12,2)   DEFAULT NULL             COMMENT '高峰时段收入',
        `dish_total_count`  INT             NOT NULL DEFAULT 0       COMMENT '菜品销售总份数',
        `is_holiday`        TINYINT         NOT NULL DEFAULT 0       COMMENT '是否节假日',
        `created_at`        DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uk_store_date` (`store_id`, `summary_date`),
        KEY `idx_date` (`summary_date`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='营业汇总表';
    """

    id: Optional[int] = Field(None, description="记录ID")
    store_id: int = Field(..., description="门店ID")
    summary_date: date = Field(..., description="日期")
    total_revenue: Decimal = Field(0.00, description="总营业额")
    total_orders: int = Field(0, description="总订单数")
    total_customers: int = Field(0, description="总顾客数")
    avg_price: Decimal = Field(0.00, description="客单价")
    dine_in_revenue: Decimal = Field(0.00, description="堂食收入")
    takeout_revenue: Decimal = Field(0.00, description="外卖收入")
    peak_hour_revenue: Optional[Decimal] = Field(None, description="高峰时段收入")
    dish_total_count: int = Field(0, description="菜品销售总份数")
    is_holiday: int = Field(0, description="是否节假日")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    @classmethod
    def get_paginated_list(cls, page: int = 1, page_size: int = 20,
                           store_id: Optional[int] = None,
                           date_from: Optional[str] = None,
                           date_to: Optional[str] = None,
                           store_ids: Optional[list] = None) -> dict:
        try:
            db = cls.get_db_connection()
            if db is None:
                return {"total": 0, "page": page, "page_size": page_size, "data": []}

            table_name = cls.get_table_name_with_db()
            store_table = Store.get_table_name_with_db()
            where_clauses = []
            params = []

            if store_id is not None:
                where_clauses.append("ds.`store_id` = %s")
                params.append(store_id)
            if store_ids is not None:
                placeholders = ",".join(["%s"] * len(store_ids))
                where_clauses.append(f"ds.`store_id` IN ({placeholders})")
                params.extend(store_ids)
            if date_from:
                where_clauses.append("ds.`summary_date` >= %s")
                params.append(date_from)
            if date_to:
                where_clauses.append("ds.`summary_date` <= %s")
                params.append(date_to)

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            count_sql = f"SELECT COUNT(*) AS total FROM {table_name} ds {where_sql}"
            count_result = db.execute(count_sql, tuple(params))
            total = count_result[0]["total"] if count_result else 0

            offset = (page - 1) * page_size
            list_sql = f"""SELECT ds.*, s.`name` AS store_name
FROM {table_name} ds
LEFT JOIN {store_table} s ON s.`id` = ds.`store_id`
{where_sql}
ORDER BY ds.`summary_date` DESC, ds.`store_id` ASC
LIMIT {offset}, {page_size}"""
            results = db.execute(list_sql, tuple(params))

            return {"total": total, "page": page, "page_size": page_size, "data": results or []}
        except Exception as e:
            logger.error(f"查询营业汇总列表失败: {e}")
            return {"total": 0, "page": page, "page_size": page_size, "data": []}

    @classmethod
    def get_stat(cls, store_id: Optional[int] = None,
                 date_from: Optional[str] = None,
                 date_to: Optional[str] = None,
                 store_ids: Optional[list] = None) -> dict:
        try:
            db = cls.get_db_connection()
            if db is None:
                return {}

            table_name = cls.get_table_name_with_db()
            where_clauses = []
            params = []

            if store_id is not None:
                where_clauses.append("`store_id` = %s")
                params.append(store_id)
            if store_ids is not None:
                placeholders = ",".join(["%s"] * len(store_ids))
                where_clauses.append(f"`store_id` IN ({placeholders})")
                params.extend(store_ids)
            if date_from:
                where_clauses.append("`summary_date` >= %s")
                params.append(date_from)
            if date_to:
                where_clauses.append("`summary_date` <= %s")
                params.append(date_to)

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            sql = f"""SELECT
    COUNT(DISTINCT `store_id`) AS store_count,
    COUNT(*) AS day_count,
    SUM(`total_revenue`) AS total_revenue,
    SUM(`total_orders`) AS total_orders,
    AVG(`avg_price`) AS avg_price,
    SUM(`dine_in_revenue`) AS total_dine_in,
    SUM(`takeout_revenue`) AS total_takeout,
    SUM(`peak_hour_revenue`) AS total_peak_hour
FROM {table_name}
{where_sql}"""
            results = db.execute(sql, tuple(params))
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"查询营业汇总统计失败: {e}")
            return {}
