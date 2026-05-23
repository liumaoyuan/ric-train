"""聊天助手 Agent - 全局单例 Agent 管理

根据角色列表实例化全局单例 Agent，通过会话 ID 区分不同用户。
使用 LangChain create_agent() API:
  - @tool 装饰器定义工具
  - ChatMemoryMiddleware 管理对话记忆（Redis + MySQL）
"""
import json
import logging
from typing import AsyncGenerator, List

from langchain.agents import create_agent
from langchain_core.messages import RemoveMessage, HumanMessage

from CateringAiSystem.Agent.memory import AgentMemory
from CateringAiSystem.Agent.middleWare import ChatMemoryMiddleware, set_session_context
from CateringAiSystem.Agent.tools import knowledge_search, data_query, web_search, general_chat
from CateringAiSystem.Utils import llm_models

logger = logging.getLogger(__name__)


def _get_tools_for_role(role_codes: List[str]) -> list:
    has_boss = "admin" in role_codes
    has_franchisee = "franchisee" in role_codes
    tools = [knowledge_search, data_query, general_chat]
    if has_boss or (not has_franchisee):
        tools.append(web_search)
    return tools


# ── System Prompt（不含会话记忆，记忆作为消息传入） ──

SYSTEM_PROMPT_TPL = """你是一个连锁餐饮企业的 AI 智能助手，名叫"小餐"。
你的职责是帮助用户解答关于公司制度、门店数据、菜品知识等各类问题。

## 可用工具
{tool_descriptions}

## 工具使用规则
1. 用户询问公司制度、菜品知识、操作流程 → 使用 knowledge_search
2. 用户询问营业数据、订单情况、菜品销量 → 使用 data_query
3. 用户询问行业新闻、最新资讯、竞品动态 → 使用 web_search（仅限有权限的用户）
4. 用户闲聊、问候、或以上都不适用 → 使用 general_chat

## 重要规范
- 优先使用 knowledge_search 和 data_query，避免杜撰信息
- 每次只调用一个工具，根据返回结果决定下一步
- 收到工具结果后整理成自然语言回答，简洁明了
- 不要暴露工具调用细节，直接呈现结果"""


# ── 全局单例 Agent 缓存（按角色） ──

_role_agents: dict = {}


def _get_role_key(role_codes: List[str]) -> str:
    """生成角色缓存键，确保顺序无关"""
    return ":".join(sorted(role_codes))


async def get_agent_for_role(role_codes: List[str]):
    """根据角色列表获取或创建全局单例 Agent"""
    key = _get_role_key(role_codes)
    if key not in _role_agents:
        _role_agents[key] = build(role_codes)
        logger.info(f"创建角色 Agent: {key}")
    return _role_agents[key]


def clear_role_agent_cache():
    """清空所有角色 Agent 缓存（测试用）"""
    _role_agents.clear()

def build(role_codes):
    """构建 LangChain Agent（角色级，不含会话记忆）"""
    tools = _get_tools_for_role(role_codes)

    tool_descriptions = "\n".join([f"- {t.name}: {t.description}" for t in tools])
    system_prompt = SYSTEM_PROMPT_TPL.format(
        tool_descriptions=tool_descriptions,
    )

    return create_agent(
        model=llm_models.get_qian_wen(),
        system_prompt=system_prompt,
        tools=tools,
        middleware=[
            ChatMemoryMiddleware(
                llm=llm_models.get_deepseek(),
                max_chat_round=15,
                max_tokens=5000,
                keep_rounds=5,
            ),
        ],
    )

class ChatAgent:
    """聊天助手 Agent（全局单例，按角色复用）"""

    async def arun(self, session_id: str, user_id: str, question: str) -> str:
        set_session_context(session_id, user_id)

        memory_msgs, _ = await AgentMemory.build_memory_messages(
            session_id=session_id, user_id=user_id, keep_rounds=5,
        )
        input_messages = memory_msgs + [HumanMessage(content=question)]
        config = {"configurable": {"thread_id": session_id}}
        return ""
