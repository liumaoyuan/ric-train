import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, ClassVar

from pydantic import Field

from Base.Repository.models.defaultDbModel import DefaultDbModel

logger = logging.getLogger(__name__)


class Dish(DefaultDbModel):
    """菜品信息表"""
    table_alias: ClassVar[str] = "dish"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{{table_name}}` (
        `id`            INT             NOT NULL AUTO_INCREMENT  COMMENT '菜品ID',
        `name`          VARCHAR(100)    NOT NULL                 COMMENT '菜品名称',
        `category`      VARCHAR(50)     NOT NULL                 COMMENT '分类: 热菜/凉菜/主食/汤品/饮品/配菜',
        `price`         DECIMAL(10,2)   NOT NULL                 COMMENT '标准价格',
        `cost`          DECIMAL(10,2)   DEFAULT NULL             COMMENT '成本',
        `unit`          VARCHAR(10)     DEFAULT '份'             COMMENT '单位',
        `spicy_level`   TINYINT         DEFAULT 0                COMMENT '辣度: 0不辣 1微辣 2中辣 3重辣',
        `popularity`    INT             DEFAULT 50               COMMENT 'popularity 权重(用于生成销量)',
        `image_url`     VARCHAR(255)    DEFAULT NULL             COMMENT '图片URL',
        `status`        TINYINT         DEFAULT 1                COMMENT '状态: 1上架 0下架',
        `created_at`    DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='菜品信息表';
    """

    id: Optional[int] = Field(None, description="菜品ID")
    name: str = Field(..., description="菜品名称")
    category: str = Field(..., description="分类: 热菜/凉菜/主食/汤品/饮品/配菜")
    price: Decimal = Field(..., description="标准价格")
    cost: Optional[Decimal] = Field(None, description="成本")
    unit: str = Field("份", description="单位")
    spicy_level: int = Field(0, description="辣度: 0不辣 1微辣 2中辣 3重辣")
    popularity: int = Field(50, description="popularity 权重")
    image_url: Optional[str] = Field(None, description="图片URL")
    status: int = Field(1, description="状态: 1上架 0下架")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    @classmethod
    def get_paginated_list(cls, page: int = 1, page_size: int = 20,
                           category: Optional[str] = None,
                           status: Optional[int] = None,
                           keyword: Optional[str] = None) -> dict:
        try:
            db = cls.get_db_connection()
            if db is None:
                return {"total": 0, "page": page, "page_size": page_size, "data": []}

            table_name = cls.get_table_name_with_db()
            where_clauses = []
            params = []

            if category:
                where_clauses.append("`category` = %s")
                params.append(category)
            if status is not None:
                where_clauses.append("`status` = %s")
                params.append(status)
            if keyword:
                where_clauses.append("`name` LIKE %s")
                params.append(f"%{keyword}%")

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
            logger.error(f"查询菜品列表失败: {e}")
            return {"total": 0, "page": page, "page_size": page_size, "data": []}
