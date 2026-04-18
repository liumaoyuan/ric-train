import logging

from Base.Config.setting import settings
from Base.Repository.base.baseDBModel import BaseDBModel
from Base.Repository.base.connectionManager import ConnectionManager
from Base.Repository.connections.mysqlConnection import MySQLConnection

logger = logging.getLogger(__name__)

def register_wolin_connection():
    """注册默认数据库连接，如果连接失败则记录日志但不影响程序运行"""
    try:
        ConnectionManager.register(key='wolin', db_connection=MySQLConnection(
            host=settings.default.get('wolin_db_host'),
            user=settings.default.get('wolin_db_user'),
            password=settings.default.get('wolin_db_password'),
            database=settings.default.get('wolin_db_name'),
            port=int(settings.default.get('wolin_db_port')),
            charset="utf8mb4",
            mincached=2,
            maxcached=10,
            maxconnections=20,
            blocking=False,
        ), is_default=True)
        BaseDBModel.set_default_db_connection(ConnectionManager.get_default())
        logger.info(f"Wolin 数据库连接注册成功 - host: {settings.default.get('WOLIN_DB_HOST')}, port: {settings.default.get('WOLIN_DB_PORT')}, database: {settings.default.get('WOLIN_DB_NAME')}, user: {settings.default.get('WOLIN_DB_USER')}")
    except Exception as e:
        logger.warning(f"注册 Wolin 数据库连接失败，程序将以无持久化模式运行：{str(e)}")


class WolinModuleDBModel(BaseDBModel):
    """
    Wolin 模块数据库模型基类

    使用延迟连接获取，确保 register_wolin_connection() 先被调用
    """
    _db_connection = None  # 初始为 None，延迟获取

    @classmethod
    def get_db_connection(cls):
        """延迟获取数据库连接"""
        if cls._db_connection is None:
            try:
                cls._db_connection = ConnectionManager.get('wolin')
            except ValueError:
                # 如果 'wolin' 连接未注册，返回 None
                logger.warning(f"'wolin' 数据库连接未注册，操作将被跳过")
                return None
        return cls._db_connection
