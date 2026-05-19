import logging
from functools import wraps
from inspect import iscoroutinefunction
from typing import List

from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)


def get_current_user(request: Request) -> dict:
    """从请求中获取当前用户信息（由中间件注入）"""
    user = getattr(request.state, "current_user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="未认证，请先登录")
    return user


def require_permission(permission_codes: str | List[str]):
    """
    权限校验装饰器，校验当前用户是否拥有指定权限

    Args:
        permission_codes: 权限标识字符串或列表（满足任一即可通过）

    Usage:
        @router.post("/sys/user")
        @require_permission("sys:user:add")
        def create_user(...): ...

        @router.delete("/sys/user/{id}")
        @require_permission(["sys:user:delete", "admin"])
        def delete_user(...): ...
    """
    codes = [permission_codes] if isinstance(permission_codes, str) else permission_codes

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None:
                for _, v in kwargs.items():
                    if isinstance(v, Request):
                        request = v
                        break

            if request is None:
                logger.warning("require_permission: 未找到 Request 对象")
                raise HTTPException(status_code=500, detail="内部错误：无法获取请求上下文")

            user = get_current_user(request)
            user_permissions: list = user.get("permissions", [])

            # 管理员权限（admin）可以访问所有接口
            if "admin" in user.get("roles", []):
                if iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)

            # 检查是否拥有任一所需权限
            for code in codes:
                if code in user_permissions:
                    if iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    return func(*args, **kwargs)

            raise HTTPException(status_code=403, detail=f"无权限访问，需要权限: {', '.join(codes)}")

        return wrapper

    return decorator
