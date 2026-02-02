import sqlite3
from typing import Optional, List, Dict, Any
import logging

from Base.Repository.base.baseConnection import BaseConnection

logger = logging.getLogger(__name__)


class SQLiteConnection(BaseConnection):
    """
    SQLite 数据库连接实现

    继承自 BaseConnection，实现 SQLite 特定的连接管理。
    注意：SQLite 不支持连接池，所有方法都使用单连接模式。
    """

    def __init__(
        self,
        host: str = "",  # SQLite 不使用 host
        user: str = "",  # SQLite 不使用 user
        password: str = "",  # SQLite 不使用 password
        database: str = ":memory:",  # SQLite 数据库文件路径，默认内存数据库
        port: int = 0,  # SQLite 不使用 port
        charset: str = "utf8",
        mincached: int = 0,  # SQLite 不支持连接池
        maxcached: int = 0,
        maxconnections: int = 1,
        blocking: bool = False,
    ):
        # 调用父类初始化（SQLite 不支持连接池）
        super().__init__(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            charset=charset,
            mincached=0,  # 强制为 0
            maxcached=0,
            maxconnections=1,
            blocking=False,
        )

        # 初始化数据库
        self._ensure_database_exists()
        self._create_connection_pool()

    # ======================
    # SQLite 特定实现
    # ======================

    def _ensure_database_exists(self):
        """如果数据库不存在，则自动创建（SQLite 实现）"""
        db_path = self.config["database"]

        # SQLite 会自动创建数据库文件，无需额外处理
        if db_path == ":memory:":
            logger.debug("使用内存数据库")
        else:
            logger.debug(f"使用数据库文件: {db_path}")

    def _create_connection_pool(self):
        """创建连接池（SQLite 不支持连接池）"""
        # SQLite 不支持连接池，设置为 None
        self._connection_pool = None
        logger.debug("SQLite 不支持连接池，使用单连接模式")

    def _get_raw_connection(self):
        """获取原生数据库连接（SQLite 实现）"""
        return sqlite3.connect(
            self.config["database"],
            check_same_thread=False,  # 允许多线程访问
        )

    # ======================
    # 覆盖父类方法以适配 SQLite
    # ======================

    def execute_query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """执行查询语句，返回结果列表（SQLite 使用字典行）"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row  # 设置行工厂
        try:
            cur = conn.cursor()
            cur.execute(sql, params or ())
            results = [dict(row) for row in cur.fetchall()]
            return results
        finally:
            conn.close()

    def execute_update(self, sql: str, params: Optional[tuple] = None, commit: bool = True) -> int:
        """执行更新语句，返回影响的行数（SQLite 自动提交）"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            cur.execute(sql, params or ())
            affected = cur.rowcount
            if commit:
                conn.commit()
            return affected
        finally:
            conn.close()

    def execute_insert(self, sql: str, params: Optional[tuple] = None, commit: bool = True) -> int:
        """执行插入语句，返回插入的ID（SQLite 语法）"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            cur.execute(sql, params or ())
            last_id = cur.lastrowid
            if commit:
                conn.commit()
            return last_id
        finally:
            conn.close()

    # ======================
    # SQLite 便捷方法
    # ======================

    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在（SQLite 特定语法）"""
        sql = """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """
        result = self.execute_query(sql, (table_name,))
        return len(result) > 0
