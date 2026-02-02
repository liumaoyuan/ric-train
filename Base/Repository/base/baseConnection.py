from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class BaseConnection(ABC):
    """
    数据库连接抽象基类

    定义了所有数据库连接应该实现的核心接口。
    具体的数据库实现（MySQL, PostgreSQL, Oracle, SQLite）应该继承此类。
    """

    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        database: str,
        port: int,
        charset: str,
        # 连接池通用参数
        mincached: int,
        maxcached: int,
        maxconnections: int,
        blocking: bool,
    ):
        self.config = {
            "host": host,
            "user": user,
            "password": password,
            "database": database,
            "port": port,
            "charset": charset,
        }
        self.pool_config = {
            "mincached": mincached,
            "maxcached": maxcached,
            "maxconnections": maxconnections,
            "blocking": blocking,
        }
        self._connection_pool = None

    # ======================
    # 抽象方法（必须由子类实现）
    # ======================

    @abstractmethod
    def _ensure_database_exists(self):
        """如果数据库不存在，则自动创建"""
        pass

    @abstractmethod
    def _create_connection_pool(self):
        """创建连接池（子类根据具体数据库实现）"""
        pass

    @abstractmethod
    def _get_raw_connection(self):
        """获取原生数据库连接（不使用连接池时）"""
        pass

    # ======================
    # 公共方法（所有数据库通用）
    # ======================

    def get_connection(self):
        """从连接池获取一个数据库连接"""
        if self._connection_pool is not None:
            return self._connection_pool.connection()
        else:
            return self._get_raw_connection()

    @contextmanager
    def get_connection_context(self):
        """获取连接的上下文管理器，自动归还连接到池中"""
        conn = self.get_connection()
        try:
            yield conn
        finally:
            conn.close()  # 关闭连接会自动归还到连接池

    def execute_query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """执行查询语句，返回结果列表"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                return cur.fetchall()
        finally:
            conn.close()

    def execute_update(self, sql: str, params: Optional[tuple] = None, commit: bool = True) -> int:
        """执行更新语句，返回影响的行数"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                affected = cur.rowcount
                if commit:
                    conn.commit()
                return affected
        finally:
            conn.close()

    def execute_insert(self, sql: str, params: Optional[tuple] = None, commit: bool = True) -> int:
        """执行插入语句，返回插入的ID"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                last_id = cur.lastrowid
                if commit:
                    conn.commit()
                return last_id
        finally:
            conn.close()

    @contextmanager
    def get_connection_for_transaction(self):
        """
        获取用于事务的连接上下文管理器
        用于需要跨多个操作的事务，连接不会在每次操作后自动归还
        """
        conn = self.get_connection()
        try:
            yield conn
        finally:
            conn.close()  # 事务结束后归还连接到连接池

    def close(self) -> None:
        """关闭连接池（释放所有连接）"""
        if self._connection_pool is not None:
            logger.info("连接池已关闭")
        logger.debug("DatabaseConnection 已释放")
