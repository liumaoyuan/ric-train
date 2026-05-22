"""聊天助手 Agent - 记忆管理层

双层记忆存储架构：
  Redis (短期):  agent:memory:{session_id} — 最近 N 轮消息列表
                 agent:summary:{session_id} — AI 摘要
                 TTL: 消息 24h, 摘要 7d
  MySQL (持久):  base_llm_conversation    — 全量对话记录
                 base_llm_session         — 会话元数据 + 摘要

加载优先级: Redis → MySQL（Redis 空时才回退到 MySQL）
"""
import json
import logging
from typing import List, Optional, Tuple

from Base.Config.setting import settings
from Base.Models.BaseLLMConversationModel import BaseLLMConversationModel
from Base.Models.BaseLLMSession import BaseLLMSession
from Base.Service.llmConversationService import save_conversation_from_db_2_vdb_only_data
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

logger = logging.getLogger(__name__)

# ── Redis key 前缀与 TTL ──
MEMORY_KEY_PREFIX = "agent:memory:"
SUMMARY_KEY_PREFIX = "agent:summary:"
MEMORY_TTL = 86400  # 消息列表 24h
SUMMARY_TTL = 604800  # 摘要 7d

# ── 缓存引用（延迟初始化） ──
_async_redis = None


async def _get_redis():
    """延迟获取 async Redis 连接"""
    global _async_redis
    if _async_redis is not None:
        try:
            await _async_redis.ping()
            return _async_redis
        except Exception:
            _async_redis = None
    try:
        redis_config = settings.redis
        import redis.asyncio as aioredis
        _async_redis = aioredis.Redis(
            host=redis_config.host, port=redis_config.port,
            password=redis_config.password or None,
            db=redis_config.db, decode_responses=True,
        )
        await _async_redis.ping()
        logger.info("Async Redis 连接成功 (memory)")
    except Exception as e:
        logger.warning(f"Redis 不可用，将仅使用 MySQL: {e}")
        _async_redis = None
    return _async_redis


