"""聊天助手 Agent - 全局单例 Agent 管理（仅流式）

根据角色列表缓存全局单例 CompiledStateGraph，通过 LangGraph Checkpointer
（thread_id = session_id）自动管理会话状态，无需手动加载/保存记忆。

使用方式:
  agent = await get_agent_for_role(["admin"])
  async for event in agent.astream({"messages": [msg]}, config):
      ...
"""
import logging
from typing import List, Optional

import redis.asyncio as aioredis
from langgraph.checkpoint.redis import AsyncRedisSaver
from langgraph.graph.state import CompiledStateGraph

from Base.Config.setting import settings
from CateringAiSystem.Agent.graph import build_agent

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
            db=rc.db,
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
