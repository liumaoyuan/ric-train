"""聊天助手 Agent - Agent 管理与执行

使用 LangChain create_agent() API:
  - @tool 装饰器定义工具
  - ChatMemoryMiddleware 管理对话记忆（Redis + MySQL）
"""
import json
import logging
from typing import AsyncGenerator, List

from langchain.agents import create_agent
from langchain_community.chat_models import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from Base.Config.setting import settings
from CateringAiSystem.Agent.memory import AgentMemory
from CateringAiSystem.Agent.middleWare import ChatMemoryMiddleware
from CateringAiSystem.Agent.tools import knowledge_search, data_query, web_search, general_chat

logger = logging.getLogger(__name__)

# ── Agent 实例缓存 ──
_agent_instances: dict = {}

def _get_qwen_chat_model(**kwargs) -> BaseChatModel:
    qwen_config = settings.dashscope
    return ChatOpenAI(
        model=kwargs.pop("model", qwen_config.model or "qwen-plus"),
        api_key=kwargs.pop("api_key", qwen_config.api_key),
        base_url=kwargs.pop("base_url", qwen_config.base_url)
        or "https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=kwargs.pop("temperature", 0.7),
        **kwargs,
    )


def _get_tools_for_role(role_codes: List[str]) -> list:
    has_boss = "admin" in role_codes
    has_franchisee = "franchisee" in role_codes
    tools = [knowledge_search, data_query, general_chat]
    if has_boss or (not has_franchisee):
        tools.append(web_search)
    return tools


# ── System Prompt ──

SYSTEM_PROMPT_TPL = """你是一个连锁餐饮企业的 AI 智能助手，名叫"小餐"。
你的职责是帮助用户解答关于公司制度、门店数据、菜品知识等各类问题。

{memory_context}

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


async def create_agent_for_session(
    session_id: str,
    user_id: str,
    role_codes: List[str],
    enable_search: bool = False,
) -> "ChatAgent":
    """为指定会话创建或获取 Agent 实例"""
    cache_key = f"{user_id}:{session_id}"
    if cache_key in _agent_instances:
        return _agent_instances[cache_key]

    agent = ChatAgent(
        session_id=session_id,
        user_id=user_id,
        role_codes=role_codes,
        enable_search=enable_search,
    )
    await agent._build()
    _agent_instances[cache_key] = agent
    return agent


def clear_agent_cache(user_id: str = None, session_id: str = None):
    global _agent_instances
    if user_id and session_id:
        _agent_instances.pop(f"{user_id}:{session_id}", None)
    elif user_id:
        _agent_instances = {k: v for k, v in _agent_instances.items() if not k.startswith(f"{user_id}:")}
    else:
        _agent_instances = {}


class ChatAgent:
    """聊天助手 Agent"""

    def __init__(self, session_id: str, user_id: str, role_codes: List[str], enable_search: bool = False):
        self.session_id = session_id
        self.user_id = user_id
        self.role_codes = role_codes
        self.enable_search = enable_search
        self._agent = None

    async def _build(self):
        """构建 LangChain Agent（含记忆加载）"""
        tools = _get_tools_for_role(self.role_codes)

        # 从记忆层加载上下文（Redis → MySQL）
        memory_msgs, summary_text = await AgentMemory.build_memory_messages(
            session_id=self.session_id,
            user_id=self.user_id,
            max_recent=20,
        )
        memory_context = ""
        for m in memory_msgs:
            if isinstance(m, SystemMessage):
                memory_context += f"【历史摘要】{m.content}\n"
            elif isinstance(m, HumanMessage):
                memory_context += f"用户:{m.content}\n"
            elif isinstance(m, AIMessage):
                memory_context += f"助手:{m.content}\n"

        tool_descriptions = "\n".join([f"- {t.name}: {t.description}" for t in tools])
        system_prompt = SYSTEM_PROMPT_TPL.format(
            memory_context=memory_context,
            tool_descriptions=tool_descriptions,
        )

        llm = _get_qwen_chat_model()

        self._agent = create_agent(
            model=llm,
            system_prompt=system_prompt,
            tools=tools,
            middleware=[
                # 自定义记忆中间件（负责摘要压缩 + Redis/MySQL 持久化）
                ChatMemoryMiddleware(
                    llm=_get_qwen_chat_model(),
                    session_id=self.session_id,
                    user_id=self.user_id,
                    max_chat_round=20,
                    max_tokens=5000,
                ),
            ],
        )

    async def astream(self, question: str) -> AsyncGenerator[dict, None]:
        """流式执行 Agent，产生 SSE 事件"""
        if not self._agent:
            yield {"type": "error", "content": "Agent 未初始化"}
            return

        config = {"configurable": {"thread_id": self.session_id}}

        try:
            full_content = ""
            async for event in self._agent.astream_events(
                {"messages": [HumanMessage(content=question)]},
                config=config,
                version="v1",
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
                    self.session_id,
                    ("user", question),
                    ("assistant", full_content),
                )

        except Exception as e:
            logger.error(f"Agent 流式执行异常: {e}", exc_info=True)
            yield {"type": "error", "content": f"处理异常: {e}"}

    async def arun(self, question: str) -> str:
        """非流式执行 Agent"""
        if not self._agent:
            return "Agent 未初始化"

        config = {"configurable": {"thread_id": self.session_id}}

        try:
            result = await self._agent.ainvoke(
                {"messages": [HumanMessage(content=question)]},
                config=config,
            )
            messages = result.get("messages", []) if isinstance(result, dict) else getattr(result, "messages", [])
            answer = ""
            if messages:
                last = messages[-1]
                answer = last.content if hasattr(last, "content") else str(last)
            else:
                answer = str(result)

            # Agent 执行完成 → 推送到 Redis 短期记忆
            if answer:
                await AgentMemory.push_to_redis(
                    self.session_id,
                    ("user", question),
                    ("assistant", answer),
                )
            return answer

        except Exception as e:
            logger.error(f"Agent 执行异常: {e}", exc_info=True)
            return f"处理异常: {e}"
