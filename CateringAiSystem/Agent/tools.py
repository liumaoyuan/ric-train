"""聊天助手 Agent - @tool 工具集

工具清单:
  - knowledge_search:  知识库 RAG 检索
  - data_query:        自然语言转 SQL 查询门店经营数据（真实执行）
  - web_search:        联网搜索（通义千问内置）
  - general_chat:      通用闲聊兜底
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from langchain.tools import tool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig

from CateringAiSystem.Utils import llm_models

logger = logging.getLogger(__name__)


# ── Schema 定义（业务表结构，用于 NL2SQL 注入） ──

BUSINESS_SCHEMA = """
数据库: catering_ai_system

表 store（门店）:
  store_id          INT           PRIMARY KEY   # 门店ID
  store_name        VARCHAR(100)                # 门店名称（格式：省+城市+xxx店）
  province          VARCHAR(50)                 # 省份
  city              VARCHAR(50)                 # 城市
  address           VARCHAR(255)                # 详细地址
  status            TINYINT       DEFAULT 1     # 状态 1营业 0停业
  open_date         DATE                        # 开业日期

表 dish（菜品）:
  dish_id           INT           PRIMARY KEY   # 菜品ID
  dish_name         VARCHAR(100)                # 菜品名称
  category          VARCHAR(50)                 # 分类（如：招牌、主食、汤品、小吃、饮品）
  price             DECIMAL(10,2)               # 价格
  popularity        INT           DEFAULT 0     # 受欢迎程度（权重，越高越常被点）

表 daily_summary（每日营业汇总）:
  store_id          INT                         # 门店ID
  summary_date      DATE                        # 日期
  total_revenue     DECIMAL(12,2)  DEFAULT 0    # 总营业额
  total_orders      INT           DEFAULT 0     # 总订单数
  avg_price         DECIMAL(10,2) DEFAULT 0     # 客单价
  dine_in_revenue   DECIMAL(12,2) DEFAULT 0     # 堂食营业额
  takeout_revenue   DECIMAL(12,2) DEFAULT 0     # 外卖营业额

表 dine_in_order（堂食订单）:
  order_no          VARCHAR(50)   PRIMARY KEY   # 订单号
  store_id          INT                         # 门店ID
  order_date        DATETIME                    # 下单时间
  total_amount      DECIMAL(10,2)               # 金额
  payment_method    VARCHAR(20)                 # 支付方式（微信支付/支付宝/现金）

表 takeout_order（外卖订单）:
  order_no          VARCHAR(50)   PRIMARY KEY   # 订单号
  store_id          INT                         # 门店ID
  order_date        DATETIME                    # 下单时间
  total_amount      DECIMAL(10,2)               # 金额
  platform          VARCHAR(50)                 # 外卖平台
  delivery_fee      DECIMAL(10,2) DEFAULT 0     # 配送费

表 order_item（订单明细）:
  id                BIGINT        PRIMARY KEY   # ID
  order_no          VARCHAR(50)                 # 订单号（关联 dine_in_order/takeout_order）
  dish_name         VARCHAR(100)                # 菜品名称
  quantity          INT           DEFAULT 1     # 数量
  subtotal          DECIMAL(10,2)               # 小计金额

表 review（评论）:
  review_id         BIGINT        PRIMARY KEY   # 评论ID
  store_id          INT                         # 门店ID
  platform          VARCHAR(50)                 # 平台来源
  rating            TINYINT                     # 评分 1-5
  content           TEXT                        # 评论内容
  review_date       DATETIME                    # 评论时间