class AgentMemory:
    """Agent 记忆管理器"""

    # ──────────────── 会话管理 ────────────────

    @staticmethod
    def get_or_create_session(user_id: str, title: str = None, session_uuid: str = None) -> BaseLLMSession:
        return BaseLLMSession.get_or_create_session(
            user_id=user_id, title=title or "新对话", session_uuid=session_uuid,
        )

    @staticmethod
    def list_sessions(user_id: str, limit: int = 50, offset: int = 0) -> list:
        return BaseLLMSession.get_sessions_by_user(
            user_id=user_id, limit=limit, offset=offset,
        )

    @staticmethod
    async def delete_session(session_id: str, user_id: str) -> bool:
        try:
            session = BaseLLMSession.get_by_session_uuid(session_id)
            if not session or session.user_id != user_id:
                return False
            session.delete()
            for conv in BaseLLMConversationModel.find_by(session_id=session_id, user_id=user_id):
                conv.delete()
            # 同时清除 Redis
            redis_conn = await _get_redis()
            if redis_conn:
                await redis_conn.delete(f"{MEMORY_KEY_PREFIX}{session_id}")
                await redis_conn.delete(f"{SUMMARY_KEY_PREFIX}{session_id}")
            return True
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False

    # ──────────────── 摘要管理 ────────────────

    @staticmethod
    def get_session_summary(session_id: str) -> str:
        try:
            session = BaseLLMSession.get_by_session_uuid(session_id)
            return session.ai_summary or "" if session else ""
        except Exception:
            return ""

    @staticmethod
    def update_session_summary(session_id: str, summary: str):
        try:
            session = BaseLLMSession.get_by_session_uuid(session_id)
            if session:
                session.ai_summary = summary
                session.save()
        except Exception as e:
            logger.error(f"更新 MySQL 摘要失败: {e}")

    # ──────────────── Redis 短期记忆 ────────────────

    @staticmethod
    async def push_to_redis(session_id: str, *messages: Tuple[str, str]):
        """追加消息到 Redis 列表，每条 (role, content)"""
        redis_conn = await _get_redis()
        if not redis_conn:
            return
        key = f"{MEMORY_KEY_PREFIX}{session_id}"
        try:
            for role, content in messages:
                await redis_conn.rpush(key, json.dumps({"role": role, "content": content}, ensure_ascii=False))
            await redis_conn.expire(key, MEMORY_TTL)
        except Exception as e:
            logger.warning(f"Redis 推送失败: {e}")

    @staticmethod
    async def load_from_redis(session_id: str) -> Optional[List[dict]]:
        """从 Redis 加载消息列表，返回 [{"role":..., "content":...}, ...] 或 None"""
        redis_conn = await _get_redis()
        if not redis_conn:
            return None
        key = f"{MEMORY_KEY_PREFIX}{session_id}"
        try:
            raw_list = await redis_conn.lrange(key, 0, -1)
            if not raw_list:
                return None
            messages = []
            for raw in raw_list:
                try:
                    messages.append(json.loads(raw))
                except json.JSONDecodeError:
                    continue
            return messages
        except Exception as e:
            logger.warning(f"Redis 读取失败: {e}")
            return None

    @staticmethod
    async def save_summary_to_redis(session_id: str, summary: str):
        """保存摘要到 Redis"""
        redis_conn = await _get_redis()
        if not redis_conn:
            return
        key = f"{SUMMARY_KEY_PREFIX}{session_id}"
        try:
            await redis_conn.set(key, summary, ex=SUMMARY_TTL)
        except Exception as e:
            logger.warning(f"Redis 摘要保存失败: {e}")

    @staticmethod
    async def load_summary_from_redis(session_id: str) -> Optional[str]:
        """从 Redis 加载摘要"""
        redis_conn = await _get_redis()
        if not redis_conn:
            return None
        key = f"{SUMMARY_KEY_PREFIX}{session_id}"
        try:
            val = await redis_conn.get(key)
            return val if val else None
        except Exception:
            return None

    @staticmethod
    async def clear_redis_memory(session_id: str):
        """清除 Redis 中的会话记忆"""
        redis_conn = await _get_redis()
        if not redis_conn:
            return
        try:
            await redis_conn.delete(f"{MEMORY_KEY_PREFIX}{session_id}")
            await redis_conn.delete(f"{SUMMARY_KEY_PREFIX}{session_id}")
        except Exception as e:
            logger.warning(f"Redis 清除失败: {e}")

    @staticmethod
    async def trim_redis_memory(session_id: str, keep_rounds: int):
        """截断 Redis 消息列表，只保留最近 keep_rounds 条对话"""
        redis_conn = await _get_redis()
        if not redis_conn:
            return
        key = f"{MEMORY_KEY_PREFIX}{session_id}"
        try:
            current_len = await redis_conn.llen(key)
            if current_len > keep_rounds * 2:
                await redis_conn.ltrim(key, -(keep_rounds * 2), -1)
        except Exception as e:
            logger.warning(f"Redis 截断失败: {e}")

    # ──────────────── MySQL 持久化 ────────────────

    @staticmethod
    def load_from_mysql(session_id: str, user_id: str, limit: int = 20) -> List[dict]:
        """从 MySQL 加载最近消息，返回 [{"role":..., "content":...}, ...]"""
        try:
            convs = BaseLLMConversationModel.find_by(
                session_id=session_id, user_id=user_id,
                limit=limit, order_by="created_at", order="ASC",
            )
            messages = []
            for c in convs:
                if c.question:
                    messages.append({"role": "user", "content": c.question})
                if c.answer:
                    answer = c.get_answer if hasattr(c, "get_answer") else c.answer
                    messages.append({"role": "assistant", "content": answer})
            return messages
        except Exception as e:
            logger.error(f"MySQL 加载失败: {e}")
            return []

    @staticmethod
    def save_conversation(
            question: str, answer: str, user_id: str, session_id: str,
            duration_ms: int, rewrite_question: str = "",
            reasoning: str = "", status: str = "success",
    ):
        """保存到 MySQL + Milvus"""
        try:
            store_answer = (
                json.dumps({"reasoning": reasoning, "content": answer}, ensure_ascii=False, separators=(",", ":"))
                if reasoning else answer
            )
            conv = BaseLLMConversationModel(
                question=question, rewrite_question=rewrite_question or "",
                answer=store_answer, user_id=user_id, session_id=session_id,
                stream_mode="1", status=status, duration_ms=duration_ms,
                source="agent_chat",
            )
            conv.save()
            if status == "success":
                save_conversation_from_db_2_vdb_only_data({
                    "id": conv.id, "session_id": session_id, "user_id": user_id,
                    "question": question, "rewrite_question": rewrite_question or "",
                    "answer": answer,
                })
        except Exception as e:
            logger.error(f"MySQL 保存失败: {e}")

    # ──────────────── 前端历史展示 ────────────────

    @staticmethod
    def get_conversation_history(session_id: str, user_id: str) -> list:
        try:
            convs = BaseLLMConversationModel.find_by(
                session_id=session_id, user_id=user_id,
                limit=50, order_by="created_at", order="ASC",
            )
            result = []
            for c in convs:
                if c.question:
                    result.append({"role": "user", "content": c.question})
                if c.answer:
                    answer = c.get_answer if hasattr(c, "get_answer") else c.answer
                    result.append({"role": "assistant", "content": answer})
            return result
        except Exception as e:
            logger.error(f"获取历史失败: {e}")
            return []

    # ──────────────── 记忆构建（供 Agent 使用） ────────────────

    @classmethod
    async def build_memory_messages(
            cls, session_id: str, user_id: str, keep_rounds: int = 5,
    ) -> Tuple[List[BaseMessage], str]:
        """构建记忆上下文消息列表

        策略:
          1. 尝试从 Redis 加载消息列表 + 摘要
          2. Redis 不存在 → 从 MySQL 加载最近消息 → 同步到 Redis
          3. 组合: [摘要SystemMessage] + 对话HumanMessage/AIMessage

        Returns:
          (messages, summary_text) — messages 是 LangChain 消息列表，summary_text 是原始摘要文本
        """
        messages: List[BaseMessage] = []
        summary_text = ""

        # 1. 先从 Redis 加载
        redis_msgs = await cls.load_from_redis(session_id)
        redis_summary = await cls.load_summary_from_redis(session_id)

        if redis_msgs is not None and redis_summary is not None:
            summary_text = redis_summary
        elif redis_msgs is not None:
            summary_text = redis_summary or ""
        else:
            # 2. Redis 空 → 从 MySQL 回退
            mysql_msgs = cls.load_from_mysql(session_id, user_id, limit=keep_rounds)
            summary_text = cls.get_session_summary(session_id)
            if mysql_msgs:
                await cls.push_to_redis(session_id, *[(m["role"], m["content"]) for m in mysql_msgs])
            if summary_text:
                await cls.save_summary_to_redis(session_id, summary_text)
            redis_msgs = mysql_msgs

        # 3. 组装 LangChain 消息列表
        if summary_text:
            messages.append(SystemMessage(content=f"【历史对话摘要】\n{summary_text}"))

        if redis_msgs:
            for m in redis_msgs:
                if m["role"] == "user":
                    messages.append(HumanMessage(content=m["content"]))
                elif m["role"] == "assistant":
                    messages.append(AIMessage(content=m["content"]))

        return messages, summary_text

    @classmethod
    async def compress_and_save(
            cls, session_id: str, summary_text: str, keep_rounds: int = 5,
    ):
        """压缩记忆：更新 Redis + MySQL 摘要，截断消息列表"""
        await cls.save_summary_to_redis(session_id, summary_text)
        cls.update_session_summary(session_id, summary_text)
        await cls.trim_redis_memory(session_id, keep_rounds)
