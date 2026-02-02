"""
BaseDBModel 测试
测试 ORM 模型功能
"""

import pytest
from Base.Repository.base.baseDBModel import BaseDBModel
from Base.Repository.connections.sqliteConnection import SQLiteConnection
from typing import Optional, ClassVar
from abc import ABC


@pytest.fixture
def test_db():
    """创建测试数据库"""
    db = SQLiteConnection(database=":memory:")
    yield db
    db.close()


@pytest.fixture
def test_db_with_tables(test_db):
    """创建包含测试表的数据库"""
    # 创建 users 表
    test_db.execute_update("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            age INTEGER
        )
    """)

    # 创建 products 表
    test_db.execute_update("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL,
            stock INTEGER DEFAULT 0
        )
    """)

    return test_db


@pytest.fixture
def user_model(test_db_with_tables):
    """创建用户模型并设置连接"""
    class User(BaseDBModel):
        table_alias: ClassVar[str] = "users"
        id: Optional[int] = None
        name: str
        email: str
        age: Optional[int] = None

    User.set_db_connection(test_db_with_tables)
    return User


@pytest.fixture
def product_model(test_db_with_tables):
    """创建商品模型并设置连接"""
    class Product(BaseDBModel):
        table_alias: ClassVar[str] = "products"
        id: Optional[int] = None
        name: str
        price: float
        stock: int = 0

    Product.set_db_connection(test_db_with_tables)
    return Product


def test_base_db_model_inherits_abc():
    """测试 BaseDBModel 继承 ABC"""
    assert issubclass(BaseDBModel, ABC)


def test_base_db_model_has_id_field():
    """测试模型必须包含 id 字段"""
    class ValidModel(BaseDBModel):
        id: Optional[int] = None
        name: str

    assert "id" in ValidModel.model_fields

    # 缺少 id 字段会触发警告
    class InvalidModel(BaseDBModel):
        name: str  # 缺少 id 字段


def test_base_db_model_table_alias(user_model):
    """测试表别名"""
    assert user_model.get_table_name() == "users"


def test_base_db_model_auto_table_name():
    """测试自动生成表名"""
    class UserProfile(BaseDBModel):
        id: Optional[int] = None
        name: str

    # UserProfile → user_profile
    assert UserProfile.get_table_name() == "user_profile"


def test_base_db_model_save_insert(user_model):
    """测试保存（插入）"""
    user = user_model(name="Alice", email="alice@example.com", age=25)
    user_id = user.save()

    assert user_id is not None
    assert user.id == user_id
    assert isinstance(user_id, int)


def test_base_db_model_get_by_id(user_model):
    """测试根据 ID 查询"""
    # 先插入数据
    user = user_model(name="Bob", email="bob@example.com", age=30)
    user.save()

    # 根据 ID 查询
    found_user = user_model.get_by_id(user.id)
    assert found_user is not None
    assert found_user.name == "Bob"
    assert found_user.email == "bob@example.com"
    assert found_user.age == 30


def test_base_db_model_get_by_id_not_found(user_model):
    """测试查询不存在的 ID"""
    user = user_model.get_by_id(999999)
    assert user is None


def test_base_db_model_update(user_model):
    """测试更新记录"""
    # 先插入
    user = user_model(name="Charlie", email="charlie@example.com", age=35)
    user.save()

    # 更新
    user.age = 36
    user.update()

    # 验证更新
    updated_user = user_model.get_by_id(user.id)
    assert updated_user.age == 36
    assert updated_user.name == "Charlie"


def test_base_db_model_update_fields(user_model):
    """测试更新指定字段"""
    user = user_model(name="David", email="david@example.com", age=40)
    user.save()

    # 使用 update 方法更新多个字段
    user.update(age=41, email="david_new@example.com")

    updated_user = user_model.get_by_id(user.id)
    assert updated_user.age == 41
    assert updated_user.email == "david_new@example.com"
    assert updated_user.name == "David"  # 未更新


