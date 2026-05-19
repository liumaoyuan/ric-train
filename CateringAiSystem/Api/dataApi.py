from typing import Optional

from fastapi import APIRouter, Request, Query

from CateringAiSystem.Service.dataService import DataService
from CateringAiSystem.Utils.rbacUtils import get_current_user, require_permission

router = APIRouter(prefix="/api/v1/data", tags=["原始数据查询"])


@router.get("/orders")
@require_permission(["data:order:list", "data:dine-in:list", "data:takeout:list"])
def list_orders(
        request: Request,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        store_id: Optional[int] = None,
        order_type: Optional[str] = None,
        payment_method: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
):
    """订单列表（合并堂食+外卖，分页）"""
    user = get_current_user(request)
    store_ids = DataService.get_user_store_ids(user)
    data = DataService.get_orders(
        page=page, page_size=page_size,
        store_id=store_id, order_type=order_type,
        payment_method=payment_method,
        date_from=date_from, date_to=date_to,
        store_ids=store_ids,
    )
    return {"code": 200, "msg": "success", "data": data}


@router.get("/orders/{order_no}")
@require_permission(["data:order:detail", "data:dine-in:detail", "data:takeout:detail"])
def get_order_detail(order_no: str, request: Request):
    """订单详情（含菜品明细）"""
    result = DataService.get_order_detail(order_no)
    if result is None:
        return {"code": 404, "msg": "订单不存在", "data": None}
    return {"code": 200, "msg": "success", "data": result}


@router.get("/dine-in-orders")
@require_permission("data:dine-in:list")
def list_dine_in_orders(
        request: Request,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        store_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
):
    """堂食订单列表（分页）"""
    user = get_current_user(request)
    store_ids = DataService.get_user_store_ids(user)
    data = DataService.get_dine_in_orders(
        page=page, page_size=page_size,
        store_id=store_id, date_from=date_from, date_to=date_to,
        store_ids=store_ids,
    )
    return {"code": 200, "msg": "success", "data": data}


@router.get("/dine-in-orders/{order_no}")
@require_permission("data:dine-in:detail")
def get_dine_in_order_detail(order_no: str, request: Request):
    """堂食订单详情（含菜品明细）"""
    result = DataService.get_dine_in_order_detail(order_no)
    if result is None:
        return {"code": 404, "msg": "订单不存在", "data": None}
    return {"code": 200, "msg": "success", "data": result}


@router.get("/takeout-orders")
@require_permission("data:takeout:list")
def list_takeout_orders(
        request: Request,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        store_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
):
    """外卖订单列表（分页）"""
    user = get_current_user(request)
    store_ids = DataService.get_user_store_ids(user)
    data = DataService.get_takeout_orders(
        page=page, page_size=page_size,
        store_id=store_id, date_from=date_from, date_to=date_to,
        store_ids=store_ids,
    )
    return {"code": 200, "msg": "success", "data": data}


@router.get("/takeout-orders/{order_no}")
@require_permission("data:takeout:detail")
def get_takeout_order_detail(order_no: str, request: Request):
    """外卖订单详情（含菜品明细）"""
    result = DataService.get_takeout_order_detail(order_no)
    if result is None:
        return {"code": 404, "msg": "订单不存在", "data": None}
    return {"code": 200, "msg": "success", "data": result}


@router.get("/daily-summary")
@require_permission("data:summary:list")
def list_daily_summary(
        request: Request,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        store_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
):
    """营业汇总列表（分页）"""
    user = get_current_user(request)
    store_ids = DataService.get_user_store_ids(user)
    data = DataService.get_daily_summary(
        page=page, page_size=page_size,
        store_id=store_id,
        date_from=date_from, date_to=date_to,
        store_ids=store_ids,
    )
    return {"code": 200, "msg": "success", "data": data}


@router.get("/daily-summary/stat")
@require_permission("data:summary:list")
def get_daily_summary_stat(
        request: Request,
        store_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
):
    """营业汇总统计概览"""
    user = get_current_user(request)
    store_ids = DataService.get_user_store_ids(user)
    data = DataService.get_daily_summary_stat(
        store_id=store_id,
        date_from=date_from, date_to=date_to,
        store_ids=store_ids,
    )
    return {"code": 200, "msg": "success", "data": data}


@router.get("/dishes")
@require_permission("data:dish:list")
def list_dishes(
        request: Request,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        category: Optional[str] = None,
        status: Optional[int] = None,
        keyword: Optional[str] = None,
):
    """菜品列表（分页）"""
    data = DataService.get_dishes(
        page=page, page_size=page_size,
        category=category, status=status, keyword=keyword,
    )
    return {"code": 200, "msg": "success", "data": data}


@router.get("/dishes/{dish_id}")
@require_permission("data:dish:detail")
def get_dish_detail(dish_id: int, request: Request):
    """菜品详情"""
    result = DataService.get_dish_detail(dish_id)
    if result is None:
        return {"code": 404, "msg": "菜品不存在", "data": None}
    return {"code": 200, "msg": "success", "data": result}


@router.get("/stores")
@require_permission("data:store:list")
def list_stores(
        request: Request,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=9999),
        province: Optional[str] = None,
        city: Optional[str] = None,
        status: Optional[int] = None,
):
    """门店列表（分页）"""
    user = get_current_user(request)
    store_ids = DataService.get_user_store_ids(user)
    data = DataService.get_stores(
        page=page, page_size=page_size,
        province=province, city=city, status=status,
        store_ids=store_ids,
    )
    return {"code": 200, "msg": "success", "data": data}


@router.get("/stores/{store_id}")
@require_permission("data:store:detail")
def get_store_detail(store_id: int, request: Request):
    """门店详情"""
    result = DataService.get_store_detail(store_id)
    if result is None:
        return {"code": 404, "msg": "门店不存在", "data": None}
    return {"code": 200, "msg": "success", "data": result}


@router.get("/reviews")
@require_permission("data:review:list")
def list_reviews(
        request: Request,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        store_id: Optional[int] = None,
        platform: Optional[str] = None,
        rating: Optional[int] = None,
        is_positive: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
):
    """评论列表（分页）"""
    user = get_current_user(request)
    store_ids = DataService.get_user_store_ids(user)
    data = DataService.get_reviews(
        page=page, page_size=page_size,
        store_id=store_id, platform=platform,
        rating=rating, is_positive=is_positive,
        date_from=date_from, date_to=date_to,
        store_ids=store_ids,
    )
    return {"code": 200, "msg": "success", "data": data}


@router.get("/reviews/{review_id}")
@require_permission("data:review:detail")
def get_review_detail(review_id: int, request: Request):
    """评论详情"""
    result = DataService.get_review_detail(review_id)
    if result is None:
        return {"code": 404, "msg": "评论不存在", "data": None}
    return {"code": 200, "msg": "success", "data": result}
