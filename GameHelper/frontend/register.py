from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

def frontend_init(app: FastAPI):
    """初始化前端静态资源和页面"""

    # 获取当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(current_dir, 'static')

    # 挂载静态文件目录
    if os.path.exists(static_dir):
        app.mount("/game-static", StaticFiles(directory=static_dir), name="game_static")

    # 注册前端页面路由
    @app.get("/game")
    async def game_page():
        """游戏助手主页"""
        html_path = os.path.join(current_dir, 'index.html')
        if os.path.exists(html_path):
            return FileResponse(html_path)
        return {"message": "游戏助手项目 - 前端页面开发中..."}
