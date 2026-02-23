# 挂载静态文件
from pathlib import Path

from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from fastapi import Request, APIRouter

from fastapi import FastAPI

# 定位当前目录作为模板根路径 （如此 需要 .html 文件和当前文件同目录下）
BASE_DIR = Path(__file__).parent

router = APIRouter(prefix="/edu")


def frontend_init(app: FastAPI):
    # 模板配置
    templates = Jinja2Templates(directory=BASE_DIR)

    @router.get("/", response_class=HTMLResponse)
    async def interview_upload_page(request: Request):
        """做题页面"""
        return templates.TemplateResponse("doQuestion.html", {"request": request})

    app.include_router(router, tags=["教育局项目-前端"])
