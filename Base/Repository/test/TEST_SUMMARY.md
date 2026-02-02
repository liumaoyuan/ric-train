# Repository 模块测试套件总结

## 测试文件清单

### 1. conftest.py
**作用**: pytest 配置和共享 fixtures

**Fixtures**:
- `test_db_dir`: 测试数据库目录（session 级别）
- `test_sqlite_db`: 创建测试用的 SQLite 数据库文件
- `cleanup_connections`: 测试后清理所有连接

### 2. test_base_connection.py
**作用**: 测试 BaseConnection 抽象基类

**测试内容**:
- ✅ 抽象基类验证
- ✅ 抽象方法验证
- ✅ 配置初始化
- ✅ 公共方法签名
- ✅ 上下文管理器

**测试数量**: 10+

### 3. test_sqlite_connection.py
**作用**: 测试 SQLite 连接实现

**测试内容**:
- ✅ 内存数据库创建
- ✅ 文件数据库创建
- ✅ 连接配置
- ✅ SQL 执行（查询、插入、更新）
- ✅ 事务处理
- ✅ 表存在检查
- ✅ 批量操作
- ✅ 复杂查询
- ✅ 参数处理
- ✅ 连接关闭

**测试数量**: 20+

### 4. test_base_db_model.py
**作用**: 测试 BaseDBModel ORM 功能

**测试内容**:
- ✅ 模型继承和抽象类验证
- ✅ 必需字段验证（id）
- ✅ 表名映射（自动和自定义）
- ✅ CRUD 操作（创建、读取、更新、删除）
- ✅ 条件查询（find_by, find_one_by）
- ✅ 分页查询（get_all with limit/offset）
- ✅ 统计功能（count）
- ✅ 连接优先级（实例 > 类 > 全局）
- ✅ 多模型支持

**测试数量**: 40+

### 5. test_connection_manager.py
**作用**: 测试 ConnectionManager 连接管理

**测试内容**:
- ✅ 注册单个和多个连接
- ✅ 默认连接设置
- ✅ 获取连接（指定和默认）
- ✅ 列出所有连接
- ✅ 关闭单个和所有连接
- ✅ 默认连接覆盖
- ✅ 类级别单例验证

**测试数量**: 15+

### 6. test_integration.py
**作用**: 集成测试和端到端场景

**测试内容**:
- ✅ 完整 CRUD 工作流程
- ✅ 多用户操作
- ✅ 用户-订单关系
- ✅ 事务处理（提交和回滚）
- ✅ 分页功能
- ✅ 搜索和过滤
- ✅ ConnectionManager 工作流程
- ✅ 批量操作
- ✅ 数据一致性
- ✅ 错误处理
- ✅ 复杂场景（用户、订单、日志）

**测试数量**: 10+

## 测试统计

| 文件 | 测试函数数 | 覆盖功能 |
|------|------------|----------|
| test_base_connection.py | 10+ | 抽象基类 |
| test_sqlite_connection.py | 20+ | SQLite 连接 |
| test_base_db_model.py | 40+ | ORM 模型 |
| test_connection_manager.py | 15+ | 连接管理 |
| test_integration.py | 10+ | 集成场景 |
| **总计** | **95+** | **完整覆盖** |

## 运行测试

### 快速开始

```bash
# 进入测试目录
cd Base/Repository/test

# 运行所有测试
pytest

# 运行特定文件
pytest test_sqlite_connection.py -v

# 运行特定测试
pytest test_sqlite_connection.py::test_sqlite_connection_create_memory_db -v
```

### 使用运行脚本

```bash
# 交互式菜单
python run_tests.py

# 选择选项：
# 1. 运行所有测试
# 2-6. 运行特定测试模块
# 7. 生成覆盖率报告
# 8. 只运行失败的测试
# 9. 详细模式
```

## 测试覆盖范围

### 功能覆盖

- ✅ **连接管理**
  - 创建连接（内存、文件）
  - 连接池（SQLite 除外）
  - 连接配置
  - 连接关闭

- ✅ **SQL 执行**
  - 查询（SELECT）
  - 插入（INSERT）
  - 更新（UPDATE）
  - 删除（DELETE）
  - 批量操作

- ✅ **事务处理**
  - 自动提交
  - 手动提交
  - 回滚
  - 上下文管理器

- ✅ **ORM 功能**
  - 模型定义
  - 表名映射
  - CRUD 操作
  - 条件查询
  - 分页
  - 统计

- ✅ **连接管理器**
  - 注册连接
  - 获取连接
  - 默认连接
  - 关闭连接

- ✅ **集成场景**
  - 用户管理
  - 订单处理
  - 关系操作
  - 批量操作
  - 错误处理

### 边界条件

- ✅ 空结果查询
- ✅ 不存在的记录
- ✅ 无影响行的更新/删除
- ✅ 事务回滚
- ✅ 连接优先级
- ✅ 数据一致性

## 测试特点

### 1. 独立性
- 每个测试独立运行
- 不依赖其他测试的状态
- 使用 fixtures 共享资源

### 2. 可维护性
- 清晰的测试命名
- 详细的文档字符串
- 合理的测试分组

### 3. 完整性
- 覆盖主要功能
- 测试边界条件
- 验证错误处理

### 4. 可扩展性
- 易于添加新测试
- fixtures 可复用
- 模块化设计

## 依赖要求

```bash
pip install pytest
pip install pytest-cov  # 可选：生成覆盖率报告
```

## 最佳实践

### 1. 使用 fixtures
```python
@pytest.fixture
def test_db():
    db = SQLiteConnection(database=":memory:")
    yield db
    db.close()

def test_example(test_db):
    # 使用 test_db
    pass
```

### 2. 测试独立
```python
def test_independent():
    # 不依赖其他测试
    pass
```

### 3. 清理资源
```python
def test_with_cleanup(cleanup_connections):
    # 使用 cleanup_connections fixture
    pass
```

### 4. 清晰的断言
```python
assert result is not None
assert count == 10
assert "error" in str(exc_info.value)
```

## 持续集成

建议在 CI/CD 中运行测试：

```yaml
# .github/workflows/test.yml 示例
- name: Run tests
  run: |
    cd Base/Repository/test
    pytest --cov=Base.Repository --cov-report=xml
```

## 下一步

- [ ] 添加性能测试
- [ ] 添加压力测试
- [ ] 提高测试覆盖率到 90%+
- [ ] 添加更多集成场景
- [ ] 添加并发测试

## 参考资料

- [pytest 文档](https://docs.pytest.org/)
- [测试最佳实践](https://docs.python-guide.org/writing/tests/)
- [Repository 模块文档](../README.md)
