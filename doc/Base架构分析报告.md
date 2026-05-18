# Base 项目架构分析报告

## 概述

**Base** 是一个通用 Python 基础框架，面向 AI + 数据库驱动的业务系统。采用分层架构设计，以 `Base/__init__.py` 为入口自动完成初始化（配置加载、日志设置、默认 LLM 创建），以 `Base/main.py` 作为 FastAPI 应用启动入口。

---

## 目录结构总览

```
Base/
├── __init__.py          # 初始化：加载配置 + 日志 + 创建默认 Qwen LLM
├── main.py              # FastAPI 应用入口（uvicorn :8010）
├── Config/              # 配置管理（Pydantic Settings + .env）
├── Ai/                  # AI/LLM 抽象层（OpenAI 兼容接口）
├── Repository/          # 数据库仓储层（关系型 + 向量数据库）
├── Models/              # 数据模型（MySQL 模型 + Milvus 模型）
├── Service/             # 业务服务层
├── Client/              # 第三方客户端封装
├── RicUtils/            # 工具函数库
├── Meta/                # 设计模式（单例元类）
├── DataSet/             # 数据集管理
├── Api/                 # FastAPI 路由注册
└── test/                # 测试
```

---

## 各模块详细分析

### 1. Config — 配置管理

- 基于 `pydantic_settings.BaseSettings`，自动从项目根目录 `.env` 文件加载
- `Settings` 聚合了 11 个子配置：MySQL, Email, LLM, DashScope, DeepSeek, Redis, FFmpeg, MinIO, Milvus, TencentCOS, Neo4j, TTS, BaseModule
- `BaseEnvSettings` 提供 `to_dict()`, `get()`, 字典式访问，自动类型转换（如 `"true"→True`）
- 日志系统：按天轮转文件日志（保留30天）+ 彩色控制台 + 单独 ERROR 文件
- 日志级别通过 `settings.log_level` 控制

### 2. Ai — AI/LLM 抽象层

核心架构：**抽象基类模式**

```
BaseLlm（抽象基类）
  ├── QwenLlm      # 通义千问实现
  └── DeepSeekLlm  # DeepSeek 实现
```

| 特性 | QwenLlm | DeepSeekLlm |
|------|---------|-------------|
| Streaming | ✓ | ✓ |
| Embedding | ✓ | ✗ |
| ASR | ✓ | ✗ |
| OCR | ✓ | ✗ |
| 思考模式 | ✓ | ✗ |
| 上下文窗口 | 8K~1M | 64K~128K |

- 基于 OpenAI 兼容接口（`openai` SDK），同步/异步双通道
- 统一接口：`invoke()` / `ainvoke()`（简单调用），`chat()` / `achat()`（多消息对话）
- 能力委派模式：`ocr()` → `_ocr()`，先检查 `supports_ocr` 再调用子类实现
- Qwen 独有：思考模式（`reasoning_content`），流式返回 `{"type":"reasoning"/"content"}` 字典
- Qwen 独有：`enable_search` 联网搜索参数
- OCR/ASR/Embedding 使用 `@timing_log` + `@cache_with_params` 装饰器
- 全局默认实例通过 `get_default_qwen_llm()` 获取

### 3. Repository — 数据库仓储层

最复杂层，分为两套独立体系：

#### 3a. 关系型数据库（RDB）

**`BaseConnection`（抽象基类）→ MySQLConnection / PostgreSQLConnection / SQLiteConnection**

- `execute()` 统一入口，自动检测 SQL 操作类型（QUERY/INSERT/UPDATE/DELETE）
- 内置连接不可用时的优雅降级（返回空列表/-1/0）
- 连接池管理（DBUtils.PooledDB）+ 事务上下文管理器

**`BaseDBModel`（Pydantic ORM 模型基类）**

- 三级连接优先级：**实例级别 > 类级别 > 全局默认**
- 驼峰→下划线自动表名，支持 `table_alias` 自定义
- 完整 CRUD：`save()`, `get_by_id()`, `get_all()`, `find_by()`, `find_one_by()`, `delete_by_id()`, `bulk_insert()`
- `save()` 根据 `id` 自动判断 INSERT 或 UPDATE
- `_ensure_table_exists()` 表存在性检查 + 自动建表（`_table_checked` 类变量缓存）
- `bulk_insert()` 分批插入 + 返回 MySQL 批量插入的 ID 范围
- 表存在性检查支持 MySQL / PostgreSQL / SQLite 三种方言

#### 3b. 向量数据库（VDB）

**`BaseVDBConnection`（抽象基类）→ MilvusConnection**

**`BaseVDBModel`（Pydantic Milvus ORM 模型基类）**

- 自动根据子类字段生成 Milvus Collection Schema
- **密集向量**：`list[float]` + `json_schema_extra={'dim': 768}`
- **稀疏向量**：`is_sparse_vector=True` + `bm25_source_field`，自动创建 BM25 函数
- `hybrid_search()`：密集向量 + 稀疏向量混合搜索，支持权重加权、RRFRanker、过滤表达式
- 支持 `auto_id` 主键
- 自动集合创建（`_collection_checked` 类变量缓存）

#### 3c. 连接管理器

- `ConnectionManager` 多数据源管理，键值对注册
- 包导入时自动注册默认连接和 Base 模块连接
- 连接失败不会阻止程序启动（仅记录警告）

### 4. Models — 数据模型

