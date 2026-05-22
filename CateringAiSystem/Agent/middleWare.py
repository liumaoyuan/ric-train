"""聊天助手 Agent - 自定义记忆压缩中间件

工作流：
  1. Agent 执行前：从 Redis 加载短期记忆（Redis 空则回退 MySQL）
  2. Agent 执行后：将新对话追加到 Redis
  3. 检查是否超过最大条数或 token 数 → 触发 AI 摘要压缩
  4. 压缩后更新 Redis + MySQL 摘要，截断消息列表
"""
import contextvars
import logging
import uuid
from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import AgentState
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    RemoveMessage,
    BaseMessage, SystemMessage, ToolMessage, AIMessage, HumanMessage,
)
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.runtime import Runtime

from CateringAiSystem.Agent.memory import AgentMemory

logger = logging.getLogger(__name__)

# ── 运行时会话上下文（全局单例 Agent 通过 contextvars 区分不同会话） ──
_session_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("session_id", default="")
_user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="")


def set_session_context(session_id: str, user_id: str):
    """设置当前会话上下文（每次调用 Agent 前由 ChatAgent 设置）"""
    _session_id_var.set(session_id)
    _user_id_var.set(user_id)


def get_session_id() -> str:
    return _session_id_var.get()


def get_user_id() -> str:
    return _user_id_var.get()


class ChatMemoryMiddleware(AgentMiddleware):
    """
    自定义对话记忆压缩中间件

    在消息超过阈值时自动对早期对话做 AI 摘要保留最近 N 轮完整对话。
    同时负责在 agent 执行前后与 Redis + MySQL 同步记忆。

    session_id / user_id 通过 contextvars 动态获取，支持全局单例 Agent。
    """

    def __init__(
        self,
        llm: BaseChatModel,
        max_chat_round: int = 15,
        max_tokens: int = 5000,
        keep_rounds: int = 5,
    ):
        super().__init__()
        self.llm = llm
        self.max_chat_round = max_chat_round
        self.max_tokens = max_tokens
        self.keep_rounds = keep_rounds

    async def abefore_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        """模型调用前检查消息数/token数，超出则触发 AI 摘要压缩"""
        session_id = get_session_id()
        messages: list[BaseMessage] = state.get("messages", [])

        # 只对 HumanMessage/AIMessage 计算对话轮次
        chat_msgs = [m for m in messages if isinstance(m, (HumanMessage, AIMessage))]

        total_chars = sum(len(m.content or "") for m in chat_msgs if m.content)
        exceed_round = len(chat_msgs) > self.max_chat_round * 2
        exceed_tokens = total_chars > self.max_tokens

        if not exceed_round and not exceed_tokens:
            return None

        # 分割：早期需要摘要的 + 近期保留的
        need_summary = chat_msgs[:-self.keep_rounds * 2]
        keep_latest = chat_msgs[-self.keep_rounds * 2:]

        # LLM 对早期对话做智能摘要
        formatted = self._format_msgs(need_summary)
        summary_prompt = (
            f"请简洁总结以下多轮对话的核心内容、关键信息和重要约定，精简但不要丢失重要信息：\n"
            f"{formatted}\n只输出总结一段话，不要多余内容。"
        )
        try:
            summary_resp = await self.llm.ainvoke(summary_prompt)
            summary_text = summary_resp.content if hasattr(summary_resp, "content") else str(summary_resp)
        except Exception as e:
            logger.warning(f"记忆摘要生成失败，跳过压缩: {e}")
            return None

        # 持久化摘要到 Redis + MySQL
        try:
            await AgentMemory.compress_and_save(
                session_id=session_id,
                summary_text=summary_text,
                keep_rounds=self.keep_rounds,
            )
        except Exception as e:
            logger.warning(f"摘要持久化失败: {e}")

        # 构建新消息列表：摘要 + 近期对话 + 工具消息
        tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
        summary_msg = SystemMessage(content=f"【历史对话摘要】\n{summary_text}")

        # 确保每条消息都有 ID（add_messages reducer 需要）
        new_messages: list[BaseMessage] = [summary_msg, *keep_latest, *tool_msgs]
        for m in new_messages:
            if m.id is None:
                m.id = str(uuid.uuid4())

        logger.info(
            f"记忆压缩完成 | session={session_id} "
        )

        return {
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                summary_msg,
                *keep_latest,
                *tool_msgs,
            ]
        }

    @staticmethod
    def _format_msgs(msgs: list[BaseMessage]) -> str:
        lines = []
        for m in msgs:
            role = "用户" if isinstance(m, HumanMessage) else "AI"
            lines.append(f"{role}:{m.content}")
        return "\n".join(lines)
