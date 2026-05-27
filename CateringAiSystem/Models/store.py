import logging
from datetime import date, datetime
from typing import Optional, ClassVar

from pydantic import Field

from Base.Repository.models.defaultDbModel import DefaultDbModel

logger = logging.getLogger(__name__)


class Store(DefaultDbModel):
    """门店信息表"""
    table_alias: ClassVar[str] = "store"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{table_alias}` (
        `id`            INT             NOT NULL AUTO_INCREMENT  COMMENT '门店ID',
        `name`          VARCHAR(100)    NOT NULL                 COMMENT '门店名称',
        `province`      VARCHAR(50)     NOT NULL                 COMMENT '所在省份',
        `city`          VARCHAR(50)     NOT NULL                 COMMENT '所在城市',
        `district`      VARCHAR(50)     DEFAULT NULL             COMMENT '所在区/县',
        `address`       VARCHAR(200)    DEFAULT NULL             COMMENT '详细地址',
        `phone`         VARCHAR(20)     DEFAULT NULL             COMMENT '联系电话',
        `open_date`     DATE            DEFAULT NULL             COMMENT '开业日期',
        `status`        TINYINT         DEFAULT 1                COMMENT '状态: 1营业 0停业',
        `level`         TINYINT         DEFAULT 2                COMMENT '门店等级: 1旗舰 2标准 3简配',
        `created_at`    DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at`    DATETIME        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        KEY `idx_city` (`city`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='门店信息表';
    """

    id: Optional[int] = Field(None, description="门店ID")
    name: str = Field(..., description="门店名称")
    province: str = Field(..., description="所在省份")
    city: str = Field(..., description="所在城市")
    district: Optional[str] = Field(None, description="所在区/县")
    address: Optional[str] = Field(None, description="详细地址")
    phone: Optional[str] = Field(None, description="联系电话")
    open_date: Optional[date] = Field(None, description="开业日期")
    status: int = Field(1, description="状态: 1营业 0停业")
    level: int = Field(2, description="门店等级: 1旗舰 2标准 3简配")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    @classmethod
    def get_paginated_list(cls, page: int = 1, page_size: int = 20,
                           province: Optional[str] = None,
                           city: Optional[str] = None,
                           status: Optional[int] = None,
                           store_ids: Optional[list] = None) -> dict:
        try:
            cls._ensure_table_exists()
            db = cls.get_db_connection()
            if db is None:
                return {"total": 0, "page": page, "page_size": page_size, "data": []}

            table_name = cls.get_table_name_with_db()
            where_clauses = []
            params = []

            if province:
                where_clauses.append("`province` = %s")
                params.append(province)
            if city:
                where_clauses.append("`city` = %s")
                params.append(city)
            if status is not None:
                where_clauses.append("`status` = %s")
                params.append(status)
            if store_ids is not None:
                placeholders = ",".join(["%s"] * len(store_ids))
                where_clauses.append(f"`id` IN ({placeholders})")
                params.extend(store_ids)

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            count_sql = f"SELECT COUNT(*) AS total FROM {table_name} {where_sql}"
            count_result = db.execute(count_sql, tuple(params))
            total = count_result[0]["total"] if count_result else 0

            offset = (page - 1) * page_size
            list_sql = f"""SELECT * FROM {table_name}
{where_sql}
ORDER BY `id` ASC
LIMIT {offset}, {page_size}"""
            results = db.execute(list_sql, tuple(params))

            return {"total": total, "page": page, "page_size": page_size, "data": results or []}
        except Exception as e:
            logger.error(f"查询门店列表失败: {e}")
            return {"total": 0, "page": page, "page_size": page_size, "data": []}
