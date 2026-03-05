# 游戏攻略数据库模块

## 概述

本模块提供游戏攻略存储功能，支持实体关联和语义搜索。

## 表结构

### MySQL 表

#### 1. game_strategy - 攻略主表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT UNSIGNED | 主键 ID |
| title | VARCHAR(500) | 攻略标题 |
| content | TEXT | 攻略正文内容 |
| source_url | VARCHAR(1000) | 来源链接 |
| game_name | VARCHAR(100) | 游戏名称 |
| strategy_type | VARCHAR(50) | 攻略类型 |
| status | TINYINT UNSIGNED | 状态 (0-禁用，1-启用) |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |
| created_by | BIGINT UNSIGNED | 创建人 ID |
| updated_by | BIGINT UNSIGNED | 更新人 ID |

#### 2. game_entity - 游戏实体表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT UNSIGNED | 主键 ID |
| entity_name | VARCHAR(100) | 实体名称 |
| entity_code | VARCHAR(50) | 实体编码 |
| entity_type | VARCHAR(50) | 实体类型 (hero/mode/item/skill) |
| game_name | VARCHAR(100) | 所属游戏 |
| aliases | VARCHAR(500) | 别名/外号列表 |
| description | TEXT | 实体描述 |
| status | TINYINT UNSIGNED | 状态 |

#### 3. game_strategy_entity_rel - 攻略 - 实体关联表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT UNSIGNED | 主键 ID |
| strategy_id | BIGINT UNSIGNED | 攻略 ID |
| entity_id | BIGINT UNSIGNED | 实体 ID |
| relevance_score | INT UNSIGNED | 相关性权重 |
| created_at | DATETIME | 创建时间 |
| created_by | BIGINT UNSIGNED | 创建人 ID |

### VDB 向量表

#### game_strategy - 攻略向量表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 (auto_id) |
| db_id | str | MySQL 中的攻略 ID |
| title | str | 标题 (支持 BM25 搜索) |
| content | str | 攻略内容 |
| game_name | str | 游戏名称 |
| strategy_type | str | 攻略类型 |
| entity_names | str | 关联实体名称列表 |
| embedding | List[float] | 密集向量 (dim=1024) |
| title_sparse | List[float] | 稀疏向量 (基于 title 的 BM25) |

## 文件结构

```
GameHelper/
├── models/
│   ├── gameStrategyModel.py      # MySQL 攻略主表模型
│   ├── gameEntityModel.py        # MySQL 游戏实体表模型
│   ├── gameStrategyEntityRelModel.py  # 关联表模型
│   └── pojo/
│       ├── gameStrategyPo.py     # 攻略数据对象
│       └── gameEntityPo.py       # 实体数据对象
├── VdbModels/
│   └── VdbGameStrategy.py        # VDB 攻略向量表模型
├── services/
│   └── gameStrategyService.py    # 业务逻辑层
└── db/
    ├── dataInit.py               # 初始化脚本
    └── testStrategyDb.py         # 测试脚本
```

## 使用方法

### 1. 初始化表结构

```python
from GameHelper.db.dataInit import init_game_strategy_tables

# 创建所有表结构
init_game_strategy_tables()
```

### 2. 初始化测试数据

```python
from GameHelper.db.dataInit import init_test_game_strategy_data

# 创建测试攻略和实体数据
init_test_game_strategy_data()
```

### 3. 创建攻略

```python
from GameHelper.services.gameStrategyService import GameStrategyService
from GameHelper.models.pojo.gameStrategyPo import GameStrategyCreateRequest

request = GameStrategyCreateRequest(
    title="海克斯大乱斗 杰斯出装推荐",
    content="杰斯在海克斯大乱斗中的最强出装...",
    source_url="https://example.com/guide/1",
    game_name="英雄联盟",
    strategy_type="出装",
    entity_names=["杰斯", "海克斯大乱斗"]
)

strategy = GameStrategyService.create_strategy(request, created_by=1)
```

### 4. 查询攻略

```python
# 根据 ID 查询
strategy = GameStrategyService.get_strategy_by_id(strategy_id)

# 根据游戏名称查询
strategies = GameStrategyService.get_strategies_by_game("英雄联盟", limit=100)

# 根据实体查询
strategies = GameStrategyService.get_strategies_by_entity("杰斯", limit=10)

# 语义搜索
results = GameStrategyService.search_strategies("杰斯出装", game_name="英雄联盟", limit=10)
```

### 5. 更新攻略

```python
from GameHelper.models.pojo.gameStrategyPo import GameStrategyUpdateRequest

request = GameStrategyUpdateRequest(
    title="新标题",
    content="新内容",
    status=0  # 禁用
)

GameStrategyService.update_strategy(strategy_id, request, updated_by=1)
```

### 6. 删除攻略

```python
# 软删除
GameStrategyService.delete_strategy(strategy_id)
```

### 7. 实体管理

```python
from GameHelper.services.gameStrategyService import GameEntityService

# 获取或创建实体
entity = GameEntityService.get_or_create_entity("杰斯", "英雄联盟", "hero")

# 创建实体
entity = GameEntityService.create_entity(
    entity_name="杰斯",
    entity_code="jayce",
    entity_type="hero",
    game_name="英雄联盟",
    aliases="未来守护者",
    description="来自皮尔特沃夫的天才发明家"
)

# 根据名称获取实体
entity = GameEntityService.get_entity_by_name("杰斯", "英雄联盟")

# 根据类型获取实体
entities = GameEntityService.get_entities_by_type("hero", "英雄联盟", limit=100)
```

## 运行测试

```bash
# 激活虚拟环境
.venv/Scripts/activate

# 运行测试脚本
python GameHelper/db/testStrategyDb.py
```

## 运行完整初始化

```bash
# 激活虚拟环境
.venv/Scripts/activate

# 运行初始化脚本
python GameHelper/db/dataInit.py
```

## 注意事项

1. 数据库连接：确保 `base_module` 数据库连接已正确配置
2. VDB 连接：确保 Milvus 向量数据库连接已正确配置
3. 日志编码：Windows 环境下可能需要设置 PYTHONUTF8=1 环境变量
