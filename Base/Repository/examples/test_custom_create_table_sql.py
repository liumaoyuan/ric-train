"""
BaseDBModel 自定义建表SQL示例
演示如何手动声明建表语句
"""

import logging
from datetime import datetime
from pydantic import BaseModel
from Base.Repository.base.baseDBModel import BaseDBModel
from Base.Repository.connections.mysqlConnection import MySQLConnection, get_module_mysql_connection
from Base.Config.setting import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 设置数据库连接
db = MySQLConnection(
    host=settings.mysql.host,
    user=settings.mysql.user,
    password=settings.mysql.password,
    database="test_custom_sql",
    port=3306,
    charset="utf8mb4",
    mincached=0,
    maxcached=0,
    maxconnections=1
)

BaseDBModel.set_default_db_connection(db)


def example1_auto_generate_sql():
    """示例1：使用自动生成的建表SQL"""
    print("\n=== 示例 1: 自动生成建表SQL ===")

    class User(BaseDBModel):
        """用户模型 - 自动生成建表SQL"""
        name: str
        email: str
        age: int
        is_active: bool = True

    # 查看生成的SQL
    sql = User.get_create_table_sql()
    print(f"生成的建表SQL:\n{sql}")

    # 保存用户（表会自动创建）
    user = User(name="张三", email="zhangsan@example.com", age=25, is_active=True)
    user_id = user.save()
    print(f"用户创建成功，ID: {user_id}")

    # 验证
    saved_user = User.get_by_id(user_id)
    print(f"验证: {saved_user.to_dict()}")

    # 清理
    User.delete_by_id(user_id)


def example2_custom_sql_with_indexes():
    """示例2：自定义建表SQL（带索引）"""
    print("\n=== 示例 2: 自定义建表SQL - 带索引 ===")

    class Product(BaseDBModel):
        """产品模型 - 自定义建表SQL"""
        name: str
        description: str
        price: float
        stock: int

        # 自定义建表SQL（包含索引）
        create_table_sql = '''
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                stock INT NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_name (name),
                INDEX idx_price (price),
                INDEX idx_stock (stock)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        '''

    # 查看自定义SQL
    sql = Product.get_create_table_sql()
    print(f"自定义建表SQL:\n{sql}")

    # 保存产品（使用自定义SQL创建表）
    product = Product(
        name="高性能笔记本",
        description="最新款高性能笔记本电脑，16GB内存，512GB固态硬盘",
        price=5999.99,
        stock=100
    )
    product_id = product.save()
    print(f"产品创建成功，ID: {product_id}")

    # 验证
    saved_product = Product.get_by_id(product_id)
    print(f"验证: {saved_product.to_dict()}")

    # 清理
    Product.delete_by_id(product_id)


def example3_custom_sql_with_foreign_keys():
    """示例3：自定义建表SQL（带外键）"""
    print("\n=== 示例 3: 自定义建表SQL - 带外键 ===")

    class Customer(BaseDBModel):
        """客户模型"""
        name: str
        email: str
        phone: str

        # 自定义建表SQL
        create_table_sql = '''
            CREATE TABLE IF NOT EXISTS customers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(200) NOT NULL UNIQUE,
                phone VARCHAR(20),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        '''

    class Order(BaseDBModel):
        """订单模型 - 带外键"""
        customer_id: int
        product_name: str
        quantity: int
        total_amount: float

        # 自定义建表SQL（包含外键约束）
        create_table_sql = '''
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                customer_id INT NOT NULL,
                product_name VARCHAR(200) NOT NULL,
                quantity INT NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        '''

    # 创建客户
    customer = Customer(
        name="张三",
        email="zhangsan@example.com",
        phone="13800138000"
    )
    customer_id = customer.save()
    print(f"客户创建成功，ID: {customer_id}")

    # 创建订单
    order = Order(
        customer_id=customer_id,
        product_name="高性能笔记本",
        quantity=1,
        total_amount=5999.99
    )
    order_id = order.save()
    print(f"订单创建成功，ID: {order_id}")

    # 验证
    saved_order = Order.get_by_id(order_id)
    print(f"验证订单: {saved_order.to_dict()}")

    # 清理
    Order.delete_by_id(order_id)
    Customer.delete_by_id(customer_id)


def example4_custom_sql_with_constraints():
    """示例4：自定义建表SQL（带复杂约束）"""
    print("\n=== 示例 4: 自定义建表SQL - 带复杂约束 ===")

    class Article(BaseDBModel):
        """文章模型"""
        title: str
        content: str
        author_id: int
        status: str = "draft"

        # 自定义建表SQL（多种约束）
        create_table_sql = '''
            CREATE TABLE IF NOT EXISTS articles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                content LONGTEXT,
                author_id INT NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'draft',
                view_count INT DEFAULT 0,
                published_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT chk_status CHECK (status IN ('draft', 'published', 'archived')),
                INDEX idx_status (status),
                INDEX idx_published_at (published_at),
                INDEX idx_author_id (author_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        '''

    # 查看SQL
    sql = Article.get_create_table_sql()
    print(f"自定义建表SQL:\n{sql}")

    # 创建文章
    article = Article(
        title="Python异步编程指南",
        content="这是一篇关于Python异步编程的详细指南...",
        author_id=1,
        status="published"
    )
    article_id = article.save()
    print(f"文章创建成功，ID: {article_id}")

    # 验证
    saved_article = Article.get_by_id(article_id)
    print(f"验证: 标题={saved_article.title}, 状态={saved_article.status}")

    # 清理
    Article.delete_by_id(article_id)


