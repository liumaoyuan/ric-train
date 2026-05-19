"""
CateringAiSystem — 连锁餐饮 AI 系统主入口

Phase 1: 系统管理（RBAC 完整 CRUD + JWT 认证）
"""
from Base.Config.logConfig import setup_logging

setup_logging()

from fastapi import FastAPI

from CateringAiSystem.Middleware.authMiddleware import AuthMiddleware
from CateringAiSystem.Api.authApi import router as auth_router
from CateringAiSystem.Api.sysUserApi import router as user_router
from CateringAiSystem.Api.sysRoleApi import router as role_router
from CateringAiSystem.Api.sysMenuApi import router as menu_router
from CateringAiSystem.Api.dataApi import router as data_router

app = FastAPI(
    title="连锁餐饮 AI 系统",
    description="连锁餐饮 AI 系统 API — Phase 1: RBAC 系统管理",
    version="1.0.0",
)

# 注册中间件
app.add_middleware(AuthMiddleware)

# 注册路由
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(role_router)
app.include_router(menu_router)
app.include_router(data_router)


@app.get("/")
def root():
    return {"code": 200, "msg": "连锁餐饮 AI 系统 — Phase 2 (原始数据查询)", "data": None}


@app.get("/health")
def health():
    return {"code": 200, "msg": "OK", "data": None}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, host="0.0.0.0", port=8011)
