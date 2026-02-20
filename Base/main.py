from Base.Api.ai.chatApi import register_ai_chat_router
from Base.Config.logConfig import setup_logging

setup_logging()

from fastapi import FastAPI

app = FastAPI()

register_ai_chat_router(app)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app=app, host="0.0.0.0", port=8010)