def test_base_db_model_delete(user_model):
    """测试删除记录"""
    user = user_model(name="Eve", email="eve@example.com", age=28)
    user.save()
    user_id = user.id

    # 删除
    result = user.delete()
    assert result is True

    # 验证删除
    deleted_user = user_model.get_by_id(user_id)
    assert deleted_user is None


def test_base_db_model_delete_by_id(user_model):
    """测试根据 ID 删除"""
    user = user_model(name="Frank", email="frank@example.com", age=32)
    user.save()
    user_id = user.id

    # 根据 ID 删除
    result = user_model.delete_by_id(user_id)
    assert result is True

    # 验证删除
    deleted_user = user_model.get_by_id(user_id)
    assert deleted_user is None


def test_base_db_model_find_by(user_model):
    """测试条件查询"""
    # 插入多条数据
    user_model(name="Alice", email="alice1@example.com", age=25).save()
    user_model(name="Alice", email="alice2@example.com", age=30).save()
    user_model(name="Bob", email="bob@example.com", age=25).save()

    # 查询所有 name=Alice 的用户
    users = user_model.find_by(name="Alice")
    assert len(users) == 2

    # 查询 age=25 的用户
    users = user_model.find_by(age=25)
    assert len(users) == 2

    # 多条件查询
    users = user_model.find_by(name="Alice", age=30)
    assert len(users) == 1
    assert users[0].email == "alice2@example.com"


def test_base_db_model_find_by_no_results(user_model):
    """测试条件查询无结果"""
    users = user_model.find_by(name="Nonexistent")
    assert users == []


def test_base_db_model_find_one_by(user_model):
    """测试查询单条记录"""
    user_model(name="Grace", email="grace@example.com", age=27).save()

    user = user_model.find_one_by(email="grace@example.com")
    assert user is not None
    assert user.name == "Grace"
    assert user.age == 27


def test_base_db_model_find_one_by_multiple_results(user_model):
    """测试查询单条记录（有多条结果时返回第一条）"""
    user_model(name="Henry", email="henry1@example.com", age=22).save()
    user_model(name="Henry", email="henry2@example.com", age=23).save()

    user = user_model.find_one_by(name="Henry")
    assert user is not None
    assert user.name == "Henry"


def test_base_db_model_find_one_by_no_results(user_model):
    """测试查询单条记录（无结果）"""
    user = user_model.find_one_by(email="nonexistent@example.com")
    assert user is None


def test_base_db_model_get_all(user_model):
    """测试查询所有记录"""
    # 插入多条数据
    user_model(name="Alice", email="alice@example.com", age=25).save()
    user_model(name="Bob", email="bob@example.com", age=30).save()
    user_model(name="Charlie", email="charlie@example.com", age=35).save()

    users = user_model.get_all()
    assert len(users) == 3
    assert all(isinstance(u, user_model) for u in users)


def test_base_db_model_get_all_empty(user_model):
    """测试查询所有记录（空）"""
    users = user_model.get_all()
    assert users == []


def test_base_db_model_get_all_with_limit(user_model):
    """测试分页查询"""
    # 插入 5 条数据
    for i in range(5):
        user_model(name=f"User{i}", email=f"user{i}@example.com", age=20 + i).save()

    # 查询前 3 条
    users = user_model.get_all(limit=3)
    assert len(users) == 3

    # 查询第 2-4 条（offset=1, limit=3）
    users = user_model.get_all(limit=3, offset=1)
    assert len(users) == 3


def test_base_db_model_count(user_model):
    """测试统计数量"""
    assert user_model.count() == 0

    # 插入 3 条数据
    for i in range(3):
        user_model(name=f"User{i}", email=f"user{i}@example.com", age=20 + i).save()

    assert user_model.count() == 3


def test_base_db_model_to_dict(user_model):
    """测试转换为字典"""
    user = user_model(id=1, name="Test", email="test@example.com", age=25)

    result = user.to_dict()
    assert isinstance(result, dict)
    assert result["id"] == 1
    assert result["name"] == "Test"
    assert result["email"] == "test@example.com"
    assert result["age"] == 25


