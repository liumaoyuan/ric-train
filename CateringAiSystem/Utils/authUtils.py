import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
import bcrypt

# JWT 配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ric-train-jwt-secret-key-2026-abcdefgh")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE", 120))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE", 7))

# 北京时区
BJT = timezone(timedelta(hours=8))


def hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌（短期）"""
    to_encode = data.copy()
    expire = datetime.now(BJT) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """创建刷新令牌（长期）"""
    to_encode = data.copy()
    expire = datetime.now(BJT) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """解码并验证 JWT 令牌，失败返回 None"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def create_tokens(user_id: int, username: str, roles: list, permissions: list) -> dict:
    """生成登录令牌对（access + refresh）"""
    payload = {
        "user_id": user_id,
        "username": username,
        "roles": roles,
        "permissions": permissions,
    }
    return {
        "access_token": create_access_token(payload),
        "refresh_token": create_refresh_token(payload),
        "token_type": "Bearer",
    }
