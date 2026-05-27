import logging
from decimal import Decimal
from typing import Optional, ClassVar

from pydantic import Field

from Base.Repository.models.defaultDbModel import DefaultDbModel

logger = logging.getLogger(__name__)


class OrderItem(DefaultDbModel):
    """订单菜品明细表"""
    table_alias: ClassVar[str] = "order_item"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{table_alias}` (
        `id`            BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '明细ID',
        `order_no`      VARCHAR(50)     NOT NULL                 COMMENT '订单号',
        `store_id`      INT             NOT NULL                 COMMENT '门店ID',
        `dish_id`       INT             NOT NULL                 COMMENT '菜品ID',
        `dish_name`     VARCHAR(100)    NOT NULL                 COMMENT '菜品名称',
        `quantity`      INT             NOT NULL DEFAULT 1       COMMENT '数量',
        `price`         DECIMAL(10,2)   NOT NULL                 COMMENT '单价',
        `amount`        DECIMAL(10,2)   NOT NULL                 COMMENT '小计金额',
        PRIMARY KEY (`id`),
        KEY `idx_order_no` (`order_no`),
        KEY `idx_store_dish` (`store_id`, `dish_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单菜品明细表';
    """

    id: Optional[int] = Field(None, description="明细ID")
    order_no: str = Field(..., description="订单号")
    store_id: int = Field(..., description="门店ID")
    dish_id: int = Field(..., description="菜品ID")
    dish_name: str = Field(..., description="菜品名称")
    quantity: int = Field(1, description="数量")
    price: Decimal = Field(..., description="单价")
    amount: Decimal = Field(..., description="小计金额")
