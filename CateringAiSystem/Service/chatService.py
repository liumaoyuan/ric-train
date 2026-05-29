"""聊天助手服务 - 编排 LangGraph StateGraph Agent 工作流（仅流式）

会话状态由 LangGraph Checkpointer 自动管理（thread_id = session_id），
无需手动加载/保存记忆。
"""
import json
import logging
import time
from typing import AsyncGenerator, Optional

from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.types import Command

from Base.Service.aiService import AuditingTextError
from CateringAiSystem.Agent import (
    AgentMemory,
    get_agent_for_role,
)
from CateringAiSystem.Agent.middleWare import set_session_context

logger = logging.getLogger(__name__)


class ChatService:
    """聊天助手服务（仅流式）"""

    # ── 会话管理 ──

    @staticmethod
    def get_or_create_session(user_id: str, title: str = None):
        return AgentMemory.get_or_create_session(user_id, title)

    @staticmethod
    def list_sessions(user_id: str, limit: int = 50, offset: int = 0):
        return AgentMemory.list_sessions(user_id, limit, offset)

    @staticmethod
    async def delete_session(session_id: str, user_id: str) -> bool:
        return await AgentMemory.delete_session(session_id, user_id)

    @staticmethod
    def get_conversation_history(session_id: str, user_id: str) -> list:
        return AgentMemory.get_conversation_history(session_id, user_id)

    # ── AI 对话（仅流式） ──

    @classmethod
    async def ask_stream(
        cls,
        question: str,
        user_id: str,
        session_id: Optional[str] = None,
        user_info: Optional[dict] = None,
    ) -> AsyncGenerator[str, None]:
        """流式对话 - LangGraph StateGraph astream(messages)"""
        start_time = time.time()
        session = None
        actual_session_id = None

        try:
            # 1. 会话
            session = AgentMemory.get_or_create_session(user_id, session_uuid=session_id)
            actual_session_id = session.session_uuid

            yield f"data: {json.dumps({'type': 'start', 'session_id': actual_session_id}, ensure_ascii=False)}\n\n"

            # 2. 关键词替换
            safe_question = question
            # safe_question = keyword_replace_question(question)

            # 3. 文本审核（暂跳过）
            # auditing_dict = AiService.auditing_text(safe_question)
            # ...

            # 4. 问题改写（暂跳过）
            # final_question = AiService.rewrite_question(...) or safe_question
            final_question = safe_question

            # 5. 角色权限
            roles = (user_info or {}).get("roles", ["employee"])
            store_ids = (user_info or {}).get("store_ids", [])

            # 6. 设置运行时上下文
            set_session_context(actual_session_id, user_id)

            # 7. 通过 Checkpointer Agent 流式执行
            #  Checkpointer 自动从 thread_id 恢复历史消息
            agent = await get_agent_for_role(role_codes=roles)
            config = {
                "configurable": {
                    "thread_id": actual_session_id,
                    "role_codes": roles,
                    "store_ids": store_ids,
                }
            }

            input_message = HumanMessage(content=final_question)
            full_content = ""

            # 使用 stream_mode="messages" 逐 token 输出
            async for event in agent.astream(
                {"messages": [input_message]},
                config=config,
                stream_mode="messages",
            ):
                if isinstance(event, tuple) and len(event) == 2:
                    chunk, metadata = event
                    if isinstance(chunk, AIMessageChunk):
                        node = metadata.get("langgraph_node", "")
                        content = chunk.content or ""
                        if node == "call_model" and content:
                            yield f"data: {json.dumps({'type': 'content', 'content': content}, ensure_ascii=False)}\n\n"
                            full_content += content

            # 8. 检查是否因人工审核中断
            try:
                state = await agent.aget_state(config)
                if state and state.next:
                    for interrupt_item in state.interrupts:
                        review_data = interrupt_item.value
                        if isinstance(review_data, dict) and review_data.get("type") == "human_review":
                            review_event = json.dumps({
                                'type': 'human_review',
                                'session_id': actual_session_id,
                                'data': review_data,
                            }, ensure_ascii=False)
                            yield f"data: {review_event}\n\n"
                            return  # 等待前端 resume，不保存对话
            except Exception as e:
                logger.warning("检查中断状态失败: %s", e)

            # 9. 持久化对话记录到 MySQL（供前端历史展示）
            if full_content:
                cls._save_conversation(
                    question, full_content, user_id, actual_session_id, start_time,
                )

            yield f"data: {json.dumps({'type': 'done', 'session_id': actual_session_id}, ensure_ascii=False)}\n\n"

        except AuditingTextError:
            error_msg = "内容审核未通过，请重新输入"
            cls._save_and_yield_error(question, error_msg, user_id, actual_session_id or session_id, start_time)
        except Exception as e:
            logger.error("对话处理异常: %s", e, exc_info=True)
            error_msg = "抱歉，服务器错误，请稍后再试"
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg}, ensure_ascii=False)}\n\n"
            cls._save_conversation(
                question, error_msg, user_id,
                actual_session_id or (session.session_uuid if session else "unknown"),
                start_time, status="failed",
            )

    @classmethod
    async def resume_stream(
        cls,
        session_id: str,
        decision: dict,
        user_id: str,
        user_info: Optional[dict] = None,
    ) -> AsyncGenerator[str, None]:
        """人工审核后恢复 Agent 执行（流式）"""
        start_time = time.time()
        roles = (user_info or {}).get("roles", ["employee"])
        store_ids = (user_info or {}).get("store_ids", [])

        try:
            agent = await get_agent_for_role(role_codes=roles)
            config = {
                "configurable": {
                    "thread_id": session_id,
                    "role_codes": roles,
                    "store_ids": store_ids,
                }
            }

            set_session_context(session_id, user_id)

            # 从 checkpoint 获取原始问题（用于保存对话记录）
            original_question = ""
            try:
                state_snap = await agent.aget_state(config)
                if state_snap and state_snap.values:
                    for m in reversed(state_snap.values.get("messages", [])):
                        if isinstance(m, HumanMessage):
                            original_question = m.content if hasattr(m, "content") else ""
                            break
            except Exception:
                pass

            full_content = ""

            async for event in agent.astream(
                Command(resume=decision),
                config=config,
                stream_mode="messages",
            ):
                if isinstance(event, tuple) and len(event) == 2:
                    chunk, metadata = event
                    if isinstance(chunk, AIMessageChunk):
                        node = metadata.get("langgraph_node", "")
                        content = chunk.content or ""
                        if node == "call_model" and content:
                            yield f"data: {json.dumps({'type': 'content', 'content': content}, ensure_ascii=False)}\n\n"
                            full_content += content

            # 检查是否再次中断（连续审核场景）
            try:
                state = await agent.aget_state(config)
                if state and state.next:
                    for interrupt_item in state.interrupts:
                        review_data = interrupt_item.value
                        if isinstance(review_data, dict) and review_data.get("type") == "human_review":
                            review_event = json.dumps({
                                'type': 'human_review',
                                'session_id': session_id,
                                'data': review_data,
                            }, ensure_ascii=False)
                            yield f"data: {review_event}\n\n"
                            return
            except Exception as e:
                logger.warning("检查中断状态失败: %s", e)

            if full_content:
                cls._save_conversation(
                    original_question, full_content, user_id, session_id, start_time,
                )

            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error("恢复执行异常: %s", e, exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'content': '恢复执行失败'}, ensure_ascii=False)}\n\n"
            cls._save_conversation(
                "", f"恢复执行失败: {e}", user_id, session_id, start_time, status="failed",
            )

    # ── 内部工具 ──

    @classmethod
    def _save_conversation(
        cls, question: str, answer: str, user_id: str,
        session_id: str, start_time: float, status: str = "success",
    ):
        AgentMemory.save_conversation(
            question=question, answer=answer,
            user_id=user_id, session_id=session_id,
            duration_ms=int((time.time() - start_time) * 1000),
            status=status,
        )

    @classmethod
    async def _save_and_yield_error(
        cls, question, error_msg, user_id, session_id, start_time,
    ):
        cls._save_conversation(
            question, error_msg, user_id, session_id, start_time, status="failed",
        )
