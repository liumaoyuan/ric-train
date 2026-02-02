"""
SQL 执行日志演示示例
展示如何启用和使用 SQL 日志记录功能
"""

import logging
from Base.Repository.connections.mysqlConnection import MySQLConnection
from Base.Config.setting import settings

# 配置日志级别和格式
logging.basicConfig(
    level=logging.DEBUG,  # 设置为 DEBUG 级别以查看 SQL 日志
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 或者只查看 SQL 相关的日志
# logging.getLogger('Base.Repository.base.baseConnection').setLevel(logging.DEBUG)


def demonstrate_sql_logging():
    """演示 SQL 日志功能"""

    # 创建数据库连接
    db = MySQLConnection(
        host=settings.mysql.host,
        user=settings.mysql.user,
        password=settings.mysql.password,
        database="test_sql_logging",
        port=3306,
        charset="utf8mb4",
        mincached=0,
        maxcached=0,
        maxconnections=1
    )

    # 示例 1: 创建表（无参数）
    print("\n=== 示例 1: 创建表 ===")
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            age INT,
            email VARCHAR(200)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # 示例 2: 插入数据（带参数）
    print("\n=== 示例 2: 插入数据 ===")
    db.execute(
        "INSERT INTO users (name, age, email) VALUES (%s, %s, %s)",
        ("张三", 25, "zhangsan@example.com")
    )
    db.execute(
        "INSERT INTO users (name, age, email) VALUES (%s, %s, %s)",
        ("李四", 30, "lisi@example.com")
    )
    db.execute(
        "INSERT INTO users (name, age, email) VALUES (%s, %s, %s)",
        ("王五", 28, None)  # 测试 NULL 值
    )

    # 示例 3: 查询数据（带参数）
    print("\n=== 示例 3: 查询数据 ===")
    results = db.execute(
        "SELECT * FROM users WHERE age >= %s",
        (25,)
    )
    print(f"查询到 {len(results)} 条记录")

    # 示例 4: 更新数据（带参数）
    print("\n=== 示例 4: 更新数据 ===")
    affected = db.execute(
        "UPDATE users SET age = %s WHERE name = %s",
        (26, "张三")
    )
    print(f"更新了 {affected} 条记录")

    # 示例 5: 删除数据（带参数）
    print("\n=== 示例 5: 删除数据 ===")
    affected = db.execute(
        "DELETE FROM users WHERE email IS NULL"
    )
    print(f"删除了 {affected} 条记录")

    # 示例 6: 使用不同参数类型
    print("\n=== 示例 6: 使用不同参数类型 ===")
    db.execute(
        "INSERT INTO users (name, age, email) VALUES (%s, %s, %s)",
        ("测试用户", 100, "test@test.com")  # 字符串、整数
    )
    db.execute(
        "INSERT INTO users (name, age, email) VALUES (%s, %s, %s)",
        (None, 0, None)  # NULL 值
    )

    # 示例 7: 显式指定操作类型
    print("\n=== 示例 7: 显式指定操作类型 ===")
    from Base.Repository.base.baseConnection import OperationType
    db.execute(
        "SELECT COUNT(*) as count FROM users",
        operation_type=OperationType.QUERY
    )

    db.close()
    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    demonstrate_sql_logging()
