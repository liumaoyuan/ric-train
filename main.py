from Base.Config.logConfig import setup_logging
from CateringAiSystem.Api import register

# 日志配置初始化
setup_logging()

from fastapi import FastAPI

app = FastAPI(
    title="连锁餐饮 AI 系统",
    description="连锁餐饮 AI 系统",
    version="1.0.0",
)

# 注册中间件和路由
register(app)


@app.get("/")
def root():
    return {"code": 200, "msg": "连锁餐饮 AI 系统", "data": None}


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app="main:app", host="0.0.0.0", port=8000)
