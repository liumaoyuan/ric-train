"""
pytest 配置文件
提供共享的 fixtures 和测试配置
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path


# 测试数据库配置
TEST_DB_DIR = Path(__file__).parent / "test_dbs"
TEST_DB_DIR.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def test_db_dir():
    """测试数据库目录（session 级别）"""
    yield TEST_DB_DIR
    # 清理：测试结束后删除测试数据库文件
    if TEST_DB_DIR.exists():
        shutil.rmtree(TEST_DB_DIR, ignore_errors=True)


@pytest.fixture
def test_sqlite_db(test_db_dir):
    """创建测试用的 SQLite 数据库"""
    db_path = test_db_dir / "test.db"
    yield db_path
    # 清理
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def cleanup_connections():
    """测试后清理所有连接"""
    yield
    # 清理 ConnectionManager 中的所有连接
    from Base.Repository.base.connectionManager import ConnectionManager
    ConnectionManager._connections.clear()
    ConnectionManager._default_key = None

    # 清理 BaseDBModel 的连接
    from Base.Repository.base.baseDBModel import BaseDBModel
    BaseDBModel._default_db_connection = None
    BaseDBModel._db_connection = None