def example5_mixed_auto_and_custom():
    """示例5：混合使用自动生成和自定义SQL"""
    print("\n=== 示例 5: 混合使用自动生成和自定义SQL ===")

    class SimpleUser(BaseDBModel):
        """简单用户模型 - 自动生成SQL"""
        name: str
        email: str

    class ComplexOrder(BaseDBModel):
        """复杂订单模型 - 自定义SQL"""
        user_id: int
        product_name: str
        quantity: int
        total_amount: float

        # 自定义建表SQL
        create_table_sql = '''
            CREATE TABLE IF NOT EXISTS complex_orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                product_name VARCHAR(200) NOT NULL,
                quantity INT NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        '''

    # 创建用户（自动生成SQL）
    user = SimpleUser(name="张三", email="zhangsan@example.com")
    user_id = user.save()
    print(f"用户创建成功（自动生成SQL），ID: {user_id}")

    # 创建订单（自定义SQL）
    order = ComplexOrder(
        user_id=user_id,
        product_name="高性能笔记本",
        quantity=1,
        total_amount=5999.99
    )
    order_id = order.save()
    print(f"订单创建成功（自定义SQL），ID: {order_id}")

    # 清理
    ComplexOrder.delete_by_id(order_id)
    SimpleUser.delete_by_id(user_id)


def example6_get_sql_without_creating():
    """示例6：获取建表SQL但不创建表"""
    print("\n=== 示例 6: 获取建表SQL但不创建表 ===")

    class TestTable(BaseDBModel):
        """测试模型"""
        name: str
        value: int

        # 自定义建表SQL
        create_table_sql = '''
            CREATE TABLE IF NOT EXISTS test_tables (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                value INT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_name_value (name, value)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        '''

    # 获取建表SQL（不会创建表）
    sql = TestTable.get_create_table_sql()
    print("获取的建表SQL（未执行）:")
    print(sql)

    # 验证表未被创建
    print(f"表是否存在: {TestTable.table_exists()}")


def example7_different_table_names():
    """示例7：不同的表名设置"""
    print("\n=== 示例 7: 不同的表名设置 ===")

    class UserProfile(BaseDBModel):
        """用户资料模型"""
        nickname: str
        avatar: str
        bio: str

        # 自定义表名
        table_alias = "user_profiles"

        # 自定义建表SQL
        create_table_sql = '''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nickname VARCHAR(50) NOT NULL,
                avatar VARCHAR(500),
                bio TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        '''

    class UserSettings(BaseDBModel):
        """用户设置模型"""
        theme: str = "light"
        language: str = "zh-CN"
        notifications_enabled: bool = True

        # 使用默认表名（user_settings）

    # 查看表名
    print(f"UserProfile 表名: {UserProfile.get_table_name()}")
    print(f"UserSettings 表名: {UserSettings.get_table_name()}")

    # 查看建表SQL
    print("\nUserProfile 建表SQL:")
    print(UserProfile.get_create_table_sql())

    print("\nUserSettings 建表SQL（自动生成）:")
    print(UserSettings.get_create_table_sql())


def example8_predefined_sql():
    """示例8：从外部文件或变量读取建表SQL"""
    print("\n=== 示例 8: 从外部读取建表SQL ===")

    # 从外部定义的SQL（可以从文件读取）
    PREDEFINED_USER_TABLE_SQL = '''
        CREATE TABLE IF NOT EXISTS external_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(200) NOT NULL UNIQUE,
            last_login DATETIME,
            is_active TINYINT(1) DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_username (username),
            INDEX idx_email (email),
            INDEX idx_last_login (last_login)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    '''

    class ExternalUser(BaseDBModel):
        """外部用户模型"""
        username: str
        password_hash: str
        email: str
        is_active: bool = True

        # 使用外部定义的SQL
        create_table_sql = PREDEFINED_USER_TABLE_SQL

    # 查看建表SQL
    print("外部定义的建表SQL:")
    print(ExternalUser.get_create_table_sql())

    # 创建用户
    user = ExternalUser(
        username="testuser",
        password_hash="hashed_password_here",
        email="testuser@example.com",
        is_active=True
    )
    user_id = user.save()
    print(f"用户创建成功，ID: {user_id}")

    # 清理
    ExternalUser.delete_by_id(user_id)


def cleanup():
    """清理测试表"""
    print("\n=== 清理测试数据 ===")

    try:
        # 清理所有测试表
        db.execute("DROP TABLE IF EXISTS users")
        db.execute("DROP TABLE IF EXISTS products")
        db.execute("DROP TABLE IF EXISTS customers")
        db.execute("DROP TABLE IF EXISTS orders")
        db.execute("DROP TABLE IF EXISTS articles")
        db.execute("DROP TABLE IF EXISTS complex_orders")
        db.execute("DROP TABLE IF EXISTS test_tables")
        db.execute("DROP TABLE IF EXISTS user_profiles")
        db.execute("DROP TABLE IF EXISTS user_settings")
        db.execute("DROP TABLE IF EXISTS external_users")

        print("测试表已清理")
    except Exception as e:
        print(f"清理时出错: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("BaseDBModel 自定义建表SQL示例")
    print("=" * 60)

    try:
        # 执行示例
        example1_auto_generate_sql()
        example2_custom_sql_with_indexes()
        example3_custom_sql_with_foreign_keys()
        example4_custom_sql_with_constraints()
        example5_mixed_auto_and_custom()
        example6_get_sql_without_creating()
        example7_different_table_names()
        example8_predefined_sql()

        print("\n" + "=" * 60)
        print("所有示例执行完成！")
        print("=" * 60)

    finally:
        # 清理
        cleanup()

    # 关闭数据库连接
    db.close()
