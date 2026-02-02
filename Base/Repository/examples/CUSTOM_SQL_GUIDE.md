# BaseDBModel 自定义建表SQL使用指南

## 功能概述

BaseDBModel 支持两种建表方式：
1. **自动生成**（默认）：根据 Pydantic 模型字段自动生成建表SQL
2. **手动声明**（推荐）：通过 `create_table_sql` 类变量手动指定建表SQL

## 何时使用自定义建表SQL

### 推荐使用自定义SQL的场景

✅ 需要添加索引（INDEX）  
✅ 需要设置默认值（DEFAULT）  
✅ 需要添加外键约束（FOREIGN KEY）  
✅ 需要添加唯一约束（UNIQUE）  
✅ 需要添加检查约束（CHECK）  
✅ 需要指定字段长度（如 VARCHAR(200)）  
✅ 需要使用特殊的数据库特性  
✅ 表结构较复杂

### 可以使用自动生成的场景

✅ 简单的CRUD表  
✅ 字段类型简单  
✅ 不需要索引和约束  
✅ 快速原型开发

## 使用方法

### 方式1：自动生成（默认）

```python
from Base.Repository.base.baseDBModel import BaseDBModel

class User(BaseDBModel):
    """用户模型"""
    name: str
    email: str
    age: int
    is_active: bool = True

# 查看生成的SQL
sql = User.get_create_table_sql()
print(sql)

# 生成的SQL（MySQL）:
# CREATE TABLE IF NOT EXISTS `users` (
#     `id` INT AUTO_INCREMENT PRIMARY KEY,
#     `name` VARCHAR(255) NOT NULL,
#     `email` VARCHAR(255) NOT NULL,
#     `age` INT NOT NULL,
#     `is_active` TINYINT(1)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

### 方式2：手动声明（推荐）

```python
from Base.Repository.base.baseDBModel import BaseDBModel

class User(BaseDBModel):
    """用户模型"""
    name: str
    email: str
    age: int
    is_active: bool = True

    # 自定义建表SQL
    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(200) NOT NULL UNIQUE,
            age INT NOT NULL,
            is_active TINYINT(1) DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_email (email),
            INDEX idx_age (age)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    '''

# 查看自定义SQL
sql = User.get_create_table_sql()
print(sql)

# 保存时会使用自定义SQL
user = User(name="张三", email="zhangsan@example.com", age=25, is_active=True)
user_id = user.save()  # 使用 create_table_sql 创建表
```

## 优先级规则

当同时存在 `create_table_sql` 和自动生成时：

1. **优先使用自定义SQL**：如果定义了 `create_table_sql`，则使用它
2. **自动生成**：如果没有定义 `create_table_sql`，则自动生成

```python
class User(BaseDBModel):
    name: str
    email: str

    # 如果定义了 create_table_sql，优先使用它
    create_table_sql = "CREATE TABLE users (...)"

    # 即使有字段定义，也会使用自定义SQL
```

## 自定义建表SQL示例

### 示例1：带索引

```python
class Product(BaseDBModel):
    name: str
    description: str
    price: float
    stock: int

    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            price DECIMAL(10,2) NOT NULL,
            stock INT NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_name (name),
            INDEX idx_price (price),
            INDEX idx_stock (stock)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    '''
```

### 示例2：带外键

```python
class Customer(BaseDBModel):
    name: str
    email: str

    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS customers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(200) NOT NULL UNIQUE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    '''

class Order(BaseDBModel):
    customer_id: int
    product_name: str
    quantity: int

    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            product_name VARCHAR(200) NOT NULL,
            quantity INT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    '''
