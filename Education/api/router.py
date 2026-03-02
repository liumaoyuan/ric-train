from Education.api.core.questionApi import router as question_router
from Education.api.core.paperApi import router as paper_router
from Education.api.core.examApi import router as exam_router


def router_register(app):
    app.include_router(question_router, tags=["教育局项目"])
    app.include_router(paper_router, tags=["教育局项目"])
    app.include_router(exam_router, tags=["教育局项目"])