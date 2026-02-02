# SQL 日志记录功能使用指南

## 概述

`BaseConnection` 提供了自动 SQL 执行日志记录功能，可以帮助开发调试和监控数据库操作。

## 功能特性

1. **自动记录所有 SQL 执行**
   - 自动记录 SQL 语句和参数
   - 显示操作类型（QUERY, INSERT, UPDATE, DELETE）
   - 记录执行结果（行数、插入 ID 等）

2. **智能参数格式化**
   - 自动将参数值格式化到 SQL 语句中
   - 正确处理 NULL 值
   - 转义字符串中的特殊字符
   - 支持多种数据类型（字符串、数字、布尔值、列表等）

3. **错误日志**
   - SQL 执行失败时自动记录错误信息
   - 显示失败的 SQL 语句和参数

## 使用方法

### 1. 基本启用

```python
import logging

# 方法 1: 设置全局日志级别为 DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 方法 2: 只启用 SQL 相关的日志
logging.getLogger('Base.Repository.base.baseConnection').setLevel(logging.DEBUG)
```

### 2. 日志输出格式

日志格式：`[时间戳] - [模块名] - [日志级别] - [操作类型] SQL 语句`

**示例输出：**

```
2026-02-02 14:30:25 - Base.Repository.base.baseConnection - DEBUG - [INSERT] INSERT INTO users (name, age) VALUES ('张三', 25)
2026-02-02 14:30:26 - Base.Repository.base.baseConnection - DEBUG - 提交事务，插入 ID: 1
2026-02-02 14:30:27 - Base.Repository.base.baseConnection - DEBUG - [QUERY] SELECT * FROM users WHERE age >= 25
2026-02-02 14:30:27 - Base.Repository.base.baseConnection - DEBUG - 查询返回 3 行数据
2026-02-02 14:30:28 - Base.Repository.base.baseConnection - DEBUG - [UPDATE] UPDATE users SET age = 26 WHERE name = '张三'
2026-02-02 14:30:28 - Base.Repository.base.baseConnection - DEBUG - 提交事务，影响行数: 1
```

### 3. 完整示例

```python
import logging
from Base.Repository.connections.mysqlConnection import MySQLConnection
from Base.Config.setting import settings

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 创建连接
db = MySQLConnection(
    host=settings.mysql.host,
    user=settings.mysql.user,
    password=settings.mysql.password,
    database="my_database"
)

# 执行 SQL - 自动记录日志
db.execute("INSERT INTO users (name, age) VALUES (%s, %s)", ("张三", 25))
db.execute("SELECT * FROM users WHERE age >= %s", (20,))
db.execute("UPDATE users SET age = %s WHERE name = %s", (26, "张三"))

db.close()
```

### 4. 日志级别说明

| 级别 | 说明 | 用途 |
|------|------|------|
| DEBUG | 详细的调试信息，包括 SQL 语句和参数 | 开发和调试 |
| INFO | 一般信息，如连接池创建、事务提交等 | 生产环境监控 |
| WARNING | 警告信息 | 需要注意但不影响运行的情况 |
| ERROR | 错误信息，如 SQL 执行失败 | 问题排查 |

### 5. 配置不同的日志级别

#### 开发环境（记录所有 SQL）
```python
logging.basicConfig(level=logging.DEBUG)
```

#### 生产环境（只记录错误）
```python
logging.basicConfig(level=logging.ERROR)
```

#### 只记录 SQL 相关的 DEBUG 日志
```python
# SQL 相关日志使用 DEBUG
logging.getLogger('Base.Repository.base.baseConnection').setLevel(logging.DEBUG)

# 其他模块使用 INFO
logging.basicConfig(level=logging.INFO)
```

### 6. 日志输出到文件

```python
import logging

# 配置日志输出到文件
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='sql.log',  # 输出到文件
    filemode='a'  # 追加模式
)
```

### 7. 使用不同的日志格式

```python
# 简洁格式
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s: %(message)s'
)

# 包含文件名和行号
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s'
)
```

## 参数格式化示例

| SQL | 参数 | 格式化后的 SQL |
|-----|------|---------------|
| `SELECT * FROM users WHERE id = %s` | `(1,)` | `SELECT * FROM users WHERE id = 1` |
| `INSERT INTO users (name) VALUES (%s)` | `("张三",)` | `INSERT INTO users (name) VALUES ('张三')` |
| `UPDATE users SET age = %s WHERE name = %s` | `(26, "李四")` | `UPDATE users SET age = 26 WHERE name = '李四'` |
| `SELECT * FROM users WHERE email = %s` | `(None,)` | `SELECT * FROM users WHERE email = NULL` |
| `INSERT INTO users (text) VALUES (%s)` | `("It's a test",)` | `INSERT INTO users (text) VALUES ('It''s a test')` |

## 错误日志示例

```
2026-02-02 14:30:25 - Base.Repository.base.baseConnection - ERROR - SQL 执行失败: Duplicate entry '1' for key 'PRIMARY'
2026-02-02 14:30:25 - Base.Repository.base.baseConnection - ERROR - 失败 SQL: INSERT INTO users (id, name) VALUES (%s, %s)
2026-02-02 14:30:25 - Base.Repository.base.baseConnection - ERROR - 参数: (1, '张三')
```

## 注意事项

1. **敏感数据**：SQL 日志可能包含敏感信息（如密码），在生产环境中建议使用 INFO 或更高级别
2. **性能影响**：DEBUG 级别的日志会有轻微性能影响，生产环境建议使用 INFO 或 ERROR 级别
3. **文件大小**：长时间运行可能导致日志文件过大，建议配置日志轮转
4. **PyMySQL 日志**：PySQL 本身的查询日志功能有限，推荐使用本实现

## 日志轮转配置（生产环境推荐）

```python
import logging
from logging.handlers import RotatingFileHandler

# 配置日志轮转（每个文件最大 10MB，保留 5 个备份）
handler = RotatingFileHandler(
    'sql.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

logger = logging.getLogger('Base.Repository.base.baseConnection')
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
```

## 常见问题

### Q1: 为什么看不到 SQL 日志？
A: 请确保日志级别设置为 DEBUG 或更低：
```python
logging.basicConfig(level=logging.DEBUG)
```

### Q2: 如何关闭 SQL 日志？
A: 将日志级别设置为 INFO 或更高：
```python
logging.getLogger('Base.Repository.base.baseConnection').setLevel(logging.WARNING)
```

### Q3: 如何只记录错误？
A:
```python
logging.getLogger('Base.Repository.base.baseConnection').setLevel(logging.ERROR)
```

## 测试示例

运行测试示例查看日志效果：
```bash
python Base/Repository/examples/test_sql_logging.py
```
