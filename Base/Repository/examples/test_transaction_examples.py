"""
数据库事务使用示例
演示正确和错误的事务使用方式
"""

import logging
from Base.Repository.connections.mysqlConnection import MySQLConnection
from Base.Config.setting import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def example_wrong_no_commit():
    """❌ 错误示例：忘记提交事务"""
    print("\n=== 错误示例 1: 忘记提交事务 ===")

    db = MySQLConnection(
        host=settings.mysql.host,
        user=settings.mysql.user,
        password=settings.mysql.password,
        database="test_wrong_example",
        port=3306,
        charset="utf8mb4",
        mincached=0,
        maxcached=0,
        maxconnections=1
    )

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # ❌ 错误：没有提交事务
    with db.get_connection_context() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name) VALUES (%s)", ("Alice",))
        cur.execute("INSERT INTO users (name) VALUES (%s)", ("Bob",))
        # 退出上下文时，连接关闭，未提交的事务会被回滚！
        print("执行了插入操作，但未提交...")

    # 验证数据
    results = db.execute("SELECT * FROM users")
    print(f"实际插入的记录数: {len(results)}")  # 应该是 0！

    db.close()
    print("数据未插入（被回滚）\n")


def example_correct_manual_commit():
    """✅ 正确示例：手动提交事务"""
    print("=== 正确示例 1: 手动提交事务 ===")

    db = MySQLConnection(
        host=settings.mysql.host,
        user=settings.mysql.user,
        password=settings.mysql.password,
        database="test_correct_example",
        port=3306,
        charset="utf8mb4",
        mincached=0,
        maxcached=0,
        maxconnections=1
    )

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # ✅ 正确：手动提交事务
    with db.get_connection_context() as conn:
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO users (name) VALUES (%s)", ("Alice",))
            cur.execute("INSERT INTO users (name) VALUES (%s)", ("Bob",))
            conn.commit()  # 手动提交事务
            print("执行了插入操作并提交...")
        except Exception as e:
            conn.rollback()
            raise

    # 验证数据
    results = db.execute("SELECT * FROM users")
    print(f"实际插入的记录数: {len(results)}")  # 应该是 2
    print(f"插入的用户: {[r['name'] for r in results]}\n")

    db.close()


def example_correct_use_execute():
    """✅ 正确示例：使用 execute() 方法（自动提交）"""
    print("=== 正确示例 2: 使用 execute() 方法 ===")

    db = MySQLConnection(
        host=settings.mysql.host,
        user=settings.mysql.user,
        password=settings.mysql.password,
        database="test_execute_example",
        port=3306,
        charset="utf8mb4",
        mincached=0,
        maxcached=0,
        maxconnections=1
    )

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # ✅ 正确：使用 execute() 方法会自动提交
    db.execute("INSERT INTO users (name) VALUES (%s)", ("Alice",))
    db.execute("INSERT INTO users (name) VALUES (%s)", ("Bob",))
    db.execute("INSERT INTO users (name) VALUES (%s)", ("Charlie",))
    print("使用 execute() 插入了 3 条记录...")

    # 验证数据
    results = db.execute("SELECT * FROM users")
    print(f"实际插入的记录数: {len(results)}")  # 应该是 3
    print(f"插入的用户: {[r['name'] for r in results]}\n")

    db.close()


def example_bulk_insert():
    """✅ 正确示例：批量插入"""
    print("=== 正确示例 3: 批量插入 ===")

    db = MySQLConnection(
        host=settings.mysql.host,
        user=settings.mysql.user,
        password=settings.mysql.password,
        database="test_bulk_example",
        port=3306,
        charset="utf8mb4",
        mincached=0,
        maxcached=0,
        maxconnections=1
    )

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            age INT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # ✅ 正确：批量操作后提交
    data = [("Alice", 25), ("Bob", 30), ("Charlie", 35)]
    with db.get_connection_context() as conn:
        cur = conn.cursor()
        cur.executemany("INSERT INTO users (name, age) VALUES (%s, %s)", data)
        conn.commit()  # 手动提交事务

    print(f"批量插入了 {len(data)} 条记录...")

    # 验证数据
    results = db.execute("SELECT * FROM users")
    print(f"实际插入的记录数: {len(results)}")  # 应该是 3
    print(f"插入的用户: {[(r['name'], r['age']) for r in results]}\n")

    db.close()


def example_transaction_rollback():
    """✅ 正确示例：事务回滚"""
    print("=== 正确示例 4: 事务回滚 ===")

    db = MySQLConnection(
        host=settings.mysql.host,
        user=settings.mysql.user,
        password=settings.mysql.password,
        database="test_rollback_example",
        port=3306,
        charset="utf8mb4",
        mincached=0,
        maxcached=0,
        maxconnections=1
    )

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # 先插入一条数据
    db.execute("INSERT INTO users (name) VALUES (%s)", ("Initial User",))
    results = db.execute("SELECT * FROM users")
    initial_count = len(results)
    print(f"初始记录数: {initial_count}")

    # ✅ 正确：测试回滚
    try:
        with db.get_connection_context() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO users (name) VALUES (%s)", ("Test User",))
            raise Exception("测试回滚")  # 故意抛出异常，不提交
    except Exception:
        print("发生异常，事务已回滚...")
        pass  # 预期的异常

    # 验证数据
    results = db.execute("SELECT * FROM users")
    final_count = len(results)
    print(f"最终记录数: {final_count}")  # 应该仍然是 1
    print(f"回滚成功: {initial_count == final_count}\n")

    db.close()


def example_complex_transaction():
    """✅ 正确示例：复杂事务"""
    print("=== 正确示例 5: 复杂事务 ===")

    db = MySQLConnection(
        host=settings.mysql.host,
        user=settings.mysql.user,
        password=settings.mysql.password,
        database="test_complex_transaction",
        port=3306,
        charset="utf8mb4",
        mincached=0,
        maxcached=0,
        maxconnections=1
    )

    # 创建多个表
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            product VARCHAR(100)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product VARCHAR(100),
            quantity INT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # ✅ 正确：复杂事务，多个相关操作
    try:
        with db.get_connection_for_transaction() as conn:
            # 操作1：创建用户
            with conn.cursor() as cur:
                cur.execute("INSERT INTO users (name) VALUES (%s)", ("Alice",))
                user_id = cur.lastrowid
                print(f"创建用户 ID: {user_id}")

            # 操作2：创建订单
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO orders (user_id, product) VALUES (%s, %s)",
                    (user_id, "Product A")
                )
                print(f"创建订单")

            # 操作3：扣减库存
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO inventory (product, quantity) VALUES (%s, %s)",
                    ("Product A", 100)
                )
                print(f"更新库存")

            # 所有操作成功后提交
            conn.commit()
            print("事务已提交，所有操作成功！")

    except Exception as e:
        print(f"发生错误: {e}")
        print("事务已回滚，所有操作撤销")
        raise

    # 验证数据
    users = db.execute("SELECT * FROM users")
    orders = db.execute("SELECT * FROM orders")
    inventory = db.execute("SELECT * FROM inventory")

    print(f"\n验证结果:")
    print(f"  用户数: {len(users)}")
    print(f"  订单数: {len(orders)}")
    print(f"  库存数: {len(inventory)}\n")

    db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("数据库事务使用示例")
    print("=" * 60)

    # 错误示例
    example_wrong_no_commit()

    # 正确示例
    example_correct_manual_commit()
    example_correct_use_execute()
    example_bulk_insert()
    example_transaction_rollback()
    example_complex_transaction()

    print("=" * 60)
    print("所有示例执行完成")
    print("=" * 60)
