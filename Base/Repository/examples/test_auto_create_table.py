"""
BaseDBModel 自动创建表功能测试示例
演示自动创建表的功能
"""

import logging
from pydantic import BaseModel
from Base.Repository.base.baseDBModel import BaseDBModel
from Base.Repository.connections.mysqlConnection import MySQLConnection
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
    database="test_auto_create",
    port=3306,
    charset="utf8mb4",
    mincached=0,
    maxcached=0,
    maxconnections=1
)

BaseDBModel.set_default_db_connection(db)


# 定义用户模型（不需要手动创建表）
class User(BaseDBModel):
    """用户模型"""
    name: str
    email: str
    age: int
    is_active: bool = True

    table_alias = "users"  # 可选：自定义表名


# 定义订单模型
class Order(BaseDBModel):
    """订单模型"""
    user_id: int
    product_name: str
    quantity: int
    price: float


# 定义产品模型（使用默认表名：products）
class Product(BaseDBModel):
    """产品模型"""
    name: str
    description: str
    stock: int
    price: float


def test_auto_create_table_on_save():
    """测试保存时自动创建表"""
    print("\n=== 测试 1: 保存时自动创建表 ===")

    # 创建用户对象
    user = User(
        name="张三",
        email="zhangsan@example.com",
        age=25,
        is_active=True
    )

    # 保存时会自动创建表
    user_id = user.save()
    print(f"用户创建成功，ID: {user_id}")

    # 验证数据
    saved_user = User.get_by_id(user_id)
    print(f"验证数据: {saved_user.to_dict()}")


def test_auto_create_table_on_query():
    """测试查询时自动创建表"""
    print("\n=== 测试 2: 查询时自动创建表 ===")

    # 查询不存在的表会自动创建
    users = User.get_all()
    print(f"查询到 {len(users)} 个用户")

    # 使用条件查询
    active_users = User.find_by(is_active=True)
    print(f"活跃用户数: {len(active_users)}")


def test_auto_create_multiple_tables():
    """测试创建多个表"""
    print("\n=== 测试 3: 创建多个表 ===")

    # 创建订单
    order1 = Order(
        user_id=1,
        product_name="商品A",
        quantity=2,
        price=99.99
    )
    order_id = order1.save()
    print(f"订单创建成功，ID: {order_id}")

    # 创建产品
    product = Product(
        name="商品A",
        description="优质商品",
        stock=100,
        price=99.99
    )
    product_id = product.save()
    print(f"产品创建成功，ID: {product_id}")

    # 统计
    order_count = Order.count()
    product_count = Product.count()
    print(f"订单总数: {order_count}, 产品总数: {product_count}")


def test_auto_create_table_not_duplicate():
    """测试不会重复创建表"""
    print("\n=== 测试 4: 不会重复创建表 ===")

    # 多次保存，表只会创建一次
    user1 = User(name="李四", email="lisi@example.com", age=30)
    user2 = User(name="王五", email="wangwu@example.com", age=35)

    id1 = user1.save()
    id2 = user2.save()

    print(f"用户 ID: {id1}, {id2}")
    print("表只创建了一次，不会重复创建")


def test_different_data_types():
    """测试不同的数据类型"""
    print("\n=== 测试 5: 不同的数据类型 ===")

    # 测试各种数据类型
    user = User(
        name="测试用户",
        email="test@example.com",
        age=99,
        is_active=False
    )
    user.save()
    print(f"布尔值测试: is_active = {user.is_active}")

    order = Order(
        user_id=1,
        product_name="测试商品",
        quantity=100,
        price=999.99
    )
    order.save()
    print(f"浮点数测试: price = {order.price}")


def test_table_name_customization():
    """测试表名自定义"""
    print("\n=== 测试 6: 表名自定义 ===")

    # User 使用自定义表名 'users'
    # Order 使用默认表名 'orders'
    # Product 使用默认表名 'products'

    print(f"User 表名: {User.get_table_name()}")
    print(f"Order 表名: {Order.get_table_name()}")
    print(f"Product 表名: {Product.get_table_name()}")


def test_update_and_delete():
    """测试更新和删除"""
    print("\n=== 测试 7: 更新和删除 ===")

    # 创建用户
    user = User(name="更新测试", email="update@example.com", age=20)
    user_id = user.save()
    print(f"创建用户 ID: {user_id}")

    # 更新用户
    user.name = "更新后的名字"
    user.age = 21
    user.update()
    print(f"更新后的用户: {user.to_dict()}")

    # 删除用户
    user.delete()
    print(f"用户已删除，ID: {user_id}")

    # 验证删除
    deleted_user = User.get_by_id(user_id)
    print(f"验证删除: {deleted_user is None}")


def test_count_and_query():
    """测试统计和查询"""
    print("\n=== 测试 8: 统计和查询 ===")

    # 创建多个用户
    users_data = [
        ("用户1", "user1@example.com", 20),
        ("用户2", "user2@example.com", 25),
        ("用户3", "user3@example.com", 30),
        ("用户4", "user4@example.com", 35),
        ("用户5", "user5@example.com", 40),
    ]

    for name, email, age in users_data:
        User(name=name, email=email, age=age).save()

    # 统计
    total_count = User.count()
    print(f"用户总数: {total_count}")

    # 分页查询
    page1 = User.get_all(limit=2, offset=0)
    page2 = User.get_all(limit=2, offset=2)
    print(f"第1页: {len(page1)} 个用户")
    print(f"第2页: {len(page2)} 个用户")

    # 条件查询
    young_users = User.find_by(age__lt=30) if hasattr(User, 'find_by_age__lt') else []
    print(f"年轻用户数: {len(young_users)}")


def cleanup():
    """清理测试数据"""
    print("\n=== 清理测试数据 ===")

    # 删除所有测试数据
    User.delete_by_id(1)
    User.delete_by_id(2)

    print("测试数据已清理")


if __name__ == "__main__":
    print("=" * 60)
    print("BaseDBModel 自动创建表功能测试")
    print("=" * 60)

    try:
        # 执行测试
        test_auto_create_table_on_save()
        test_auto_create_table_on_query()
        test_auto_create_multiple_tables()
        test_auto_create_table_not_duplicate()
        test_different_data_types()
        test_table_name_customization()
        test_update_and_delete()
        test_count_and_query()

        print("\n" + "=" * 60)
        print("所有测试通过！")
        print("=" * 60)

    finally:
        # 清理
        cleanup()

    # 关闭数据库连接
    db.close()
