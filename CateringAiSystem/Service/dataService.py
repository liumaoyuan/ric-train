import logging
from typing import Optional

from CateringAiSystem.Models.businessModels import (
    Store, Dish, DineInOrder, TakeoutOrder, OrderItem, DailySummary, Review,
)

logger = logging.getLogger(__name__)


class DataService:

    # ==================== 订单数据 ====================

    @staticmethod
    def get_orders(page: int = 1, page_size: int = 20,
                   store_id: Optional[int] = None,
                   order_type: Optional[str] = None,
                   payment_method: Optional[str] = None,
                   date_from: Optional[str] = None,
                   date_to: Optional[str] = None,
                   store_ids: Optional[list] = None) -> dict:
        """
        订单列表（合并堂食+外卖）
        使用 UNION ALL + SQL 级分页，避免全量加载到 Python
        """
        try:
            dine_table = DineInOrder.get_table_name_with_db()
            takeout_table = TakeoutOrder.get_table_name_with_db()
            store_table = Store.get_table_name_with_db()
            db = DineInOrder.get_db_connection()
            if db is None:
                return {"total": 0, "page": page, "page_size": page_size, "data": []}

            where_clauses = []
            params = []

            if store_id is not None:
                where_clauses.append("`store_id` = %s")
                params.append(store_id)
            elif store_ids is not None:
                placeholders = ",".join(["%s"] * len(store_ids))
                where_clauses.append(f"`store_id` IN ({placeholders})")
                params.extend(store_ids)
            if date_from:
                where_clauses.append("`order_time` >= %s")
                params.append(date_from)
            if date_to:
                where_clauses.append("`order_time` <= %s")
                params.append(date_to)

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            select_base = "`id`, `store_id`, `order_no`, `total_amount`, `dish_count`, `order_time`, `created_at`"

            # 构建子查询，每个子查询对应一份 params
            subqueries = []
            query_params = []

            if order_type is None or order_type == "dine_in":
                subqueries.append(
                    f"SELECT {select_base}, `payment_method` AS payment_method_or_platform, "
                    f"'dine_in' AS order_type FROM {dine_table} WHERE {where_sql}"
                )
                query_params.extend(params)

            if order_type is None or order_type == "takeout":
                subqueries.append(
                    f"SELECT {select_base}, `platform` AS payment_method_or_platform, "
                    f"'takeout' AS order_type FROM {takeout_table} WHERE {where_sql}"
                )
                query_params.extend(params)

            if not subqueries:
                return {"total": 0, "page": page, "page_size": page_size, "data": []}

            union_sql = " UNION ALL ".join(subqueries)

            # 总行数
            count_sql = f"SELECT COUNT(*) AS total FROM ({union_sql}) AS combined"
            count_result = db.execute(count_sql, tuple(query_params))
            total = count_result[0]["total"] if count_result else 0
            if total == 0:
                return {"total": 0, "page": page, "page_size": page_size, "data": []}

            # 分页数据
            offset = (page - 1) * page_size
            data_sql = f"SELECT * FROM ({union_sql}) AS combined ORDER BY `order_time` DESC LIMIT %s OFFSET %s"
            data_params = tuple(query_params) + (page_size, offset)
            rows = db.execute(data_sql, data_params) or []

            # 查门店名称
            store_ids_set = set(r["store_id"] for r in rows)
            store_map = {}
            if store_ids_set:
                ids_str = ",".join(str(s) for s in store_ids_set)
                try:
                    store_sql = f"SELECT `id`, `name` FROM {store_table} WHERE `id` IN ({ids_str})"
                    store_results = db.execute(store_sql) or []
                    store_map = {r["id"]: r["name"] for r in store_results}
                except Exception:
                    pass

            data = []
            for row in rows:
                data.append({
                    "id": row["id"],
                    "store_id": row["store_id"],
                    "store_name": store_map.get(row["store_id"], ""),
                    "order_no": row["order_no"],
                    "total_amount": float(row["total_amount"]),
                    "payment_method_or_platform": row.get("payment_method_or_platform", ""),
                    "dish_count": row["dish_count"],
                    "order_time": row["order_time"].isoformat() if hasattr(row["order_time"], "isoformat") else str(row["order_time"]),
                    "order_type": row["order_type"],
                    "created_at": row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") and row["created_at"] else None,
                })

            return {"total": total, "page": page, "page_size": page_size, "data": data}
        except Exception as e:
            logger.error(f"查询订单列表失败: {e}", exc_info=True)
            return {"total": 0, "page": page, "page_size": page_size, "data": []}

    @staticmethod
    def get_order_detail(order_no: str) -> Optional[dict]:
        """
        查询订单详情（包括菜品明细）
        先查 dine_in_order，再查 takeout_order
        """
        try:
            dine_table = DineInOrder.get_table_name_with_db()
            takeout_table = TakeoutOrder.get_table_name_with_db()
            store_table = Store.get_table_name_with_db()
            item_table = OrderItem.get_table_name_with_db()

            db = DineInOrder.get_db_connection()
            if db is None:
                return None

            # 查堂食订单
            sql = f"""SELECT d.*, s.`name` AS store_name
FROM {dine_table} d
LEFT JOIN {store_table} s ON s.`id` = d.`store_id`
WHERE d.`order_no` = %s"""
            results = db.execute(sql, (order_no,))
            if results:
                order = results[0]
                order_type = "dine_in"
            else:
                # 查外卖订单
                sql = f"""SELECT t.*, s.`name` AS store_name
FROM {takeout_table} t
LEFT JOIN {store_table} s ON s.`id` = t.`store_id`
WHERE t.`order_no` = %s"""
                results = db.execute(sql, (order_no,))
                if results:
                    order = results[0]
                    order_type = "takeout"
                else:
                    return None

            # 查订单明细
            item_sql = f"""SELECT oi.*, d.`image_url`
FROM {item_table} oi
LEFT JOIN {Dish.get_table_name_with_db()} d ON d.`id` = oi.`dish_id`
WHERE oi.`order_no` = %s"""
            items = db.execute(item_sql, (order_no,)) or []

            return {
                "order_no": order["order_no"],
                "store_id": order["store_id"],
                "store_name": order.get("store_name", ""),
                "total_amount": float(order["total_amount"]),
                "dish_count": order["dish_count"],
                "order_time": order["order_time"].isoformat() if hasattr(order["order_time"], "isoformat") else str(order["order_time"]),
                "order_type": order_type,
                "payment_method_or_platform": order.get("payment_method") or order.get("platform", ""),
                "member_id": order.get("member_id"),
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
            logger.error(f"查询订单详情失败: {e}")
            return None

    # ==================== 营业汇总 ====================

    @staticmethod
    def get_daily_summary(page: int = 1, page_size: int = 20,
                          store_id: Optional[int] = None,
                          date_from: Optional[str] = None,
                          date_to: Optional[str] = None,
                          store_ids: Optional[list] = None) -> dict:
        """营业汇总分页列表"""
        return DailySummary.get_paginated_list(
            page=page, page_size=page_size,
            store_id=store_id, date_from=date_from, date_to=date_to,
            store_ids=store_ids,
        )

    @staticmethod
    def get_daily_summary_stat(store_id: Optional[int] = None,
                                date_from: Optional[str] = None,
                                date_to: Optional[str] = None,
                                store_ids: Optional[list] = None) -> dict:
        """营业汇总统计概览"""
        stat = DailySummary.get_stat(
            store_id=store_id, date_from=date_from, date_to=date_to,
            store_ids=store_ids,
        )
        if stat:
            return {
                "store_count": stat.get("store_count", 0),
                "day_count": stat.get("day_count", 0),
                "total_revenue": float(stat.get("total_revenue") or 0),
                "total_orders": int(stat.get("total_orders") or 0),
                "avg_price": float(stat.get("avg_price") or 0),
                "total_dine_in": float(stat.get("total_dine_in") or 0),
                "total_takeout": float(stat.get("total_takeout") or 0),
                "total_peak_hour": float(stat.get("total_peak_hour") or 0),
            }
        return {}

    # ==================== 菜品数据 ====================

    @staticmethod
    def get_dishes(page: int = 1, page_size: int = 20,
                   category: Optional[str] = None,
                   status: Optional[int] = None,
                   keyword: Optional[str] = None) -> dict:
        """菜品分页列表"""
        return Dish.get_paginated_list(
            page=page, page_size=page_size,
            category=category, status=status, keyword=keyword,
        )

    @staticmethod
    def _serialize(record) -> dict:
        """将模型实例序列化为可 JSON 序列化的字典"""
        if record is None:
            return {}
        d = record.to_dict()
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
            elif isinstance(v, Decimal):
                d[k] = float(v)
        return d

    @staticmethod
    def get_dish_detail(dish_id: int) -> Optional[dict]:
        """菜品详情"""
        dish = Dish.get_by_id(dish_id)
        if dish is None:
            return None
        return DataService._serialize(dish)

    # ==================== 门店数据 ====================

    @staticmethod
    def get_stores(page: int = 1, page_size: int = 20,
                   province: Optional[str] = None,
                   city: Optional[str] = None,
                   status: Optional[int] = None,
                   store_ids: Optional[list] = None) -> dict:
        """门店分页列表"""
        return Store.get_paginated_list(
            page=page, page_size=page_size,
            province=province, city=city, status=status,
            store_ids=store_ids,
        )

    @staticmethod
    def get_store_detail(store_id: int) -> Optional[dict]:
        """门店详情"""
        store = Store.get_by_id(store_id)
        if store is None:
            return None
        return DataService._serialize(store)

    # ==================== 评论数据 ====================

    @staticmethod
    def get_reviews(page: int = 1, page_size: int = 20,
                    store_id: Optional[int] = None,
                    platform: Optional[str] = None,
                    rating: Optional[int] = None,
                    is_positive: Optional[int] = None,
                    date_from: Optional[str] = None,
                    date_to: Optional[str] = None,
                    store_ids: Optional[list] = None) -> dict:
        """评论分页列表"""
        return Review.get_paginated_list(
            page=page, page_size=page_size,
            store_id=store_id, platform=platform,
            rating=rating, is_positive=is_positive,
            date_from=date_from, date_to=date_to,
            store_ids=store_ids,
        )

    @staticmethod
    def get_review_detail(review_id: int) -> Optional[dict]:
        """评论详情（含门店名称）"""
        try:
            db = Review.get_db_connection()
            if db is None:
                return None

            review_table = Review.get_table_name_with_db()
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
            # Decimal 转 float
            for k, v in row_dict.items():
                if hasattr(v, 'isocalendar'):  # date/datetime
                    row_dict[k] = v.isoformat() if hasattr(v, 'isoformat') else str(v)
            return row_dict
        except Exception as e:
            logger.error(f"查询评论详情失败: {e}")
            return None

    # ==================== 权限辅助方法 ====================

    @staticmethod
    def get_user_store_ids(user_info: dict) -> Optional[list]:
        """
        根据用户信息获取可见的门店ID列表
        - admin: None（表示所有门店）
        - employee: None（表示所有门店）
        - franchisee: 仅本门店（需用户有 store_id 属性）
        """
        roles = user_info.get("roles", [])
        if "franchisee" in roles:
            # 加盟商：从用户信息获取 store_id
            # 注意：当前 sys_user 表没有 store_id 字段，
            # 这里通过扩展用户信息或查询关联表获取
            store_id = user_info.get("store_id")
            if store_id:
                return [store_id]
            # 如果没有 store_id，返回空列表（无数据可见）
            return []
        # admin / employee 可见所有门店
        return None
