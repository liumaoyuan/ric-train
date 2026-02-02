# BaseDBModel 自动创建表功能

## 功能概述

BaseDBModel 支持在第一次使用模型时自动创建数据库表，无需手动执行建表语句。

## 特性

1. **自动检测表是否存在**
   - 在执行 CRUD 操作前自动检查
   - 如果表不存在则自动创建

2. **智能类型映射**
   - 根据 Python 类型自动映射到数据库类型
   - 支持 MySQL、PostgreSQL、SQLite

3. **避免重复创建**
   - 使用标志位记录已检查的表
   - 每个类只检查一次，避免重复

4. **自动推断表结构**
   - 从 Pydantic 模型字段自动推断
   - 支持自定义表名

## 支持的数据库类型

### MySQL 类型映射

| Python 类型 | MySQL 类型 |
|------------|-------------|
| int | INT |
| str | VARCHAR(255) |
| float | DECIMAL(10,2) |
| bool | TINYINT(1) |
| datetime | DATETIME |
| date | DATE |
| decimal.Decimal | DECIMAL(10,2) |

### PostgreSQL 类型映射

| Python 类型 | PostgreSQL 类型 |
|------------|----------------|
| int | INTEGER |
| str | VARCHAR(255) |
| float | NUMERIC(10,2) |
| bool | BOOLEAN |
| datetime | TIMESTAMP |
| date | DATE |
| decimal.Decimal | NUMERIC(10,2) |

### SQLite 类型映射

| Python 类型 | SQLite 类型 |
|------------|-------------|
| int | INTEGER |
| str | TEXT |
| float | REAL |
| bool | INTEGER |
| datetime | TEXT |
| date | TEXT |
| decimal.Decimal | REAL |

## 使用方法

### 基本用法

```python
from pydantic import BaseModel
from Base.Repository.base.baseDBModel import BaseDBModel
from Base.Repository.connections.mysqlConnection import MySQLConnection

# 1. 设置数据库连接
db = MySQLConnection(
    host="localhost",
    user="root",
    password="password",
    database="my_database"
)
BaseDBModel.set_default_db_connection(db)

# 2. 定义模型（不需要手动创建表）
class User(BaseDBModel):
    """用户模型"""
    name: str
    email: str
    age: int
    is_active: bool = True

# 3. 直接使用模型 - 表会自动创建
user = User(
    name="张三",
    email="zhangsan@example.com",
    age=25,
    is_active=True
)
user_id = user.save()  # 自动创建 users 表并插入数据
```

### 自定义表名

```python
class User(BaseDBModel):
    """用户模型"""
    name: str
    email: str

    table_alias = "my_users"  # 自定义表名
```

### 多个模型

```python
class User(BaseDBModel):
    name: str
    email: str

class Order(BaseDBModel):
    user_id: int
    product: str
    price: float

class Product(BaseDBModel):
    name: str
    description: str
    stock: int

# 第一次使用时，所有表的自动创建
User(name="张三", email="test@example.com").save()
Order(user_id=1, product="商品A", price=99.99).save()
Product(name="商品A", description="优质商品", stock=100).save()
```

## 自动创建表的时机

### 1. 在保存时创建（save）

```python
# 第一次保存时，如果表不存在则自动创建
user = User(name="张三", email="test@example.com")
user_id = user.save()  # 自动创建表
```

### 2. 在查询时创建（get_by_id, get_all, find_by）

```python
# 第一次查询时，如果表不存在则自动创建
users = User.get_all()  # 自动创建表
user = User.get_by_id(1)  # 自动创建表
users = User.find_by(name="张三")  # 自动创建表
```

### 3. 在删除时创建（delete, delete_by_id）

```python
# 第一次删除时，如果表不存在则自动创建
User.delete_by_id(1)  # 自动创建表
user.delete()  # 自动创建表
```

### 4. 在统计时创建（count）

```python
# 第一次统计时，如果表不存在则自动创建
count = User.count()  # 自动创建表
```

## 生成的表结构示例

### MySQL 表结构

```sql
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `age` INT NOT NULL,
    `is_active` TINYINT(1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### PostgreSQL 表结构

```sql
CREATE TABLE IF NOT EXISTS "users" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "email" VARCHAR(255) NOT NULL,
    "age" INTEGER NOT NULL,
    "is_active" BOOLEAN
);
```

### SQLite 表结构

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    age INTEGER NOT NULL,
    is_active INTEGER
);
```

## 字段类型处理

### Optional 字段

```python
from typing import Optional

class User(BaseDBModel):
    name: str  # 必填，NOT NULL
    email: Optional[str]  # 可选，允许 NULL
    age: Optional[int] = None  # 可选，默认值
```

生成的 SQL（MySQL）：
```sql
`name` VARCHAR(255) NOT NULL,
`email` VARCHAR(255),
`age` INT
```

### 布尔类型

```python
class User(BaseDBModel):
    is_active: bool = True
```

