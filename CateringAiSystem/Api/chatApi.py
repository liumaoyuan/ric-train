"""聊天助手 API - LangChain Agent 对话接口（仅流式）"""
import logging
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from CateringAiSystem.Service.chatService import ChatService
from CateringAiSystem.Utils.rbacUtils import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["聊天助手"])


class AskParam(BaseModel):
    question: str = Field(..., description="用户问题")
    session_id: Optional[str] = Field(None, description="会话ID，为空则自动创建")
    is_online_search: bool = Field(False, description="是否联网搜索")


class ResumeParam(BaseModel):
    session_id: str = Field(..., description="会话ID（thread_id）")
    decision: dict = Field(..., description="审核决定: {\"decision\": \"approve\"|\"reject\"}")


class CreateSessionParam(BaseModel):
    title: Optional[str] = Field(None, description="会话标题")


@router.post("/ask")
async def ask(param: AskParam, request: Request):
    """统一对话入口 - 走 LangChain Agent（仅流式）"""
    user = get_current_user(request)
    user_id = str(user["user_id"])
    user_info = {
        "user_id": user["user_id"],
        "username": user.get("username", ""),
        "roles": user.get("roles", []),
    }

    return StreamingResponse(
        ChatService.ask_stream(
            question=param.question,
            user_id=user_id,
            session_id=param.session_id,
            user_info=user_info,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/resume")
async def resume(param: ResumeParam, request: Request):
    """人工审核后恢复 Agent 执行（流式）"""
    user = get_current_user(request)
    user_id = str(user["user_id"])
    user_info = {
        "user_id": user["user_id"],
        "username": user.get("username", ""),
        "roles": user.get("roles", []),
    }

    return StreamingResponse(
        ChatService.resume_stream(
            session_id=param.session_id,
            decision=param.decision,
            user_id=user_id,
            user_info=user_info,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/session/list")
def list_sessions(request: Request):
    """获取用户会话列表"""
    user = get_current_user(request)
    sessions = ChatService.list_sessions(str(user["user_id"]))
    data = [
        {
            "session_id": s.session_uuid,
            "title": s.title or "新对话",
            "created_at": str(s.create_at) if s.create_at else "",
            "updated_at": str(s.update_at) if s.update_at else "",
        }
        for s in sessions
    ]
    return {"code": 200, "msg": "success", "data": data}


@router.post("/session/create")
def create_session(param: CreateSessionParam, request: Request):
    """创建新会话"""
    user = get_current_user(request)
    session = ChatService.get_or_create_session(
        user_id=str(user["user_id"]),
        title=param.title,
    )
    return {
        "code": 200,
        "msg": "success",
        "data": {
            "session_id": session.session_uuid,
            "title": session.title,
        },
    }


@router.delete("/session/delete")
async def delete_session(session_id: str, request: Request):
    """删除会话"""
    user = get_current_user(request)
    success = await ChatService.delete_session(session_id, str(user["user_id"]))
    if success:
        return {"code": 200, "msg": "删除成功", "data": None}
    return {"code": 404, "msg": "会话不存在或无权删除", "data": None}


@router.get("/session/history")
def get_session_history(session_id: str, request: Request):
    """获取会话对话历史"""
    user = get_current_user(request)
    messages = ChatService.get_conversation_history(
        session_id=session_id,
        user_id=str(user["user_id"]),
    )
    return {"code": 200, "msg": "success", "data": messages}
