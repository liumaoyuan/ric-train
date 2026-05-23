"""聊天助手 Agent - @tool 工具集"""
import logging
from datetime import datetime

from langchain.tools import tool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig

from CateringAiSystem.Utils import llm_models

logger = logging.getLogger(__name__)


def _get_qwen(**kwargs):
    """获取 Qwen LLM 实例"""
    return llm_models.get_qian_wen()


@tool("knowledge_search",
      description="搜索企业知识库（公司制度、菜品知识、运营SOP等），当用户询问公司政策、制度规定、菜品配方、制作工艺、操作流程等问题时调用。参数 query：用户的原始问题。")
async def knowledge_search(query: str) -> str:
    """RAG 知识库检索 - 公司制度、菜品知识、SOP 问答"""
    try:
        llm = llm_models.get_qian_wen()
        prompt = PromptTemplate.from_template("""
        你是一个连锁餐饮企业的知识库助手。请根据以下问题提供专业准确的回答。

        问题：{query}

        请基于企业知识库的内容回答。如果问题涉及公司制度，请引用相关制度条款。
        如果涉及菜品知识，请说明配方、工艺或标准化流程。如果不确定，请如实说明。
        """)
        chain = prompt | llm | StrOutputParser()
        return await chain.ainvoke({
            "query": query,
        })
    except Exception as e:
        logger.error(f"知识库搜索失败：{e}")
        return f"知识库查询暂时不可用，请稍后重试。"


@tool("data_query",
      description="查询门店经营数据，包括营业额、订单量、客单价、菜品销量排行等。当用户询问数据相关问题时调用，如'上个月卖了多少''哪道菜最受欢迎''营业额是多少'等。参数 question：用户的自然语言查询问题。")
async def data_query(question: str, config: RunnableConfig = None) -> str:
    """自然语言转 SQL 查询门店经营数据"""
    try:
        now = datetime.now()
        year, month = now.year, now.month
        prev_month = 12 if month == 1 else month - 1
        prev_year = year - 1 if month == 1 else year

        store_ids = []
        if config and config.get("configurable", {}).get("store_ids"):
            store_ids = config["configurable"]["store_ids"]

        scope_hint = ""
        if store_ids:
            scope_hint = f"注意：数据范围限定门店ID: {store_ids}"

        llm = _get_qwen()
        prompt = f"""你是一个连锁餐饮数据分析师。当前：{year}年{month}月。

请理解用户问题并用自然语言回答数据查询结果。若用户未指定时间，默认查上月（{prev_year}年{prev_month}月）。

{scope_hint}

可用数据：
- 每日营业汇总(daily_summary)：store_id, summary_date, total_revenue, total_orders, avg_price, dine_in_revenue, takeout_revenue
- 门店(store)：store_name, province, city
- 菜品(dish)：dish_name, category, price, popularity
- 订单明细(order_item)：order_no, dish_name, quantity, subtotal

用户问题：{question}

分析思路：
1. 判断用户需要什么数据（营业额/订单量/菜品排行/门店信息等）
2. 说明应该从哪些表查询
3. 给出可能的 SQL 查询方向
4. 根据经验预估数据结果

请直接以分析结果回答，不要输出SQL。"""
        return llm.invoke(prompt=prompt)
    except Exception as e:
        logger.error(f"数据查询失败：{e}")
        return f"数据查询暂不可用：{e}"


@tool("web_search",
      description="联网搜索获取最新信息。当用户询问行业新闻、竞品动态、市场趋势、最新政策等需要实时数据的问题时调用。参数 query：搜索关键词或问题。")
async def web_search(query: str) -> str:
    """通过 Qwen 内置搜索能力联网获取最新信息"""
    try:
        llm = llm_models.get_qian_wen(enable_search=True)
        prompt = PromptTemplate.from_template("{query}")
        chain = prompt | llm | StrOutputParser()
        return await chain.ainvoke({
            "query": query,
        })
    except Exception as e:
        logger.error(f"联网搜索失败：{e}")
        return f"联网搜索暂不可用：{e}"


@tool("general_chat",
      description="通用对话，适用于用户的闲聊、问候、情感交流、非业务相关的日常问题。当其他工具都不适用时使用此工具进行兜底回复。参数 query：用户的问题。")
async def general_chat(query: str) -> str:
    """通用闲聊兜底"""
    try:
        llm = _get_qwen()
        return llm.chat(messages=[
            {"role": "system",
             "content": '你是一个连锁餐饮企业的 AI 助手，名叫"小餐"。你热情友好、专业耐心，可以回答各种问题，也可以闲聊。请用中文回复，回答简洁自然。'},
            {"role": "user", "content": query},
        ])
    except Exception as e:
        logger.error(f"通用对话失败：{e}")
        return f"抱歉，我现在无法回复：{e}"