"""


# ── 工具函数 ──

def _get_llm(**kwargs):
    return llm_models.get_qian_wen(**kwargs)


# ═══════════════════════════════════════════════
# knowledge_search
# ═══════════════════════════════════════════════

@tool("knowledge_search",
      description="搜索企业知识库（公司制度、菜品知识、运营SOP等）。当用户询问公司政策、制度规定、菜品配方、制作工艺、操作流程等问题时调用。参数 query：用户的原始问题。")
async def knowledge_search(query: str) -> str:
    """RAG 知识库检索——后续接入真实 Milvus 向量检索"""
    try:
        # TODO: 接入真实 Milvus 知识库检索
        # from CateringAiSystem.Service.knowledgeService import KnowledgeService
        # docs = await KnowledgeService.asearch(query, top_k=5)
        # context = "\n\n".join(d.content for d in docs)
        # prompt = f"基于以下知识库内容回答问题：\n\n{context}\n\n问题：{query}"
        # return await _get_llm().ainvoke(prompt)

        llm = _get_llm()
        prompt = PromptTemplate.from_template(
            "你是一个连锁餐饮企业的知识库助手。请根据以下问题提供专业准确的回答。\n\n"
            "问题：{query}\n\n"
            "请基于企业知识库的内容回答。如果问题涉及公司制度，请引用相关制度条款。"
            "如果涉及菜品知识，请说明配方、工艺或标准化流程。如果不确定，请如实说明。"
        )
        chain = prompt | llm | StrOutputParser()
        return await chain.ainvoke({"query": query})
    except Exception as e:
        logger.error("知识库搜索失败：%s", e)
        return "知识库查询暂时不可用，请稍后重试。"


# ═══════════════════════════════════════════════
# data_query
# ═══════════════════════════════════════════════

@tool("data_query",
      description="查询门店经营数据，包括营业额、订单量、客单价、菜品销量排行等。当用户询问数据相关问题时调用。参数 question：用户的自然语言查询问题。")
async def data_query(question: str, config: Optional[RunnableConfig] = None) -> str:
    """自然语言转 SQL 查询门店经营数据（真实 NL2SQL 执行）"""
    try:
        now = datetime.now()
        year, month = now.year, now.month
        prev_m = 12 if month == 1 else month - 1
        prev_y = year - 1 if month == 1 else year

        # 获取门店权限范围
        store_ids = []
        if config and config.get("configurable", {}).get("store_ids"):
            store_ids = config["configurable"]["store_ids"]

        scope_hint = ""
        if store_ids:
            scope_hint = f"注意：数据范围限定门店ID: {store_ids}"

        llm = _get_llm()

        # Step 1: LLM 生成 SQL
        sql_prompt = (
            f"你是一个专业的 SQL 生成助手。当前时间：{year}年{month}月。\n\n"
            f"数据库 Schema：\n{BUSINESS_SCHEMA}\n\n"
            f"用户问题：{question}\n\n"
            f"{scope_hint}\n"
            f"若用户未指定时间，默认查上月（{prev_y}年{prev_m}月）。\n\n"
            f"重要规则：\n"
            f"1. 只返回标准 SQL 语句（MySQL），不要任何解释、注释或 markdown\n"
            f"2. 仅生成 SELECT 查询\n"
            f"3. 数值类聚合推荐使用 ROUND(x, 2)\n"
            f"4. 门店维度查询时注意按 store_id 或 store_name 分组\n"
            f"5. 自动加 LIMIT 200 上限"
        )
        sql = await llm.ainvoke(sql_prompt)
        sql_text = sql.content if hasattr(sql, "content") else str(sql)
        sql_text = sql_text.strip().removeprefix("```sql").removesuffix("```").strip()

        # Step 2: 安全校验
        if not sql_text.upper().startswith("SELECT"):
            return "安全限制：仅支持 SELECT 查询。请重新表述您的问题。"

        dangerous = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE", "EXEC"]
        sql_upper = sql_text.upper()
        for kw in dangerous:
            if f" {kw} " in f" {sql_upper} " or sql_upper.startswith(kw):
                return f"安全限制：禁止执行 {kw} 操作。"

        # Step 3: 执行 SQL（通过 ConnectionManager 获取连接）
        from Base.Repository.base.connectionManager import ConnectionManager
        conn = ConnectionManager.get_default()
        if conn is None:
            return "数据库连接不可用，请检查数据库配置。"

        try:
            rows = await asyncio.to_thread(conn.execute, sql_text)
        except Exception as sql_err:
            logger.warning("SQL 执行失败，重试: %s", sql_err)
            # 发给 LLM 修正
            fix_prompt = (
                f"以下 SQL 执行出错：\n{sql_text}\n\n"
                f"错误信息：{sql_err}\n\n"
                f"请根据 Schema 修正 SQL：\n{BUSINESS_SCHEMA}\n"
                f"只输出修正后的 SQL 语句。"
            )
            fixed = await llm.ainvoke(fix_prompt)
            fixed_sql = fixed.content if hasattr(fixed, "content") else str(fixed)
            fixed_sql = fixed_sql.strip().removeprefix("```sql").removesuffix("```").strip()
            rows = await asyncio.to_thread(conn.execute, fixed_sql)

        # Step 4: LLM 总结回答
        result_str = str(rows[:20]) if rows else "无数据"  # 只取前 20 行防止超出 token
        summary_prompt = (
            f"用户问题：{question}\n\n"
            f"查询结果：{result_str}\n\n"
            f"请用自然语言总结查询结果，回答简洁明了。如果结果为空，请告知用户。"
        )
        summary = await llm.ainvoke(summary_prompt)
        return summary.content if hasattr(summary, "content") else str(summary)

    except Exception as e:
        logger.error("数据查询失败：%s", e)
        return f"数据查询暂不可用，请稍后重试。"


# ═══════════════════════════════════════════════
# web_search
# ═══════════════════════════════════════════════

@tool("web_search",
      description="联网搜索获取最新信息。当用户询问行业新闻、竞品动态、市场趋势、最新政策等需要实时数据的问题时调用。参数 query：搜索关键词或问题。")
async def web_search(query: str) -> str:
    """通义千问内置联网搜索"""
    try:
        llm = _get_llm(enable_search=True)
        resp = await llm.ainvoke(query)
        return resp.content if hasattr(resp, "content") else str(resp)
    except Exception as e:
        logger.error("联网搜索失败：%s", e)
        return "联网搜索暂不可用，请稍后重试。"


# ═══════════════════════════════════════════════
# general_chat
# ═══════════════════════════════════════════════

@tool("general_chat",
      description="通用对话，适用于用户的闲聊、问候、情感交流、非业务相关的日常问题。当其他工具都不适用时使用此工具进行兜底回复。参数 query：用户的问题。")
async def general_chat(query: str) -> str:
    """通用闲聊兜底"""
    try:
        llm = _get_llm()
        resp = await llm.ainvoke([
            {"role": "system",
             "content": '你是一个连锁餐饮企业的 AI 助手，名叫"小餐"。你热情友好、专业耐心，可以回答各种问题，也可以闲聊。请用中文回复，回答简洁自然。'},
            {"role": "user", "content": query},
        ])
        return resp.content if hasattr(resp, "content") else str(resp)
    except Exception as e:
        logger.error("通用对话失败：%s", e)
        return f"抱歉，我现在无法回复：{e}"


# ── 工具映射表（供 graph.py 路由使用） ──

TOOL_MAP = {
    "knowledge_search": knowledge_search,
    "data_query": data_query,
    "web_search": web_search,
    "general_chat": general_chat,
}
