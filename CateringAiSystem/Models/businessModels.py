import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, ClassVar

from pydantic import Field

from Base.Repository.models.defaultDbModel import DefaultDbModel

logger = logging.getLogger(__name__)


class Store(DefaultDbModel):
    """门店信息表"""
    table_alias: ClassVar[str] = "store"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{{table_name}}` (
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
        """分页查询门店列表"""
        try:
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

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            count_sql = f"SELECT COUNT(*) AS total FROM {table_name} WHERE {where_sql}"
            count_result = db.execute(count_sql, tuple(params))
            total = count_result[0]["total"] if count_result else 0

            offset = (page - 1) * page_size
            list_sql = f"""SELECT * FROM {table_name}
WHERE {where_sql}
ORDER BY `id` ASC
LIMIT {offset}, {page_size}"""
            results = db.execute(list_sql, tuple(params))

            return {"total": total, "page": page, "page_size": page_size, "data": results or []}
        except Exception as e:
            logger.error(f"查询门店列表失败: {e}")
            return {"total": 0, "page": page, "page_size": page_size, "data": []}


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
        """分页查询菜品列表"""
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

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            count_sql = f"SELECT COUNT(*) AS total FROM {table_name} WHERE {where_sql}"
            count_result = db.execute(count_sql, tuple(params))
            total = count_result[0]["total"] if count_result else 0

            offset = (page - 1) * page_size
            list_sql = f"""SELECT * FROM {table_name}
WHERE {where_sql}
ORDER BY `id` ASC
LIMIT {offset}, {page_size}"""
            results = db.execute(list_sql, tuple(params))

            return {"total": total, "page": page, "page_size": page_size, "data": results or []}
        except Exception as e:
            logger.error(f"查询菜品列表失败: {e}")
            return {"total": 0, "page": page, "page_size": page_size, "data": []}


class DineInOrder(DefaultDbModel):
    """堂食订单表"""
    table_alias: ClassVar[str] = "dine_in_order"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{{table_name}}` (
        `id`                BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '订单ID',
        `store_id`          INT             NOT NULL                 COMMENT '门店ID',
        `order_no`          VARCHAR(50)     NOT NULL                 COMMENT '订单号',
        `total_amount`      DECIMAL(10,2)   NOT NULL DEFAULT 0.00    COMMENT '订单总金额',
        `payment_method`    VARCHAR(20)     NOT NULL                 COMMENT '支付方式',
        `member_id`         INT             DEFAULT NULL             COMMENT '会员ID',
        `dish_count`        TINYINT         NOT NULL DEFAULT 0       COMMENT '菜品数量',
        `order_time`        DATETIME        NOT NULL                 COMMENT '下单时间',
        `created_at`        DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uk_order_no` (`order_no`),
        KEY `idx_store_time` (`store_id`, `order_time`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='堂食订单表';
    """

    id: Optional[int] = Field(None, description="订单ID")
    store_id: int = Field(..., description="门店ID")
    order_no: str = Field(..., description="订单号")
    total_amount: Decimal = Field(0.00, description="订单总金额")
    payment_method: str = Field(..., description="支付方式")
    member_id: Optional[int] = Field(None, description="会员ID")
    dish_count: int = Field(0, description="菜品数量")
    order_time: datetime = Field(..., description="下单时间")
    created_at: Optional[datetime] = Field(None, description="创建时间")


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


class OrderItem(DefaultDbModel):
    """订单菜品明细表"""
    table_alias: ClassVar[str] = "order_item"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{{table_name}}` (
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
        """分页查询营业汇总列表"""
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

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            count_sql = f"SELECT COUNT(*) AS total FROM {table_name} ds WHERE {where_sql}"
            count_result = db.execute(count_sql, tuple(params))
            total = count_result[0]["total"] if count_result else 0

            offset = (page - 1) * page_size
            list_sql = f"""SELECT ds.*, s.`name` AS store_name
FROM {table_name} ds
LEFT JOIN {store_table} s ON s.`id` = ds.`store_id`
WHERE {where_sql}
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
        """获取营业汇总统计概览"""
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

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

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
WHERE {where_sql}"""
            results = db.execute(sql, tuple(params))
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"查询营业汇总统计失败: {e}")
            return {}


class Review(DefaultDbModel):
    """评论表（风评分析）"""
    table_alias: ClassVar[str] = "review"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{{table_name}}` (
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
    def get_paginated_list(cls, page: int = 1, page_size: int = 20,
                           store_id: Optional[int] = None,
                           platform: Optional[str] = None,
                           rating: Optional[int] = None,
                           is_positive: Optional[int] = None,
                           date_from: Optional[str] = None,
                           date_to: Optional[str] = None,
                           store_ids: Optional[list] = None) -> dict:
        """分页查询评论列表"""
        try:
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

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            count_sql = f"SELECT COUNT(*) AS total FROM {table_name} r WHERE {where_sql}"
            count_result = db.execute(count_sql, tuple(params))
            total = count_result[0]["total"] if count_result else 0

            offset = (page - 1) * page_size
            list_sql = f"""SELECT r.*, s.`name` AS store_name
FROM {table_name} r
LEFT JOIN {store_table} s ON s.`id` = r.`store_id`
WHERE {where_sql}
ORDER BY r.`review_time` DESC
LIMIT {offset}, {page_size}"""
            results = db.execute(list_sql, tuple(params))

            return {"total": total, "page": page, "page_size": page_size, "data": results or []}
        except Exception as e:
            logger.error(f"查询评论列表失败: {e}")
            return {"total": 0, "page": page, "page_size": page_size, "data": []}
