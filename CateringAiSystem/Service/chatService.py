"""聊天助手服务 - 编排 LangChain Agent 工作流"""
import json
import logging
import time
from typing import AsyncGenerator, Optional

from Base.Service.aiService import AiService, AuditingTextError
from Base.Service.keywordService import keyword_replace_question
from CateringAiSystem.Agent import (
    AgentMemory,
    get_agent_for_role,
)

logger = logging.getLogger(__name__)


class ChatService:
    """聊天助手服务"""

    # ── 会话管理 ──

    @staticmethod
    def get_or_create_session(user_id: str, title: str = None):
        return AgentMemory.get_or_create_session(user_id, title)

    @staticmethod
    def list_sessions(user_id: str, limit: int = 50, offset: int = 0):
        return AgentMemory.list_sessions(user_id, limit, offset)

    @staticmethod
    def delete_session(session_id: str, user_id: str) -> bool:
        return AgentMemory.delete_session(session_id, user_id)

    @staticmethod
    def get_conversation_history(session_id: str, user_id: str) -> list:
        return AgentMemory.get_conversation_history(session_id, user_id)

    # ── AI 对话 ──

    @classmethod
    async def ask_stream(
        cls,
        question: str,
        user_id: str,
        session_id: Optional[str] = None,
        is_thinking: bool = False,
        is_online_search: bool = False,
        user_info: Optional[dict] = None,
    ) -> AsyncGenerator[str, None]:
        """流式对话 - 走 create_agent() LangGraph Agent"""
        start_time = time.time()
        session = None
        actual_session_id = None

        try:
            # 1. 会话
            session = AgentMemory.get_or_create_session(user_id, session_uuid=session_id)
            actual_session_id = session.session_uuid

            yield f"data: {json.dumps({'type': 'start', 'session_id': actual_session_id}, ensure_ascii=False)}\n\n"

            # 2. 关键词替换
            # safe_question = keyword_replace_question(question)
            safe_question = question

            # 3. 文本审核
            # auditing_dict = AiService.auditing_text(safe_question)
            # if auditing_dict.get("status") == 0:
            #     error_msg = "根据《生成式人工智能服务管理暂行办法》，您的问题包含敏感信息，无法处理"
            #     cls._save_and_yield_error(question, error_msg, user_id, actual_session_id, start_time)
            #     return

            # 4. 问题改写
            # rewrite = AiService.rewrite_question(
            #     question=safe_question,
            #     user_id=user_id,
            #     session_id=actual_session_id,
            # )
            # final_question = rewrite or safe_question
            final_question = safe_question

            # 5. 获取角色权限
            roles = (user_info or {}).get("roles", ["employee"])

            # 6. 获取角色 Agent（全局单例）并执行
            agent = await get_agent_for_role(role_codes=roles)

            full_answer = []
            async for event in agent.astream(
                session_id=actual_session_id,
                user_id=user_id,
                question=final_question,
            ):
                event_type = event.get("type", "")
                event_content = event.get("content", "")

                if event_type == "content":
                    full_answer.append(event_content)
                    yield f"data: {json.dumps({'type': 'content', 'content': event_content}, ensure_ascii=False)}\n\n"

                elif event_type == "tool_call":
                    yield f"data: {json.dumps({'type': 'tool_call', 'content': event_content}, ensure_ascii=False)}\n\n"

                elif event_type == "error":
                    yield f"data: {json.dumps({'type': 'error', 'content': event_content}, ensure_ascii=False)}\n\n"
                    cls._save_conversation(question, event_content, user_id, actual_session_id, start_time, status="failed")
                    return

            # 7. 持久化
            answer = "".join(full_answer)
            if answer:
                cls._save_conversation(question, answer, user_id, actual_session_id, start_time)

            yield f"data: {json.dumps({'type': 'done', 'session_id': actual_session_id}, ensure_ascii=False)}\n\n"

        except AuditingTextError:
            error_msg = "内容审核未通过"
            cls._save_and_yield_error(question, error_msg, user_id, actual_session_id or session_id, start_time)
        except Exception as e:
            logger.error(f"对话处理异常：{e}", exc_info=True)
            error_msg = f"处理异常：{e}"
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg}, ensure_ascii=False)}\n\n"
            cls._save_conversation(
                question, error_msg, user_id,
                actual_session_id or (session.session_uuid if session else "unknown"),
                start_time, status="failed",
            )

    @classmethod
    async def ask(
        cls,
        question: str,
        user_id: str,
        session_id: Optional[str] = None,
        is_online_search: bool = False,
        user_info: Optional[dict] = None,
    ) -> dict:
        """非流式对话"""
        session = None
        actual_session_id = None
        start_time = time.time()

        try:
            session = AgentMemory.get_or_create_session(user_id, session_uuid=session_id)
            actual_session_id = session.session_uuid

            safe_question = keyword_replace_question(question)
            auditing_dict = AiService.auditing_text(safe_question)
            if auditing_dict.get("status") == 0:
                return {"error": "内容审核未通过", "session_id": actual_session_id}

            rewrite = AiService.rewrite_question(
                question=safe_question, user_id=user_id, session_id=actual_session_id,
            )
            final_question = rewrite or safe_question

            roles = (user_info or {}).get("roles", ["employee"])
            agent = await get_agent_for_role(role_codes=roles)

            answer = await agent.arun(
                session_id=actual_session_id, user_id=user_id, question=final_question,
            )
            cls._save_conversation(question, answer, user_id, actual_session_id, start_time)
            return {"answer": answer, "session_id": actual_session_id}

        except AuditingTextError:
            return {"error": "内容审核未通过", "session_id": actual_session_id}
        except Exception as e:
            logger.error(f"对话处理异常：{e}", exc_info=True)
            return {"error": str(e), "session_id": actual_session_id}

    # ── 内部工具 ──

    @classmethod
    def _save_conversation(cls, question: str, answer: str, user_id: str, session_id: str, start_time: float, status: str = "success"):
        AgentMemory.save_conversation(
            question=question, answer=answer,
            user_id=user_id, session_id=session_id,
            duration_ms=int((time.time() - start_time) * 1000),
            status=status,
        )

    @classmethod
    async def _save_and_yield_error(cls, question, error_msg, user_id, session_id, start_time, gen=None):
        if gen:
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg}, ensure_ascii=False)}\n\n"
        cls._save_conversation(question, error_msg, user_id, session_id, start_time, status="failed")
