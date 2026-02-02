# Repository 模块测试文档

## 测试概述

本目录包含 Repository 模块的所有测试用例，使用 pytest 框架。

## 测试文件

| 文件 | 描述 | 测试数量 |
|------|------|----------|
| `test_base_connection.py` | 测试 BaseConnection 抽象基类 | 10+ |
| `test_sqlite_connection.py` | 测试 SQLite 连接实现 | 20+ |
| `test_base_db_model.py` | 测试 BaseDBModel ORM 功能 | 40+ |
| `test_connection_manager.py` | 测试 ConnectionManager 连接管理 | 15+ |
| `test_integration.py` | 集成测试和端到端场景 | 10+ |

## 运行测试

### 安装依赖

```bash
pip install pytest
```

### 运行所有测试

```bash
# 在项目根目录执行
pytest Base/Repository/test/

# 或在 test 目录执行
pytest
```

### 运行特定测试文件

```bash
# 只运行 SQLite 连接测试
pytest test_sqlite_connection.py -v

# 只运行 BaseDBModel 测试
pytest test_base_db_model.py -v
```

### 运行特定测试函数

```bash
# 运行单个测试
pytest test_sqlite_connection.py::test_sqlite_connection_create_memory_db -v

# 运行包含特定名称的测试
pytest -k "insert" -v
```

### 查看详细输出

```bash
# 显示详细输出
pytest -v

# 显示打印的输出（-s）
pytest -v -s

# 显示最慢的测试（--durations）
pytest -v --durations=10
```

### 生成覆盖率报告

```bash
# 安装 coverage
pip install coverage pytest-cov

# 生成覆盖率报告
pytest --cov=Base.Repository --cov-report=html

# 在浏览器中查看
open htmlcov/index.html
```

### 只运行失败的测试

```bash
# 第一次运行
pytest -v

# 只运行失败的测试
pytest --lf -v
```

## 测试 Fixture

### conftest.py

提供了以下共享 fixtures：

- `test_db_dir`: 测试数据库目录（session 级别）
- `test_sqlite_db`: 创建测试用的 SQLite 数据库文件
- `cleanup_connections`: 测试后清理所有连接

### 使用示例

```python
def test_example(test_sqlite_db):
    """使用 SQLite 测试数据库"""
    db = SQLiteConnection(database=str(test_sqlite_db))
    # 测试代码
    db.close()
```

## 测试命名规范

所有测试函数必须以 `test_` 开头，例如：

```python
def test_sqlite_connection_create_memory_db():
    """测试创建内存数据库"""
    pass
```

## 断言示例

```python
# 简单断言
assert result is not None
assert count == 10

# 异常断言
with pytest.raises(ValueError):
    some_function()

# 包含断言
assert "error" in str(exc_info.value)
```

## 测试最佳实践

### 1. 每个测试独立

```python
def test_independent():
    # 不依赖其他测试的状态
    pass
```

### 2. 使用 fixtures

```python
@pytest.fixture
def setup_data():
    # 设置测试数据
    data = {"key": "value"}
    yield data
    # 清理
```

### 3. 清理资源

```python
def test_with_cleanup(test_db_dir):
    db = SQLiteConnection(database=":memory:")
    try:
        # 测试代码
        pass
    finally:
        db.close()
```

### 4. 测试边界条件

```python
def test_boundary_conditions():
    # 测试空值、最大值、最小值等
    assert handle(None) is None
    assert handle(0) is not None
```

## 持续集成

测试应该在每个 PR 之前运行，确保代码质量。

## 贡献指南

1. 为新功能添加测试
2. 保持测试覆盖率 > 80%
3. 每个测试函数应该有清晰的文档字符串
4. 使用有意义的测试名称

## 常见问题

### Q: 如何调试测试？

A: 使用 `-s` 选项查看打印输出：

```bash
pytest -v -s test_module.py::test_function
```

### Q: 如何跳过某些测试？

A: 使用 `@pytest.mark.skip` 装饰器：

```python
@pytest.mark.skip(reason="待修复")
def test_broken_feature():
    pass
```

### Q: 如何标记慢速测试？

A: 使用 `@pytest.mark.slow` 装饰器：

```python
@pytest.mark.slow
def test_slow_operation():
    pass
```

运行时排除慢速测试：

```bash
pytest -v -m "not slow"
```

## 参考资料

- [pytest 文档](https://docs.pytest.org/)
- [Repository 模块文档](../README.md)
