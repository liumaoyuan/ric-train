"""
CateringAiSystem — 连锁餐饮 AI 系统主入口

Phase 1: 系统管理（RBAC 完整 CRUD + JWT 认证）
"""
from Base.Config.logConfig import setup_logging
from CateringAiSystem.Api import register

setup_logging()

from fastapi import FastAPI

app = FastAPI(
    title="连锁餐饮 AI 系统",
    description="连锁餐饮 AI 系统",
    version="1.0.0",
)

register(app)


@app.get("/")
def root():
    return {"code": 200, "msg": "连锁餐饮 AI 系统", "data": None}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, host="0.0.0.0", port=8011)
