"""聊天助手 Agent - 记忆管理层（面向前端展示层）

LangGraph Checkpointer 接管了运行时状态管理，本层不再管理消息列表。
仅保留：
  - 会话 CRUD（会话列表 / 创建 / 删除）
  - 对话记录持久化（MySQL + Milvus，供前端历史展示）
  - AI 摘要持久化（MySQL + Redis，供前端展示）
"""
import json
import logging
from typing import List, Optional

from Base.Config.setting import settings
from Base.Models.BaseLLMConversationModel import BaseLLMConversationModel
from Base.Models.BaseLLMSession import BaseLLMSession
from Base.Service.llmConversationService import save_conversation_from_db_2_vdb_only_data

logger = logging.getLogger(__name__)

# ── Redis key（仅用于摘要缓存） ──

SUMMARY_KEY_PREFIX = "agent:summary:"
SUMMARY_TTL = 604800  # 7 天

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
        import redis.asyncio as aioredis
        rc = settings.redis
        _async_redis = aioredis.Redis(
            host=rc.host, port=rc.port,
            password=rc.password or None,
            db=rc.db, decode_responses=True,
        )
        await _async_redis.ping()
    except Exception as e:
        logger.warning("Redis 不可用 (memory): %s", e)
        _async_redis = None
    return _async_redis


class AgentMemory:
    """Agent 记忆管理器（面向前端展示层）"""

    # ──────────────── 会话管理 ────────────────

    @staticmethod
    def get_or_create_session(user_id: str, title: str = None, session_uuid: str = None) -> BaseLLMSession:
        return BaseLLMSession.get_or_create_session(
            user_id=user_id, title=title or "新对话", session_uuid=session_uuid,
        )

    @staticmethod
    def list_sessions(user_id: str, limit: int = 50, offset: int = 0) -> list:
        return BaseLLMSession.get_sessions_by_user(user_id=user_id, limit=limit, offset=offset)

    @staticmethod
    async def delete_session(session_id: str, user_id: str) -> bool:
        try:
            session = BaseLLMSession.get_by_session_uuid(session_id)
            if not session or session.user_id != user_id:
                return False
            session.delete()
            for conv in BaseLLMConversationModel.find_by(session_id=session_id, user_id=user_id):
                conv.delete()
            # 清除 Redis 摘要缓存
            redis_conn = await _get_redis()
            if redis_conn:
                await redis_conn.delete(f"{SUMMARY_KEY_PREFIX}{session_id}")
            return True
        except Exception as e:
            logger.error("删除会话失败: %s", e)
            return False

    # ──────────────── 摘要管理 ────────────────

    @staticmethod
    def get_session_summary(session_id: str) -> str:
        try:
            session = BaseLLMSession.get_by_session_uuid(session_id)
            return session.ai_summary or "" if session else ""
        except Exception:
            return ""

    @classmethod
    async def save_summary(cls, session_id: str, summary: str):
        """同时保存到 MySQL + Redis（供 summary_node 使用）"""
        cls._update_mysql_summary(session_id, summary)
        await cls._save_redis_summary(session_id, summary)

    @staticmethod
    def _update_mysql_summary(session_id: str, summary: str):
        try:
            session = BaseLLMSession.get_by_session_uuid(session_id)
            if session:
                session.ai_summary = summary
                session.save()
        except Exception as e:
            logger.error("更新 MySQL 摘要失败: %s", e)

    @staticmethod
    async def _save_redis_summary(session_id: str, summary: str):
        redis_conn = await _get_redis()
        if not redis_conn:
            return
        try:
            await redis_conn.set(f"{SUMMARY_KEY_PREFIX}{session_id}", summary, ex=SUMMARY_TTL)
        except Exception as e:
            logger.warning("Redis 摘要保存失败: %s", e)

    # ──────────────── 对话持久化（MySQL + Milvus，供前端历史展示） ────────────────

    @staticmethod
    def save_conversation(
        question: str, answer: str, user_id: str, session_id: str,
        duration_ms: int, rewrite_question: str = "",
        reasoning: str = "", status: str = "success",
    ):
        """保存对话记录到 MySQL + Milvus"""
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
            logger.error("MySQL 保存失败: %s", e)

    # ──────────────── 前端历史展示 ────────────────

    @staticmethod
    def get_conversation_history(session_id: str, user_id: str) -> list:
        """获取会话历史（供前端展示）"""
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
            logger.error("获取历史失败: %s", e)
            return []
