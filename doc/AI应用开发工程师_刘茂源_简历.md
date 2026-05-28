# 刘茂源 — AI 应用开发工程师

---

## 个人信息

| 项目 | 内容 |
|------|------|
| 求职意向 | AI 应用开发工程师 |
| 技术栈 | Python / LangGraph / FastAPI / LangChain / RAG / LLMOps |
| 工作经验 | 3 年+ |

---

## 专业技能

### AI / LLM 应用开发
- 精通 **LangGraph StateGraph** 构建有状态 Agent，掌握 Checkpointer 持久化、节点级 RetryPolicy、条件边路由等核心机制，有从 AgentExecutor 到 StateGraph 的实际迁移经验
- 熟悉 **RAG** 完整链路搭建：文档解析（PDF/Word）→ 分块策略（固定长度/段落/递归/QA对）→ Embedding 向量化 → Milvus 混合检索 → ReRank 重排序 → LLM 生成回答
- 集成 **RAGAS** 质量评估框架（Hit Rate / MRR / Faithfulness / Answer Relevancy），以 CI 门禁保障检索质量
- 实现真实 **NL2SQL** 链路：Schema 注入 → LLM 生成 SQL → 三层安全防护（只读事务 + 白名单 + LIMIT上限）→ 执行 → LLM 总结

### LLMOps 与工程优化
- 语义缓存（Redis，按角色隔离 + 场景 TTL），命中率 ~20%，月节省 LLM 费用 ~15%
- 多级模型降级链路：Qwen 限流 → 指数退避重试 → DeepSeek 降级 → 固定提示兜底
- 集成 **LangFuse** 可观测性追踪（全链路调用链 / Token 消耗 / 响应耗时 / 工具调用分布）
- **SSE 流式输出** + 前端 ReadableStream + AbortController 取消请求

### 后端工程
- **FastAPI** 异步框架，Pydantic 类型校验，异步数据库操作
- **RBAC** 权限模型（用户-角色-菜单三级），JWT 认证，函数级权限装饰器
- 多数据源管理：MySQL / Redis / Milvus / MinIO
- APScheduler 定时任务系统，支持动态 CRUD 和任务日志追踪

### 工具与平台
- LLM：通义千问（Qwen）、DeepSeek（含模型切换与降级）
- 向量数据库：Milvus（密集向量 + 稀疏向量 BM25 混合检索）
- 基础设施：Docker / Docker Compose / Git
- 前端协作：Vue 3 基础协作经验

---

## 项目经历

### 连锁餐饮 AI 系统 — AI 应用开发工程师

**技术栈：** Python / LangGraph / FastAPI / LangChain / Milvus / Redis / Vue 3 / Qwen / DeepSeek

**项目背景：** 面向 500 家门店的连锁中式快餐品牌，构建 AI 辅助管理系统。解决"规模扩张与管理半径"的矛盾——总部人力有限，加盟商缺乏数据驱动的决策工具。系统覆盖智能问答、数据分析、知识库检索、风评监控四大模块，服务老板、员工、加盟商三种角色。

**核心贡献：**

#### 1. Agent 架构设计与实现
主导从 LangChain AgentExecutor 到 **LangGraph StateGraph** 的技术选型与迁移。最终采用单 Agent + 4 工具架构（`knowledge_search` / `data_query` / `web_search` / `general_chat`），按角色缓存全局单例 Agent，通过 LangGraph 的 `thread_id` 实现会话隔离，解决了全局单例与多会话冲突的难题。StateGraph 执行流包含三个核心节点（`call_model` LLM 推理 → `call_tool` 工具执行 → `summary_node` 记忆压缩），通过条件边实现动态路由。

#### 2. RAG 知识库系统
搭建完整 RAG 链路：文档上传（PDF/Word）→ MinIO 存储 → 文本提取 → 分块（4 种策略可选）→ 前端逐块预览确认 → Embedding 向量化 → Milvus 存储。检索侧采用混合检索（密集向量 + 标量权限过滤）+ ReRank 重排序。集成 **RAGAS** 质量评估体系，设定 Hit Rate > 90%、Faithfulness > 85% 等量化目标，作为 CI 门禁防止质量回退。

