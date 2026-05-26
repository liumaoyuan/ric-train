"""聊天助手 Agent - 全局单例 Agent 管理

根据角色列表缓存全局单例 CompiledStateGraph，通过 LangGraph Checkpointer
（thread_id = session_id）自动管理会话状态，无需手动加载/保存记忆。

使用方式:
  agent = await get_agent_for_role(["admin"])
  async for event in agent.astream({"messages": [msg]}, config):
      ...
"""
import logging
from typing import AsyncGenerator, List, Optional

import redis.asyncio as aioredis
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.redis import AsyncRedisSaver
from langgraph.graph.state import CompiledStateGraph

from Base.Config.setting import settings
from CateringAiSystem.Agent.graph import build_agent
from CateringAiSystem.Agent.middleWare import set_session_context

logger = logging.getLogger(__name__)


# ── 全局单例 Agent 缓存（按角色） ──

_role_agents: dict[str, CompiledStateGraph] = {}

# ── 全局 Checkpointer（AsyncRedisSaver，所有 Agent 共享） ──

_saver: Optional[AsyncRedisSaver] = None
_saver_initialized = False


def _checkpointer() -> AsyncRedisSaver:
    """获取全局 AsyncRedisSaver 单例"""
    global _saver
    if _saver is None:
        rc = settings.redis
        redis_client = aioredis.Redis(
            host=rc.host, port=rc.port,
            password=rc.password or None,
            db=rc.db, decode_responses=True,
        )
        _saver = AsyncRedisSaver(
            redis_client=redis_client,
            ttl={"default_ttl": 3 * 24 * 60, "refresh_on_read": True},
        )
    return _saver


async def ensure_saver_ready():
    """确保 Checkpointer 已初始化（asetup）"""
    global _saver_initialized
    if not _saver_initialized:
        saver = _checkpointer()
        try:
            await saver.asetup()
            _saver_initialized = True
            logger.info("AsyncRedisSaver 索引初始化完成")
        except Exception as e:
            logger.error("AsyncRedisSaver 初始化失败: %s", e)
            raise


def _role_key(role_codes: List[str]) -> str:
    return ":".join(sorted(role_codes))


async def get_agent_for_role(role_codes: List[str]) -> CompiledStateGraph:
    """根据角色列表获取或创建全局单例 Agent"""
    await ensure_saver_ready()
    key = _role_key(role_codes)
    if key not in _role_agents:
        _role_agents[key] = build_agent(_checkpointer())
        logger.info("创建角色 Agent: %s", key)
    return _role_agents[key]


def clear_cache():
    """清空角色 Agent 缓存（测试用）"""
    _role_agents.clear()


# ── 全局状态（供 graph.py 节点通过 RunnableConfig 读取） ──
# role_codes / store_ids 等信息在每次 arun() 时注入到 config 中


class ChatAgent:
    """聊天助手 Agent（全局单例，按角色复用）"""

    @staticmethod
    async def astream(
        question: str,
        session_id: str,
        user_id: str,
        role_codes: Optional[List[str]] = None,
        store_ids: Optional[List[int]] = None,
    ) -> AsyncGenerator[dict, None]:
        """流式对话——使用 CompiledStateGraph.astream()"""
        set_session_context(session_id, user_id)

        agent = await get_agent_for_role(role_codes or ["employee"])
        config = {
            "configurable": {
                "thread_id": session_id,
                "role_codes": role_codes or ["employee"],
                "store_ids": store_ids or [],
            }
        }

        input_msg = HumanMessage(content=question)

        # 使用 stream_mode="messages" 逐 token 产出
        async for event in agent.astream(
            {"messages": [input_msg]},
            config=config,
            stream_mode="messages",
        ):
            yield event

    @staticmethod
    async def ainvoke(
        question: str,
        session_id: str,
        user_id: str,
        role_codes: Optional[List[str]] = None,
        store_ids: Optional[List[int]] = None,
    ) -> str:
        """非流式对话"""
        set_session_context(session_id, user_id)

        agent = await get_agent_for_role(role_codes or ["employee"])
        config = {
            "configurable": {
                "thread_id": session_id,
                "role_codes": role_codes or ["employee"],
                "store_ids": store_ids or [],
            }
        }

        input_msg = HumanMessage(content=question)
        result = await agent.ainvoke(
            {"messages": [input_msg]},
            config=config,
        )

        # 提取最终回复
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content and not getattr(msg, "tool_calls", None):
                return msg.content if isinstance(msg.content, str) else str(msg.content)
        return ""
