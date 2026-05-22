import asyncio
import logging

import aiomysql
from aiomysql.cursors import DictCursor

from Base.Repository.base.baseConnection import BaseConnection, OperationType

logger = logging.getLogger(__name__)


class AsyncMySQLConnection(BaseConnection):
    """
    异步 MySQL 数据库连接实现

    基于 aiomysql 提供原生异步数据库操作。
    同步 execute() 会抛出 NotImplementedError，请使用 aexecute() 进行异步操作。

    使用方法：
        async_conn = AsyncMySQLConnection(host=..., user=..., ...)
        BaseDBModel.set_default_db_connection(async_conn)
        user = await User.aget_by_id(1)
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
        self.config["type"] = "mysql"
        self._async_pool = None
        self._async_pool_lock = asyncio.Lock()

    # ======================
    # 同步方法（不支持）
    # ======================

    def _ensure_database_exists(self):
        """数据库创建在异步懒初始化时完成"""
        pass

    def _create_connection_pool(self):
        """连接池在异步懒初始化时创建"""
        pass

    def _get_raw_connection(self):
        raise NotImplementedError(
            "AsyncMySQLConnection 不支持同步 get_raw_connection()，请使用 aexecute()"
        )

    def execute(self, *args, **kwargs):
        raise NotImplementedError(
            "AsyncMySQLConnection 不支持同步 execute()，请使用 await aexecute()"
        )

    # ======================
    # 异步连接池（懒初始化）
    # ======================

    @property
    async def async_pool(self):
        """获取异步连接池，首次访问时自动初始化"""
        if self._async_pool is None:
            async with self._async_pool_lock:
                if self._async_pool is None:
                    await self._aensure_database_exists()
                    await self._acreate_connection_pool()
        return self._async_pool

    async def _aensure_database_exists(self):
        """异步检查数据库是否存在，不存在则自动创建"""
        db_name = self.config["database"]
        try:
            conn = await aiomysql.connect(
                host=self.config["host"],
                user=self.config["user"],
                password=self.config["password"],
                port=self.config["port"],
                charset=self.config["charset"],
                cursorclass=DictCursor,
                autocommit=False,
            )
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s",
                        (db_name,),
                    )
                    exists = (await cur.fetchone()) is not None
                    if not exists:
                        logger.info(f"数据库 {db_name} 不存在，正在创建...")
                        await cur.execute(
                            f"CREATE DATABASE `{db_name}` "
                            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                        )
                        await conn.commit()
                        logger.info(f"数据库 {db_name} 创建成功")
                    else:
                        logger.debug(f"数据库 {db_name} 已存在")
            finally:
                conn.close()
        except Exception as e:
            logger.warning(f"检查/创建数据库 {db_name} 失败：{e}")
            self._is_available = False

    async def _acreate_connection_pool(self):
        """异步创建 aiomysql 连接池"""
        try:
            pool_config = {
                k: v
                for k, v in self.config.items()
                if k not in ["cursorclass", "type"]
            }
            self._async_pool = await aiomysql.create_pool(
                cursorclass=DictCursor,
                autocommit=False,
                minsize=self.pool_config["mincached"],
                maxsize=self.pool_config["maxconnections"],
                pool_recycle=3600,
                **pool_config,
            )
            logger.info(
                f"异步MySQL连接池创建成功: "
                f"host={self.config['host']}, port={self.config['port']}, "
                f"database={self.config['database']}, "
                f"minsize={self.pool_config['mincached']}, "
                f"maxsize={self.pool_config['maxconnections']}"
            )
        except Exception as e:
            logger.warning(f"创建异步MySQL连接池失败：{e}")
            self._async_pool = None
            self._is_available = False

    # ======================
    # 异步 SQL 执行
    # ======================

    async def aexecute(self, sql, params=None, operation_type=None, commit=True):
        """
        异步执行 SQL 语句

        参数和返回值与 BaseConnection.execute() 保持一致：
        - query:  返回 List[Dict[str, Any]]
        - insert: 返回 int (lastrowid)
        - 其他:   返回 int (影响行数)
        """
        if not self._is_available:
            if operation_type is None:
                operation_type = self._detect_operation_type(sql)
            logger.debug(f"数据库连接不可用，跳过操作: {operation_type}")
            return self._default_return(operation_type, is_error=False)

        if operation_type is None:
            operation_type = self._detect_operation_type(sql)

        self._log_sql_execution(sql, params, operation_type)

        pool = await self.async_pool
        if pool is None:
            logger.warning("异步连接池未创建，跳过操作")
            return self._default_return(operation_type, is_error=False)

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql, params or ())

                    if operation_type == OperationType.QUERY:
                        result = await cur.fetchall()
                        logger.debug(f"查询返回 {len(result)} 行数据")
                        return result
                    elif operation_type == OperationType.INSERT:
                        last_id = cur.lastrowid
                        if commit:
                            await conn.commit()
                            logger.debug(f"提交事务，插入 ID: {last_id}")
                        return last_id
                    else:
                        affected = cur.rowcount
                        if commit:
                            await conn.commit()
                            logger.debug(f"提交事务，影响行数: {affected}")
                        return affected
        except Exception as e:
            # MySQL 错误码 1050 = 表已存在，不标记连接不可用
            if getattr(e, "args", None) and e.args[0] == 1050:
                logger.debug(f"表已存在，跳过：{e}")
                return 0
            logger.warning(f"异步 SQL 执行失败，标记连接为不可用：{e}")
            self._is_available = False
            logger.debug(f"失败 SQL: {sql}")
            logger.debug(f"参数: {params}")
            return self._default_return(operation_type, is_error=True)

    # ======================
    # 工具方法
    # ======================

    @staticmethod
    def _default_return(operation_type, is_error=False):
        """根据操作类型和状态返回默认值（与同步 execute 行为一致）"""
        if operation_type == OperationType.QUERY:
            return []
        elif operation_type == OperationType.INSERT:
            return -1
        else:
            return -1 if is_error else 0

    def get_connection_url(self) -> str:
        """获取异步 MySQL 连接URL（SQLAlchemy 格式）"""
        from urllib.parse import quote_plus

        user = self.config["user"]
        password = self.config["password"]
        host = self.config["host"]
        port = self.config["port"]
        database = self.config["database"]
        charset = self.config["charset"]
        encoded_password = quote_plus(password)
        url = (
            f"mysql+aiomysql://{user}:{encoded_password}@{host}:{port}/"
            f"{database}?charset={charset}"
        )
        logger.debug(f"异步MySQL连接URL: {user}:***@{host}:{port}/{database}")
        return url

    def close(self):
        """同步关闭连接池（尝试关闭，可能需要在事件循环中执行）"""
        if self._async_pool is not None and not self._async_pool._closed:
            self._async_pool.close()
            logger.info("异步MySQL连接池已关闭（同步 close）")
        super().close()

    async def aclose(self):
        """异步关闭连接池"""
        if self._async_pool is not None and not self._async_pool._closed:
            self._async_pool.close()
            await self._async_pool.wait_closed()
            self._async_pool = None
            logger.info("异步MySQL连接池已关闭（异步 aclose）")
