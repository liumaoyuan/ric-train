"""聊天助手 Agent - LangGraph StateGraph 定义

执行流:
  call_model → should_continue → call_tool (循环) / summary_node / __end__

节点:
  - call_model:   LLM 推理 + 工具选择决策（注入 System Prompt）
  - call_tool:    根据 LLM 工具调用路由到具体 @tool 执行
  - summary_node: 消息超过阈值时 AI 摘要压缩
"""
import logging
from typing import Any, Dict, Literal, Sequence

from langchain_core.messages import (
    AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage,
    RemoveMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.redis import AsyncRedisSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

from CateringAiSystem.Agent.memory import AgentMemory
from CateringAiSystem.Agent.middleWare import get_session_id
from CateringAiSystem.Agent.tools import TOOL_MAP, knowledge_search, data_query, web_search, general_chat
from CateringAiSystem.Utils import llm_models

from langfuse import observe

logger = logging.getLogger(__name__)

# ── Agent 状态 ──

class AgentState(TypedDict):
    """Agent State - 消息列表由 add_messages reducer 管理"""
    messages: Annotated[Sequence[BaseMessage], add_messages]

# ── 压缩阈值 ──

MAX_CHAT_ROUND = 15
MAX_CHARS = 5000
KEEP_ROUNDS = 5

# ── System Prompt（不持久化到 Checkpointer，每次 call_model 注入） ──

SYSTEM_PROMPT = """你是一个连锁餐饮企业的 AI 智能助手，名叫"小餐"。

## 可用工具
- knowledge_search: 搜索企业知识库（公司制度、菜品知识、运营SOP等）
- data_query: 查询门店经营数据（营业额、订单量、客单价、菜品销量排行等）
- web_search: 联网搜索（行业新闻、竞品动态、最新政策等）
- general_chat: 通用对话（闲聊、问候、情感交流等）

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


# ═══════════════════════════════════════════
# 节点函数
# ═══════════════════════════════════════════

@observe(as_type="generation", name="LLM_模型调用")
async def call_model(state: AgentState, config: RunnableConfig) -> dict:
    """LLM 推理节点：注入 System Prompt → 绑定工具 → 判断回复或调用工具"""
    messages = list(state["messages"])

    role_codes: list = config["configurable"].get("role_codes", ["admin"])
    tools = _pick_tools(role_codes)

    # System Prompt 注入到消息开头（不持久化到 Checkpointer）
    full_messages = [SystemMessage(content=SYSTEM_PROMPT), *messages]

    llm = llm_models.get_qian_wen()
    llm_with_tools = llm.bind_tools(tools)

    response: AIMessage = await llm_with_tools.ainvoke(full_messages)
    return {"messages": [response]}

@observe(as_type="tool", name="工具执行")
async def call_tool(state: AgentState, config: RunnableConfig) -> dict:
    """工具执行节点：遍历 LLM 输出的 tool_calls 并执行对应工具"""
    messages = state["messages"]
    last_msg = messages[-1] if messages else None
    if not last_msg or not getattr(last_msg, "tool_calls", None):
        return {"messages": []}

    results: list[ToolMessage] = []
    for tc in last_msg.tool_calls:
        tool_name = tc["name"]
        tool_args = dict(tc.get("args", {}))
        tool_id = tc["id"]

        tool_fn = TOOL_MAP.get(tool_name)
        if not tool_fn:
            logger.warning("未知工具: %s", tool_name)
            results.append(ToolMessage(
                content=f"未知工具: {tool_name}", tool_call_id=tool_id, name=tool_name,
            ))
            continue

        # 注入 RunnableConfig（某些工具需要 config 参数）
        tool_args["config"] = config

        try:
            result = await tool_fn.ainvoke(tool_args)
            content = result if isinstance(result, str) else str(result)
        except Exception as e:
            logger.error("工具 %s 执行失败: %s", tool_name, e)
            content = f"工具执行失败: {e}"

        results.append(ToolMessage(content=content, tool_call_id=tool_id, name=tool_name))

    return {"messages": results}

@observe(as_type="generation", name="记忆压缩_摘要生成")
async def summary_node(state: AgentState, config: RunnableConfig) -> dict:
    """记忆压缩节点：超过阈值时对早期对话做 AI 摘要，保留最近 KEEP_ROUNDS 轮"""
    messages = state["messages"]
    session_id = get_session_id()

    chat_msgs = [m for m in messages if isinstance(m, (HumanMessage, AIMessage))]
    if len(chat_msgs) <= KEEP_ROUNDS * 2:
        return {}

    need_summary = chat_msgs[:-KEEP_ROUNDS * 2]
    keep_latest = chat_msgs[-KEEP_ROUNDS * 2:]

    # LLM 生成摘要
    formatted = _format_msgs(need_summary)
    llm = llm_models.get_qian_wen()
    try:
        resp = await llm.ainvoke(
            f"请简洁总结以下多轮对话的核心内容、关键信息和重要约定，精简但不要丢失重要信息：\n"
            f"{formatted}\n只输出总结一段话，不要多余内容。"
        )
        summary_text = resp.content if hasattr(resp, "content") else str(resp)
    except Exception as e:
        logger.warning("摘要生成失败: %s", e)
        return {}

    # 持久化摘要
    try:
        await AgentMemory.save_summary(session_id, summary_text)
    except Exception as e:
        logger.warning("摘要持久化失败: %s", e)

    # 删除所有需要摘要的旧消息，按正确顺序重新添加：摘要 + 近期对话
    remove_ids = [RemoveMessage(id=m.id) for m in need_summary if m.id]
    summary_msg = SystemMessage(content=f"【历史对话摘要】\n{summary_text}")

    logger.info("记忆压缩完成 | session=%s | 压缩 %d 条", session_id, len(need_summary))
    # 先删除旧消息，再按正确顺序添加摘要 + 近期对话
    return {"messages": [*remove_ids, summary_msg, *keep_latest]}

@observe(as_type="span", name="路由判断", capture_input=False)
def should_continue(state: AgentState) -> Literal["call_tool", "summary_node", "__end__"]:
    """条件边：tool 调用 → call_tool；超阈值 → summary_node；否则结束"""
    msgs = state.get("messages", [])
    if msgs:
        last = msgs[-1]
        if getattr(last, "tool_calls", None):
            return "call_tool"

    chat_msgs = [m for m in msgs if isinstance(m, (HumanMessage, AIMessage))]
    if len(chat_msgs) > MAX_CHAT_ROUND * 2:
        total = sum(len(m.content or "") for m in chat_msgs if m.content)
        if total > MAX_CHARS:
            return "summary_node"

    return "__end__"


# ═══════════════════════════════════════════
# 内部辅助
# ═══════════════════════════════════════════

def _pick_tools(role_codes: list[str]) -> list:
    """根据角色选取可用工具"""
    has_boss = "admin" in role_codes
    has_franchisee = "franchisee" in role_codes
    tools = [knowledge_search, data_query, general_chat]
    if has_boss or (not has_franchisee):
        tools.append(web_search)
    return tools


def _format_msgs(msgs: Sequence[BaseMessage]) -> str:
    lines = []
    for m in msgs:
        role = "用户" if isinstance(m, HumanMessage) else "AI"
        lines.append(f"{role}:{m.content or ''}")
    return "\n".join(lines)


# ═══════════════════════════════════════════
# 构建 StateGraph
# ═══════════════════════════════════════════

def build_agent(saver: AsyncRedisSaver) -> StateGraph:
    """构建并编译 LangGraph StateGraph

    Args:
        saver: AsyncRedisSaver 实例（全局共享，由 agentManager 管理生命周期）
    """
    workflow = StateGraph(AgentState)
    workflow.add_node("call_model", call_model)
    workflow.add_node("call_tool", call_tool)
    workflow.add_node("summary_node", summary_node)

    workflow.set_entry_point("call_model")

    workflow.add_conditional_edges(
        "call_model",
        should_continue,
        {"call_tool": "call_tool", "summary_node": "summary_node", "__end__": END},
    )
    workflow.add_edge("call_tool", "call_model")    # 工具执行后回到 LLM 继续推理
    workflow.add_edge("summary_node", END)          # 压缩后结束（响应已就绪）

    return workflow.compile(checkpointer=saver)
