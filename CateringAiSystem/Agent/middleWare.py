"""聊天助手 Agent - 自定义记忆压缩中间件

工作流：
  1. Agent 执行前：从 Redis 加载短期记忆（Redis 空则回退 MySQL）
  2. Agent 执行后：将新对话追加到 Redis
  3. 检查是否超过最大轮数或 token 数 → 触发 AI 摘要压缩
  4. 压缩后更新 Redis + MySQL 摘要，截断消息列表
"""
import contextvars
import logging
from typing import List, Callable, Any

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    BaseMessage, SystemMessage, ToolMessage, AIMessage, HumanMessage,
)

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
        max_chat_round: int = 20,
        max_tokens: int = 5000,
    ):
        self.llm = llm
        self.max_chat_round = max_chat_round
        self.max_tokens = max_tokens

    async def __call__(
        self,
        state: AgentState,
        next: Callable[[AgentState], Any],
    ) -> AgentState:
        # 从 contextvars 获取当前会话（支持全局单例 Agent）
        session_id = get_session_id()

        messages: List[BaseMessage] = state.get("messages", [])

        # 1. 拆分消息：系统、工具、普通对话
        sys_msgs = [m for m in messages if isinstance(m, SystemMessage)]
        tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
        chat_msgs = [m for m in messages if isinstance(m, (HumanMessage, AIMessage))]

        # 2. 计算是否超过阈值
        total_chars = sum(len(m.content) for m in chat_msgs if m.content)
        exceed_round = len(chat_msgs) > self.max_chat_round
        exceed_tokens = total_chars > self.max_tokens

        if not exceed_round and not exceed_tokens:
            return await next(state)

        # 3. 分割：早期需要摘要的 + 近期保留的
        keep_count = self.max_chat_round
        need_summary = chat_msgs[:-keep_count]
        keep_latest = chat_msgs[-keep_count:]

        # 4. LLM 对早期对话做智能摘要
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
            return await next(state)

        summary_msg = AIMessage(content=f"【历史对话摘要】:{summary_text}")

        # 5. 持久化摘要到 Redis + MySQL
        try:
            await AgentMemory.compress_and_save(
                session_id=session_id,
                summary_text=summary_text,
                keep_rounds=self.max_chat_round,
            )
        except Exception as e:
            logger.warning(f"摘要持久化失败: {e}")

        # 6. 重新拼接: 系统 + 摘要 + 近期原话 + 工具消息
        new_messages = sys_msgs + [summary_msg] + keep_latest + tool_msgs
        state["messages"] = new_messages

        logger.info(
            f"记忆压缩完成 | session={session_id[:8]} "
            f"压缩前={len(chat_msgs)}轮 压缩后={len(keep_latest)}轮"
        )
        return await next(state)

    @staticmethod
    def _format_msgs(msgs: List[BaseMessage]) -> str:
        lines = []
        for m in msgs:
            role = "用户" if isinstance(m, HumanMessage) else "AI"
            lines.append(f"{role}:{m.content}")
        return "\n".join(lines)
