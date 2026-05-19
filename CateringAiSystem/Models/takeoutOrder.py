import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, ClassVar

from pydantic import Field

from Base.Repository.models.defaultDbModel import DefaultDbModel
from .store import Store
from .dish import Dish
from .orderItem import OrderItem

logger = logging.getLogger(__name__)


class TakeoutOrder(DefaultDbModel):
    """外卖订单表"""
    table_alias: ClassVar[str] = "takeout_order"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{{table_name}}` (
        `id`                BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '订单ID',
        `store_id`          INT             NOT NULL                 COMMENT '门店ID',
        `order_no`          VARCHAR(50)     NOT NULL                 COMMENT '订单号',
        `total_amount`      DECIMAL(10,2)   NOT NULL DEFAULT 0.00    COMMENT '订单总金额',
        `platform`          VARCHAR(20)     NOT NULL                 COMMENT '外卖平台',
        `dish_count`        TINYINT         NOT NULL DEFAULT 0       COMMENT '菜品数量',
        `order_time`        DATETIME        NOT NULL                 COMMENT '下单时间',
        `created_at`        DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uk_order_no` (`order_no`),
        KEY `idx_store_time` (`store_id`, `order_time`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外卖订单表';
    """

    id: Optional[int] = Field(None, description="订单ID")
    store_id: int = Field(..., description="门店ID")
    order_no: str = Field(..., description="订单号")
    total_amount: Decimal = Field(0.00, description="订单总金额")
    platform: str = Field(..., description="外卖平台")
    dish_count: int = Field(0, description="菜品数量")
    order_time: datetime = Field(..., description="下单时间")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    @classmethod
    def get_list(cls, page: int = 1, page_size: int = 20,
                 store_id: Optional[int] = None,
                 date_from: Optional[str] = None,
                 date_to: Optional[str] = None,
                 store_ids: Optional[list] = None) -> dict:
        """外卖订单分页列表"""
        try:
            table_name = cls.get_table_name_with_db()
            store_table = Store.get_table_name_with_db()
            db = cls.get_db_connection()
            if db is None:
                return {"total": 0, "page": page, "page_size": page_size, "data": []}

            where_clauses = []
            params = []

            if store_id is not None:
                where_clauses.append("t.`store_id` = %s")
                params.append(store_id)
            elif store_ids is not None:
                placeholders = ",".join(["%s"] * len(store_ids))
                where_clauses.append(f"t.`store_id` IN ({placeholders})")
                params.extend(store_ids)
            if date_from and date_to:
                date_from = date_from + " 00:00:00"
                date_to = date_to + " 23:59:59"
                where_clauses.append("d.`order_time` BETWEEN %s AND %s")
                params.extend([date_from, date_to])

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            count_sql = f"SELECT COUNT(*) AS total FROM {table_name} t {where_sql}"
            count_result = db.execute(count_sql, tuple(params))
            total = count_result[0]["total"] if count_result else 0
            if total == 0:
                return {"total": 0, "page": page, "page_size": page_size, "data": []}

            offset = (page - 1) * page_size
            list_sql = f"""SELECT t.*, s.`name` AS store_name
FROM {table_name} t
LEFT JOIN {store_table} s ON s.`id` = t.`store_id`
{where_sql}
ORDER BY t.`order_time` DESC
LIMIT {page_size} OFFSET {offset}"""
            rows = db.execute(list_sql, tuple(params)) or []

            data = []
            for row in rows:
                data.append({
                    "id": row["id"],
                    "store_id": row["store_id"],
                    "store_name": row.get("store_name", ""),
                    "order_no": row["order_no"],
                    "total_amount": float(row["total_amount"]),
                    "platform": row["platform"],
                    "dish_count": row["dish_count"],
                    "order_time": row["order_time"].isoformat() if hasattr(row["order_time"], "isoformat") else str(row["order_time"]),
                    "created_at": row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") and row["created_at"] else None,
                })

            return {"total": total, "page": page, "page_size": page_size, "data": data}
        except Exception as e:
            logger.error(f"查询外卖订单列表失败: {e}", exc_info=True)
            return {"total": 0, "page": page, "page_size": page_size, "data": []}

    @classmethod
    def get_detail_by_no(cls, order_no: str) -> Optional[dict]:
        """外卖订单详情（含菜品明细）"""
        try:
            table_name = cls.get_table_name_with_db()
            store_table = Store.get_table_name_with_db()
            item_table = OrderItem.get_table_name_with_db()

            db = cls.get_db_connection()
            if db is None:
                return None

            sql = f"""SELECT t.*, s.`name` AS store_name
FROM {table_name} t
LEFT JOIN {store_table} s ON s.`id` = t.`store_id`
WHERE t.`order_no` = %s"""
            results = db.execute(sql, (order_no,))
            if not results:
                return None
            order = results[0]

            item_sql = f"""SELECT oi.*, dish.`image_url`
FROM {item_table} oi
LEFT JOIN {Dish.get_table_name_with_db()} dish ON dish.`id` = oi.`dish_id`
WHERE oi.`order_no` = %s"""
            items = db.execute(item_sql, (order_no,)) or []

            return {
                "order_no": order["order_no"],
                "store_id": order["store_id"],
                "store_name": order.get("store_name", ""),
                "total_amount": float(order["total_amount"]),
                "dish_count": order["dish_count"],
                "order_time": order["order_time"].isoformat() if hasattr(order["order_time"], "isoformat") else str(order["order_time"]),
                "platform": order.get("platform", ""),
                "created_at": order["created_at"].isoformat() if hasattr(order["created_at"], "isoformat") and order["created_at"] else None,
                "items": [
                    {
                        "id": item["id"],
                        "dish_id": item["dish_id"],
                        "dish_name": item["dish_name"],
                        "quantity": item["quantity"],
                        "price": float(item["price"]),
                        "amount": float(item["amount"]),
                        "image_url": item.get("image_url"),
                    }
                    for item in items
                ],
            }
        except Exception as e:
            logger.error(f"查询外卖订单详情失败: {e}")
            return None