| 模型 | 存储 | 用途 |
|------|------|------|
| `BaseLLMConversationModel` | MySQL | LLM 对话记录 |
| `BaseLLMSession` | MySQL | LLM 会话管理 |
| `VdbLLMConversation` | Milvus | 对话向量存储（混合搜索） |
| `BaseEmailModel` | MySQL | 邮件发送记录 |
| `BaseKeywordModel` | MySQL | 关键词 |
| `VdbKeyword` | Milvus | 关键词向量 |
| `BaseParamsModel` | MySQL | 系统参数 |

亮点：`VdbLLMConversation` 使用密集向量（embedding）+稀疏向量（BM25）混合搜索，权重 0.7:0.3。

### 5. Service — 业务服务层

- **`aiService.py`**：问题改写（embedding→VDB检索→DB历史→LLM重写）+ 文本审核（本地LLM/腾讯云）
- **`MemoryV1Service.py`**：三层记忆体系
  - 【会话摘要】Session 历史摘要
  - 【语义回忆】VDB 混合搜索召回相似对话（distance > 0.5）
  - 【即时记忆】最近 N 轮对话
  - 含 VDB 与 DB 的去重逻辑
- **`llmSessionService.py`**：AI 自动会话摘要生成，增量处理（`last_handle_id`）
- **`keywordService.py`** / **`asrService.py`** / **`ttsService.py`** / **`emailService.py`**
- **`scheduler/`**：定时任务系统（`llmSessionScheduler.py`, `auto_register.py`）

### 6. Client — 第三方客户端封装

- **emailClient.py**：SMTP 邮件（HTML/纯文本/附件/内联图片/重试）
- **redisClient.py**：Redis 缓存
- **minioClient.py**：MinIO 对象存储
- **milvusClient.py**：Milvus 向量数据库
- **neo4jClient.py**：Neo4j 图数据库
- **mysqlClient.py** / **qwen.py** / **asrClient.py** / **ttsClient.py**
- **jiebaClient.py**：分词
- **schedulerClient.py**：调度器
- **tencent/**：腾讯云文本审核

### 7. RicUtils — 工具函数库

| 文件 | 功能 |
|------|------|
| `pathUtils.py` | 项目根目录查找（向上遍历，@lru_cache） |
| `decoratorUtils.py` | 装饰器：单例、计时日志、参数预处理、后置处理 |
| `redisUtils.py` | Redis 缓存装饰器（JSON/Pickle 序列化） |
| `httpUtils.py` | HTTP 请求 |
| `dataUtils.py` / `dateUtils.py` | 数据/日期处理 |
| `fileUtils.py` / `audioFileUtils.py` / `pdfUtils.py` / `docUtils.py` / `excelUtils.py` | 文件处理 |
| `reflectUtils.py` | 反射工具 |

### 8. Api — FastAPI 路由

`Base/Api/ai/chatApi.py`：AI 聊天 API，注册到 FastAPI app，监听 `:8010`。

---

## 设计模式总结

| 模式 | 位置 | 说明 |
|------|------|------|
| 抽象工厂 | `Repository/base/baseConnection.py` | `BaseConnection` → MySQL/PostgreSQL/SQLite |
| 抽象工厂 | `Ai/base/baseLlm.py` | `BaseLlm` → Qwen/DeepSeek |
| 单例 | `Meta/singletonMeta.py` | 线程安全单例元类 |
| 单例 | `RicUtils/decoratorUtils.py` | 装饰器实现的单例 |
| ORM | `Repository/base/baseDBModel.py` | Pydantic 模型 + 自动 CRUD |
| ORM | `Repository/base/baseVDB.py` | Pydantic 模型 + Milvus 自动 Schema |
| 仓储 | `Repository/` | 连接管理 + 数据访问分离 |
| 分层 | 整体架构 | Service → Repository → Connection |
| 外观 | `Client/` | 统一封装第三方服务 |

---

## 初始化流程

```
导入 Base 包时：
  1. Config.setting → 加载 .env → 生成 settings 单例
  2. Config.logConfig → setup_logging() 配置日志系统
  3. Base/__init__.py → create_qwen_llm() 创建默认 LLM
  4. Repository/__init__.py → 注册默认 + Base 模块的 MySQL 连接
  5. 所有连接失败时优雅降级（仅记录警告，不阻止启动）

启动 main.py（FastAPI）时：
  1. 初始化 FastAPI app
  2. 注册 AI Chat API 路由
  3. 自动注册定时任务
  4. uvicorn 启动 :8010
```

---

## 亮点

1. **优雅降级**：任何数据库/外部服务连接失败都不会导致程序整体崩溃
2. **三级连接优先级**（实例>类>全局），灵活支持多数据源和读写分离
3. **VDB Model 自动 Schema 生成**，降低了 Milvus 使用门槛
4. **装饰器驱动的横切关注点**：缓存（Redis）、计时、参数处理
5. **三层记忆体系**：会话摘要 + 语义回忆 + 即时对话
6. **混合搜索封装**：密集向量 + 稀疏向量（BM25）的 Weighted/RRF 融合

## 可改进点

1. `default_qwen_llm` 全局实例在多处被直接修改 `default_params`，存在副作用风险（代码中已有 TODO 标注）
2. 部分模块尚在早期阶段（DataSet 目录、部分 Service 文件）
3. `get_settings()` 的简单实现非线程安全
4. 部分异常处理中使用了裸的 `except Exception`，可考虑更精细的异常分类
