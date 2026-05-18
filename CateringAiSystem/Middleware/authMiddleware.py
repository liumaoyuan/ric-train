import re
from typing import List

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from CateringAiSystem.Utils.authUtils import decode_token

# 不需要认证的路径白名单
WHITE_LIST = [
    r"^/api/v1/auth/login$",
    r"^/api/v1/auth/refresh$",
    r"^/docs?$",
    r"^/openapi.json$",
    r"^/redoc$",
    r"^/$",
    r"^/health$",
]


class AuthMiddleware(BaseHTTPMiddleware):
    """JWT 认证中间件 — 拦截所有请求，校验 Token"""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 白名单路径跳过认证
        if self._is_white_listed(path):
            return await call_next(request)

        # 从请求头获取 Token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"code": 401, "msg": "缺少认证令牌", "data": None},
            )

        token = auth_header[7:]  # 去掉 "Bearer "
        payload = decode_token(token)
        if payload is None:
            return JSONResponse(
                status_code=401,
                content={"code": 401, "msg": "令牌无效或已过期", "data": None},
            )

        # 检查令牌类型（不允许用 refresh_token 访问业务接口）
        if payload.get("type") != "access":
            return JSONResponse(
                status_code=401,
                content={"code": 401, "msg": "请使用 access_token 访问", "data": None},
            )

        # 将用户信息注入 request.state
        request.state.current_user = {
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", []),
        }

        response = await call_next(request)
        return response

    @staticmethod
    def _is_white_listed(path: str) -> bool:
        """检查路径是否在白名单中"""
        for pattern in WHITE_LIST:
            if re.match(pattern, path):
                return True
        return False