```

### 示例3：带唯一约束

```python
class User(BaseDBModel):
    username: str
    email: str
    phone: str

    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(200) NOT NULL UNIQUE,
            phone VARCHAR(20),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    '''
```

### 示例4：带检查约束

```python
class Article(BaseDBModel):
    title: str
    content: str
    status: str

    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS articles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            content LONGTEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'draft',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT chk_status CHECK (status IN ('draft', 'published', 'archived'))
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    '''
```

### 示例5：复合唯一索引

```python
class Subscription(BaseDBModel):
    user_id: int
    plan_id: int
    start_date: datetime

    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            plan_id INT NOT NULL,
            start_date DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_user_plan (user_id, plan_id),
            INDEX idx_user_id (user_id),
            INDEX idx_plan_id (plan_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    '''
```

### 示例6：从外部文件读取

```python
# 从外部文件读取建表SQL
def read_sql_from_file(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# 使用外部SQL
class ExternalModel(BaseDBModel):
    field1: str
    field2: int

    create_table_sql = read_sql_from_file('external_model.sql')

# 或者从配置文件读取
CREATE_TABLE_SQL_CONFIG = {
    'user': 'CREATE TABLE users (...)',
    'order': 'CREATE TABLE orders (...)',
}

class User(BaseDBModel):
    name: str
    email: str

    create_table_sql = CREATE_TABLE_SQL_CONFIG['user']
```

## 获取建表SQL

### 查看最终使用的SQL

```python
# 获取最终使用的建表SQL（自定义或自动生成）
sql = User.get_create_table_sql()
print(sql)
```

### 在创建前查看SQL

```python
# 查看建表SQL（不会创建表）
sql = User.get_create_table_sql()
print("将使用的建表SQL:")
print(sql)

# 确认后再创建
# user = User(name="张三", email="test@example.com")
# user.save()
```

## 不同数据库的SQL

### MySQL

```python
class User(BaseDBModel):
    name: str
    email: str

    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(200) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    '''
```

### PostgreSQL

```python
class User(BaseDBModel):
    name: str
    email: str

    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(200) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
```

### SQLite

```python
class User(BaseDBModel):
    name: str
    email: str

    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    '''
```

## 最佳实践

### 1. 自定义SQL格式化

```python
class User(BaseDBModel):
    name: str
    email: str

    # 推荐使用三引号字符串，保留格式
    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(200) NOT NULL UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    '''
```

### 2. 添加时间戳字段

```python
class BaseModelWithTimestamps(BaseDBModel):
    """带时间戳的基类"""
    created_at: datetime = None
    updated_at: datetime = None

    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            {fields},
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    '''
```

### 3. 使用表别名和自定义SQL

```python
class UserProfile(BaseDBModel):
    nickname: str
    avatar: str

    table_alias = "user_profiles"  # 自定义表名

    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nickname VARCHAR(50) NOT NULL,
            avatar VARCHAR(500),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    '''
```

### 4. 版本化表结构

```python
class UserV1(BaseDBModel):
    """用户模型 V1"""
    name: str
    email: str

    table_alias = "users_v1"
    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS users_v1 (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(200) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    '''

class UserV2(BaseDBModel):
    """用户模型 V2（增加字段）"""
    name: str
    email: str
    phone: str  # 新增字段

    table_alias = "users_v2"
    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS users_v2 (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(200) NOT NULL,
            phone VARCHAR(20)  -- 新增字段
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    '''
```

## 常见问题

### Q1: 可以同时使用自定义SQL和自动生成吗？

A: 不可以。如果定义了 `create_table_sql`，会优先使用它，忽略自动生成的SQL。

### Q2: 如何查看自动生成的SQL？

A: 使用 `get_create_table_sql()` 方法：
```python
sql = User.get_create_table_sql()
print(sql)
```

### Q3: 自定义SQL中的字段名需要和模型字段一致吗？

A: 不需要。自定义SQL可以完全独立于模型字段定义。但建议保持一致以避免混淆。

### Q4: 修改 `create_table_sql` 后如何重建表？

A: 需要手动删除旧表后重新创建：
```python
db.execute("DROP TABLE IF EXISTS users")
user = User(name="张三", email="test@example.com")
user.save()  # 使用新的 create_table_sql 创建表
```

### Q5: 如何在生产环境中控制建表行为？

A: 建议提前执行建表SQL，不在运行时创建：
```python
# 部署脚本
if not User.table_exists():
    db.execute(User.get_create_table_sql())
```

### Q6: 自定义SQL支持占位符吗？

A: 不支持。`create_table_sql` 是完整的SQL语句，不应包含占位符。

### Q7: 如何在自定义SQL中使用当前表名？

A: 使用硬编码的表名或通过 `table_alias` 指定：
```python
class User(BaseDBModel):
    name: str
    email: str

    table_alias = "my_users"  # 明确指定表名

    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS my_users (...)
    '''
```

## 完整示例

```python
from datetime import datetime
from Base.Repository.base.baseDBModel import BaseDBModel
from Base.Repository.connections.mysqlConnection import MySQLConnection

# 设置数据库连接
db = MySQLConnection(...)
BaseDBModel.set_default_db_connection(db)

# 定义模型（使用自定义建表SQL）
class User(BaseDBModel):
    """用户模型"""
    username: str
    email: str
    password_hash: str
    is_active: bool = True

    table_alias = "users"

    # 自定义建表SQL
    create_table_sql = '''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(200) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            is_active TINYINT(1) DEFAULT 1,
            last_login DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_username (username),
            INDEX idx_email (email),
            INDEX idx_is_active (is_active),
            INDEX idx_last_login (last_login)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    '''

# 查看建表SQL
print("将使用的建表SQL:")
print(User.get_create_table_sql())

# 创建用户（表会自动创建）
user = User(
    username="zhangsan",
    email="zhangsan@example.com",
    password_hash="hashed_password_here",
    is_active=True
)
user_id = user.save()
print(f"用户创建成功，ID: {user_id}")

# 查询用户
saved_user = User.get_by_id(user_id)
print(f"用户信息: {saved_user.to_dict()}")
```

## 运行示例

查看更多示例：

```bash
python Base/Repository/examples/test_custom_create_table_sql.py
```
