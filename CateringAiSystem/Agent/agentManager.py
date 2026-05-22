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
from langchain_core.messages import HumanMessage

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


async def get_agent_for_role(role_codes: List[str]) -> "ChatAgent":
    """根据角色列表获取或创建全局单例 Agent"""
    key = _get_role_key(role_codes)
    if key not in _role_agents:
        agent = ChatAgent(role_codes=role_codes)
        await agent.build()
        _role_agents[key] = agent
        logger.info(f"创建角色 Agent: {key}")
    return _role_agents[key]


def clear_role_agent_cache():
    """清空所有角色 Agent 缓存（测试用）"""
    _role_agents.clear()


class ChatAgent:
    """聊天助手 Agent（全局单例，按角色复用）"""

    def __init__(self, role_codes: List[str]):
        self.role_codes = role_codes
        self._agent = None

    async def build(self):
        """构建 LangChain Agent（角色级，不含会话记忆）"""
        tools = _get_tools_for_role(self.role_codes)

        tool_descriptions = "\n".join([f"- {t.name}: {t.description}" for t in tools])
        system_prompt = SYSTEM_PROMPT_TPL.format(
            tool_descriptions=tool_descriptions,
        )

        self._agent = create_agent(
            model=llm_models.get_deepseek(),
            system_prompt=system_prompt,
            tools=tools,
            middleware=[
                ChatMemoryMiddleware(
                    llm=llm_models.get_deepseek(),
                    max_chat_round=20,
                    max_tokens=5000,
                ),
            ],
        )

    async def astream(self, session_id: str, user_id: str, question: str) -> AsyncGenerator[dict, None]:
        """流式执行 Agent，产生 SSE 事件"""
        if not self._agent:
            yield {"type": "error", "content": "Agent 未初始化"}
            return

        # 设置运行时上下文（中间件通过 contextvars 读取）
        set_session_context(session_id, user_id)

        # 加载历史记忆作为消息前缀
        memory_msgs, _ = await AgentMemory.build_memory_messages(
            session_id=session_id, user_id=user_id, max_recent=20,
        )
        input_messages = memory_msgs + [HumanMessage(content=question)]

        # config = {"configurable": {"thread_id": session_id}}

        try:
            full_content = ""
            async for event in self._agent.astream_events(
                {"messages": input_messages},
                # config=config,
                # version="v1",
            ):
                kind = event["event"]

                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        full_content += chunk.content
                        yield {"type": "content", "content": chunk.content}

                elif kind == "on_tool_start":
                    tool_input = event["data"].get("input", "")
                    yield {
                        "type": "tool_call",
                        "content": json.dumps(
                            {"tool": event["name"], "input": str(tool_input)[:200]},
                            ensure_ascii=False,
                        ),
                    }

                elif kind == "on_chain_end" and "output" in event["data"]:
                    output = event["data"]["output"]
                    if isinstance(output, dict) and "messages" in output:
                        msgs = output["messages"]
                        if msgs:
                            last = msgs[-1]
                            if hasattr(last, "content") and last.content:
                                full_content = last.content

            # Agent 执行完成 → 推送到 Redis 短期记忆
            if full_content:
                await AgentMemory.push_to_redis(
                    session_id,
                    ("user", question),
                    ("assistant", full_content),
                )

        except Exception as e:
            logger.error(f"Agent 流式执行异常: {e}", exc_info=True)
            yield {"type": "error", "content": f"处理异常: {e}"}

    async def arun(self, session_id: str, user_id: str, question: str) -> str:
        """非流式执行 Agent"""
        if not self._agent:
            return "Agent 未初始化"

        set_session_context(session_id, user_id)

        memory_msgs, _ = await AgentMemory.build_memory_messages(
            session_id=session_id, user_id=user_id, max_recent=20,
        )
        input_messages = memory_msgs + [HumanMessage(content=question)]
        config = {"configurable": {"thread_id": session_id}}

        try:
            result = await self._agent.ainvoke(
                {"messages": input_messages},
                config=config,
            )
            messages = result.get("messages", []) if isinstance(result, dict) else getattr(result, "messages", [])
            answer = ""
            if messages:
                last = messages[-1]
                answer = last.content if hasattr(last, "content") else str(last)
            else:
                answer = str(result)

            if answer:
                await AgentMemory.push_to_redis(
                    session_id,
                    ("user", question),
                    ("assistant", answer),
                )
            return answer

        except Exception as e:
            logger.error(f"Agent 执行异常: {e}", exc_info=True)
            return f"处理异常: {e}"