#### 3. NL2SQL 真实数据查询
在 `data_query` 工具中实现真实 NL2SQL 链路：用户自然语言 → Schema 注入 → LLM 生成 SQL → 安全校验 → 数据库执行 → LLM 总结回答。设计三层安全防护体系：
- 数据库连接层：只读事务，从根本上禁止写操作
- SQL 语法层：表名白名单校验，禁止 DROP/DELETE/ALTER 等操作，自动加 LIMIT 200
- 异常处理层：SQL 执行失败时发送错误信息给 LLM 自动修正，最多重试 2 次

#### 4. LLM 成本优化与可观测性
- **语义缓存**：问题 MD5 + 角色构成缓存键（`semantic_cache:{role}:{md5}`），按场景区分 TTL（闲聊 1h / 知识 24h / 数据 10min），预估命中率 ~20%
- **多级模型降级**：Qwen API 限流 → 指数退避（1s→2s→4s）→ 自动切换 DeepSeek → 固定提示兜底
- **LangFuse 追踪**：全链路追踪 Agent 调用链、Token 消耗、工具调用分布，每月产出《LLM 调用分析报告》驱动成本优化

#### 5. 系统架构与权限体系
- 基于 FastAPI 的异步后端架构，支持 SSE 流式输出（逐 token 推送），前端通过 ReadableStream + AbortController 实现流式交互与请求取消
- 实现完整 RBAC 权限系统（用户-角色-菜单三级），按钮级权限粒度，Agent 工具注册按角色动态过滤
- 对话记忆管理采用 LangGraph Checkpointer（Redis 短期快照）+ MySQL 持久化双层策略，超阈值时由 `summary_node` 自动压缩

**量化成果：**

| 指标 | 提升 |
|------|------|
| 加盟商问题响应时间 | 4 小时 → <5 秒 |
| 差评响应时间 | 6~12 小时 → <1 小时 |
| 总部答疑工作量 | 减少约 50% |
| LLM 月费用 | <1000 元 |
| RAG 检索有效率（Hit Rate） | >90%（目标值） |

**技术挑战与解决方案：**

- **全局单例 vs 会话隔离**：按角色缓存 Agent 单例，利用 LangGraph 的 `thread_id` 实现会话状态隔离，避免了 `contextvars` 手动管理的 bug
- **LLM 生成 SQL 不可控**：三层防护（只读事务 + 白名单 + LIMIT）+ 异常自愈重试，在功能与安全间取得平衡
- **千万级数据送入 LLM**：分层分析策略（SQL 预聚合 → 指标计算 → LLM 解读），LLM 只负责"解读"而非"计算"
- **多轮对话记忆膨胀**：summary_node 在超阈值时 AI 摘要压缩，保留最近 5 轮完整对话，成本和体验平衡

---

## 其他项目

### Base 基础框架开发与维护
参与公司自研 Python 基础框架的开发与维护，该框架提供统一的 LLM 抽象层（Qwen/DeepSeek）、多数据库 ORM（MySQL/Milvus/PostgreSQL/SQLite）、第三方客户端封装（Redis/MinIO/Neo4j）等核心能力。框架采用分层架构设计，支持优雅降级——任何外部服务连接失败不阻止程序启动。

---

## 自我评价

- 具备从 0 到 1 构建 AI 应用系统的完整经验，涵盖架构设计、技术选型、编码实现、质量评估
- 关注生产级工程细节：安全防护（NL2SQL 三层安全）、成本控制（语义缓存 + 模型降级）、可观测性（LangFuse 全链路追踪）
- 技术选型注重"匹配业务复杂度"而非"追新"——能清晰阐述 LangGraph vs AgentExecutor vs 多 Agent 的选型理由
- 有量化意识，每个功能模块都设定明确的成功指标和测量方法
