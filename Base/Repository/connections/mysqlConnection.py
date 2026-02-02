import pymysql
from pymysql.cursors import DictCursor
import logging

from Base.Config.setting import settings
from Base.Repository.base.baseConnection import BaseConnection

logger = logging.getLogger(__name__)


class MySQLConnection(BaseConnection):
    """
    MySQL 数据库连接实现

    继承自 BaseConnection，实现 MySQL 特定的连接管理。
    """

    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        database: str,
        port: int = 3306,
        charset: str = "utf8mb4",
        mincached: int = 2,
        maxcached: int = 10,
        maxconnections: int = 20,
        blocking: bool = False,
    ):
        # 调用父类初始化
        super().__init__(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            charset=charset,
            mincached=mincached,
            maxcached=maxcached,
            maxconnections=maxconnections,
            blocking=blocking,
        )
        # MySQL 特定配置
        self.config["cursorclass"] = DictCursor

        # 初始化连接池
        self._ensure_database_exists()
        self._create_connection_pool()

    # ======================
    # MySQL 特定实现
    # ======================

    def _ensure_database_exists(self):
        """如果数据库不存在，则自动创建（MySQL 实现）"""
        db_name = self.config["database"]

        try:
            # 临时连接（不指定数据库）
            temp_conn = pymysql.connect(
                host=self.config["host"],
                user=self.config["user"],
                password=self.config["password"],
                port=self.config["port"],
                charset=self.config["charset"],
                cursorclass=DictCursor,
                autocommit=False,
            )
            with temp_conn.cursor() as cur:
                # 检查数据库是否存在（MySQL 语法）
                cur.execute(
                    "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s",
                    (db_name,)
                )
                exists = cur.fetchone() is not None

                if not exists:
                    logger.info(f"数据库 {db_name} 不存在，正在创建...")
                    cur.execute(f"CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    temp_conn.commit()
                    logger.info(f"数据库 {db_name} 创建成功")
                else:
                    logger.debug(f"数据库 {db_name} 已存在")

            temp_conn.close()
        except Exception as e:
            logger.error(f"检查/创建数据库 {db_name} 失败：{e}")
            raise

    def _create_connection_pool(self):
        """创建连接池（MySQL 实现）"""
        try:
            from dbutils.pooled_db import PooledDB
            self._connection_pool = PooledDB(
                pymysql,
                **self.config,
                **self.pool_config
            )
            logger.info(f"MySQL 连接池创建成功: mincached={self.pool_config['mincached']}, maxconnections={self.pool_config['maxconnections']}")
        except ImportError:
            logger.warning("DBUtils 未安装，使用单连接模式。请执行: pip install DBUtils")
            self._connection_pool = None

    def _get_raw_connection(self):
        """获取原生数据库连接（MySQL 实现）"""
        return pymysql.connect(
            cursorclass=DictCursor,
            autocommit=False,
            **{k: v for k, v in self.config.items() if k != "cursorclass"}
        )

    # ======================
    # MySQL 便捷方法
    # ======================

    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在（MySQL 特定语法）"""
        sql = """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
        """
        result = self.execute_query(
            sql,
            (self.config["database"], table_name)
        )
        return len(result) > 0


def get_module_mysql_connection():
    """获取Base模块的 MySQL 连接（单例）"""
    return MySQLConnection(
        host=settings.mysql.host,
        user=settings.mysql.user,
        password=settings.mysql.password,
        database=settings.base_module.db_name,
        port=3306,
        charset="utf8mb4",
        mincached=2,
        maxcached=10,
        maxconnections=20,
        blocking=False,
    )

__all__ = ["get_module_mysql_connection"]

if __name__ == '__main__':
    conn = get_module_mysql_connection()
    print(conn.table_exists("test_table"))
