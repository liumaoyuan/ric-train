import logging
from typing import Optional
from decimal import Decimal

from CateringAiSystem.Models import (
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
        return DineInOrder.get_order_list(
            page=page, page_size=page_size,
            store_id=store_id, order_type=order_type,
            date_from=date_from, date_to=date_to,
            store_ids=store_ids,
        )

    @staticmethod
    def get_order_detail(order_no: str) -> Optional[dict]:
        return DineInOrder.get_order_detail(order_no)

    @staticmethod
    def get_dine_in_orders(page: int = 1, page_size: int = 20,
                           store_id: Optional[int] = None,
                           date_from: Optional[str] = None,
                           date_to: Optional[str] = None,
                           store_ids: Optional[list] = None) -> dict:
        return DineInOrder.get_list(
            page=page, page_size=page_size,
            store_id=store_id, date_from=date_from, date_to=date_to,
            store_ids=store_ids,
        )

    @staticmethod
    def get_dine_in_order_detail(order_no: str) -> Optional[dict]:
        return DineInOrder.get_detail_by_no(order_no)

    @staticmethod
    def get_takeout_orders(page: int = 1, page_size: int = 20,
                           store_id: Optional[int] = None,
                           date_from: Optional[str] = None,
                           date_to: Optional[str] = None,
                           store_ids: Optional[list] = None) -> dict:
        return TakeoutOrder.get_list(
            page=page, page_size=page_size,
            store_id=store_id, date_from=date_from, date_to=date_to,
            store_ids=store_ids,
        )

    @staticmethod
    def get_takeout_order_detail(order_no: str) -> Optional[dict]:
        return TakeoutOrder.get_detail_by_no(order_no)

    # ==================== 营业汇总 ====================

    @staticmethod
    def get_daily_summary(page: int = 1, page_size: int = 20,
                          store_id: Optional[int] = None,
                          date_from: Optional[str] = None,
                          date_to: Optional[str] = None,
                          store_ids: Optional[list] = None) -> dict:
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
        return Dish.get_paginated_list(
            page=page, page_size=page_size,
            category=category, status=status, keyword=keyword,
        )

    @staticmethod
    def _serialize(record) -> dict:
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
        return Store.get_paginated_list(
            page=page, page_size=page_size,
            province=province, city=city, status=status,
            store_ids=store_ids,
        )

    @staticmethod
    def get_store_detail(store_id: int) -> Optional[dict]:
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
        return Review.get_paginated_list(
            page=page, page_size=page_size,
            store_id=store_id, platform=platform,
            rating=rating, is_positive=is_positive,
            date_from=date_from, date_to=date_to,
            store_ids=store_ids,
        )

    @staticmethod
    def get_review_detail(review_id: int) -> Optional[dict]:
        return Review.get_detail(review_id)

    # ==================== 权限辅助方法 ====================

    @staticmethod
    def get_user_store_ids(user_info: dict) -> Optional[list]:
        roles = user_info.get("roles", [])
        if "franchisee" in roles:
            store_id = user_info.get("store_id")
            if store_id:
                return [store_id]
            return []
        return None