def test_base_db_model_table_exists(user_model):
    """测试检查表是否存在"""
    assert user_model.table_exists() is True

    class NonExistentModel(BaseDBModel):
        table_alias: ClassVar[str] = "non_existent_table"
        id: Optional[int] = None
        name: str

    NonExistentModel.set_db_connection(user_model.get_db_connection())
    assert NonExistentModel.table_exists() is False


def test_base_db_model_set_db_connection(user_model):
    """测试设置类级别连接"""
    db = SQLiteConnection(database=":memory:")
    db.execute_update("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")

    class TestModel(BaseDBModel):
        table_alias: ClassVar[str] = "test"
        id: Optional[int] = None
        name: str

    TestModel.set_db_connection(db)

    model = TestModel(name="Test")
    model_id = model.save()
    assert model_id is not None

    db.close()


def test_base_db_model_set_default_db_connection(test_db):
    """测试设置全局默认连接"""
    # 清理之前的设置
    BaseDBModel._default_db_connection = None

    test_db.execute_update("CREATE TABLE global_test (id INTEGER PRIMARY KEY, value TEXT)")

    class GlobalModel(BaseDBModel):
        table_alias: ClassVar[str] = "global_test"
        id: Optional[int] = None
        value: str

    # 设置全局默认连接
    BaseDBModel.set_default_db_connection(test_db)

    model = GlobalModel(value="test")
    model_id = model.save()
    assert model_id is not None


def test_base_db_model_connection_priority(test_db):
    """测试连接优先级（实例 > 类 > 全局）"""
    test_db.execute_update("CREATE TABLE priority_test (id INTEGER PRIMARY KEY, value TEXT)")

    class PriorityModel(BaseDBModel):
        table_alias: ClassVar[str] = "priority_test"
        id: Optional[int] = None
        value: str

    # 设置全局默认连接
    BaseDBModel._default_db_connection = test_db

    # 创建第二个数据库
    db2 = SQLiteConnection(database=":memory:")
    db2.execute_update("CREATE TABLE priority_test (id INTEGER PRIMARY KEY, value TEXT)")

    # 设置类级别连接（应该覆盖全局）
    PriorityModel.set_db_connection(db2)

    # 创建实例并设置实例级别连接（优先级最高）
    model = PriorityModel(value="test")
    model._instance_db_connection = test_db

    # 验证连接优先级
    assert model.get_connection() == test_db

    db2.close()


def test_base_db_model_save_update_or_insert(user_model):
    """测试 save 自动判断插入或更新"""
    # 无 ID 时插入
    user1 = user_model(name="InsertTest", email="insert@example.com", age=25)
    user_id = user1.save()
    assert user_id is not None
    assert user1.id == user_id

    # 有 ID 时更新
    user1.age = 26
    new_id = user1.save()
    assert new_id == user_id  # ID 不变

    # 验证更新
    updated = user_model.get_by_id(user_id)
    assert updated.age == 26


def test_base_db_model_with_product_model(product_model):
    """测试商品模型"""
    product = product_model(name="Laptop", price=999.99, stock=10)
    product_id = product.save()

    assert product_id is not None
    assert product.id == product_id

    # 查询验证
    found = product_model.get_by_id(product_id)
    assert found.name == "Laptop"
    assert found.price == 999.99
    assert found.stock == 10


def test_base_db_model_multiple_models(test_db_with_tables):
    """测试多个模型使用同一连接"""
    class User(BaseDBModel):
        table_alias: ClassVar[str] = "users"
        id: Optional[int] = None
        name: str

    class Product(BaseDBModel):
        table_alias: ClassVar[str] = "products"
        id: Optional[int] = None
        name: str

    # 两个模型使用同一个连接
    User.set_db_connection(test_db_with_tables)
    Product.set_db_connection(test_db_with_tables)

    # 插入数据
    user = User(name="Alice")
    user_id = user.save()

    product = Product(name="Laptop")
    product_id = product.save()

    assert user_id is not None
    assert product_id is not None