生成的 SQL：
- MySQL: `is_active` TINYINT(1)
- PostgreSQL: `is_active` BOOLEAN
- SQLite: `is_active` INTEGER

### 数字类型

```python
class Product(BaseDBModel):
    price: float  # DECIMAL(10,2)
    quantity: int  # INT
```

### 日期时间类型

```python
from datetime import datetime, date

class Order(BaseDBModel):
    created_at: datetime  # DATETIME/TIMESTAMP
    delivery_date: date  # DATE
```

## 禁用自动创建

如果需要禁用自动创建表功能：

```python
# 方式1：在调用时禁用
user = User(name="张三", email="test@example.com")
user._ensure_table_exists(auto_create=False)
user.save()

# 方式2：手动创建表
custom_sql = "CREATE TABLE users (...)"
User.create_table(custom_sql)

# 方式3：在代码中注释掉调用
# class BaseDBModel(BaseModel, ABC):
#     def get_by_id(cls, id_val: int) -> Optional[T]:
#         # cls._ensure_table_exists()  # 注释掉
#         ...
```

## 注意事项

### 1. 字段限制

- 自动创建表时，所有字段都会有数据库类型
- 不支持复杂类型（如 list, dict），会映射为 TEXT
- 如需使用复杂类型，请手动创建表

### 2. 索引和约束

- 自动创建表时不会添加索引（除了主键）
- 如需添加索引，请在创建后手动执行
- 不支持外键约束

### 3. 表结构修改

- 自动创建表只创建表，不会修改已存在的表
- 如需修改表结构（增加/修改字段），请手动执行 ALTER TABLE
- 不会自动检测字段变化

### 4. 性能考虑

- 首次使用时会检查表是否存在，有轻微性能开销
- 使用标志位缓存检查结果，后续使用无性能损失
- 生产环境建议提前创建表，避免运行时创建

### 5. 多线程/多进程

- 标志位使用类变量，在单个进程内有效
- 多进程环境下，每个进程都会检查一次表是否存在
- 多线程环境下，第一次检查可能有并发，但使用了 CREATE TABLE IF NOT EXISTS，安全

## 完整示例

```python
import logging
from pydantic import BaseModel
from Base.Repository.base.baseDBModel import BaseDBModel
from Base.Repository.connections.mysqlConnection import MySQLConnection

# 配置日志
logging.basicConfig(level=logging.INFO)

# 设置数据库连接
db = MySQLConnection(
    host="localhost",
    user="root",
    password="password",
    database="my_app"
)
BaseDBModel.set_default_db_connection(db)

# 定义模型
class User(BaseDBModel):
    """用户模型"""
    name: str
    email: str
    age: int
    is_active: bool = True

# 创建用户（表自动创建）
user1 = User(name="张三", email="zhangsan@example.com", age=25, is_active=True)
user_id = user1.save()
print(f"创建用户 ID: {user_id}")

# 查询用户
user = User.get_by_id(user_id)
print(f"用户信息: {user.to_dict()}")

# 更新用户
user.name = "李四"
user.age = 26
user.update()
print(f"更新后的用户: {user.to_dict()}")

# 删除用户
user.delete()
print("用户已删除")

# 创建更多用户
User(name="用户1", email="user1@example.com", age=20).save()
User(name="用户2", email="user2@example.com", age=25).save()
User(name="用户3", email="user3@example.com", age=30).save()

# 统计
count = User.count()
print(f"用户总数: {count}")

# 查询所有
all_users = User.get_all()
print(f"所有用户: {[u.name for u in all_users]}")

# 条件查询
young_users = User.find_by(age__lt=25) if hasattr(User, 'find_by_age__lt') else []
print(f"年轻用户: {[u.name for u in young_users]}")

db.close()
```

## 测试示例

运行测试示例查看自动创建表功能：

```bash
python Base/Repository/examples/test_auto_create_table.py
```

## 常见问题

### Q1: 如何修改已创建的表结构？

A: 自动创建表不会修改已存在的表。如需修改，请手动执行 ALTER TABLE：

```python
# 手动修改表结构
db.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(20)")
```

### Q2: 如何添加索引？

A: 手动执行 CREATE INDEX：

```python
db.execute("CREATE INDEX idx_email ON users(email)")
```

### Q3: 如何禁用自动创建？

A: 参见"禁用自动创建"章节。

### Q4: 如何查看生成的建表 SQL？

A: 可以调用 `_generate_create_table_sql()` 方法：

```python
sql = User._generate_create_table_sql()
print(sql)
```

### Q5: 支持哪些数据库？

A: 目前支持 MySQL、PostgreSQL、SQLite。

### Q6: 如何处理复杂的表结构？

A: 对于复杂的表结构（如外键、联合索引等），建议手动创建表：

```python
custom_sql = """
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    product_id INT,
    quantity INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    INDEX idx_user_id (user_id),
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""
Order.create_table(custom_sql)
```
