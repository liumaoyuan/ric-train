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
from langgraph.types import interrupt
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


# ── 需要人工审核的敏感工具 ──

HUMAN_REVIEW_TOOLS = {"data_query", "web_search"}


# ═══════════════════════════════════════════
# 节点函数
# ═══════════════════════════════════════════

@observe(as_type="generation", name="LLM_模型调用")
async def call_model(state: AgentState, config: RunnableConfig) -> dict:
    """LLM 推理节点：注入 System Prompt → 绑定工具 → 判断回复或调用工具"""
    messages = list(state["messages"])

    # 清理孤儿 tool_calls：因中断导致 AI 消息有 tool_calls 但缺少对应 ToolMessage
    tool_call_ids = set()
    resolved_ids = set()
    for msg in messages:
        if isinstance(msg, AIMessage):
            for tc in getattr(msg, "tool_calls", []):
                tool_call_ids.add(tc["id"])
        elif isinstance(msg, ToolMessage):
            resolved_ids.add(msg.tool_call_id)
    orphaned_ids = tool_call_ids - resolved_ids
    if orphaned_ids:
        logger.warning("清理 %d 个孤立 tool_call", len(orphaned_ids))
        messages = [
            m for m in messages
            if not (
                isinstance(m, AIMessage)
                and getattr(m, "tool_calls", None)
                and all(tc["id"] in orphaned_ids for tc in m.tool_calls)
            )
        ]

    role_codes: list = config["configurable"].get("role_codes", ["admin"])
    tools = _pick_tools(role_codes)

    # System Prompt 注入到消息开头（不持久化到 Checkpointer）
    full_messages = [SystemMessage(content=SYSTEM_PROMPT), *messages]

    llm = llm_models.get_deepseek()
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

@observe(as_type="span", name="人工审核")
async def human_review_node(state: AgentState, config: RunnableConfig) -> dict:
    """人工审核节点：敏感工具（data_query / web_search）执行前暂停等待审批"""
    last_msg = state["messages"][-1] if state["messages"] else None
    if not last_msg or not getattr(last_msg, "tool_calls", None):
        return {"messages": []}

    sensitive_calls = [tc for tc in last_msg.tool_calls if tc["name"] in HUMAN_REVIEW_TOOLS]
    if not sensitive_calls:
        return {"messages": []}

    # 暂停图执行，暴露审核信息给前端
    review_data = {
        "type": "human_review",
        "tool_calls": [
            {"name": tc["name"], "args": tc["args"], "id": tc["id"]}
            for tc in sensitive_calls
        ],
    }
    result = interrupt(review_data)

    decision = result.get("decision", "reject") if isinstance(result, dict) else "reject"

    if decision == "reject":
        return {"messages": [
            ToolMessage(
                content=f"管理员拒绝了该操作: {tc['name']}",
                tool_call_id=tc["id"],
                name=tc["name"],
            ) for tc in sensitive_calls
        ]}

    # approve / 放行，让 call_tool 正常执行
    return {"messages": []}


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
    llm = llm_models.get_deepseek()
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
def should_continue(state: AgentState) -> Literal["call_tool", "human_review", "summary_node", "__end__"]:
    """条件边：敏感工具 → human_review；普通工具 → call_tool；超阈值 → summary_node；否则结束"""
    msgs = state.get("messages", [])
    if msgs:
        last = msgs[-1]
        if getattr(last, "tool_calls", None):
            for tc in last.tool_calls:
                if tc["name"] in HUMAN_REVIEW_TOOLS:
                    return "human_review"
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
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("summary_node", summary_node)

    workflow.set_entry_point("call_model")

    workflow.add_conditional_edges(
        "call_model",
        should_continue,
        {
            "call_tool": "call_tool",
            "human_review": "human_review",
            "summary_node": "summary_node",
            "__end__": END,
        },
    )
    workflow.add_edge("call_tool", "call_model")
    workflow.add_edge("human_review", "call_tool")
    workflow.add_edge("summary_node", END)

    return workflow.compile(checkpointer=saver)
