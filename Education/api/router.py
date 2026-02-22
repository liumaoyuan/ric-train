from Education.api.core.questionApi import router as question_router


def router_register(app):
    app.include_router(question_router)