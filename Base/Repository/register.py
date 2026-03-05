from Base.Config.setting import settings
from Base.Repository.base.baseDBModel import BaseDBModel
from Base.Repository.connections.mysqlConnection import MySQLConnection
from Base.Repository.base.connectionManager import ConnectionManager
import logging

logger = logging.getLogger(__name__)


def register_default_connection():
    """注册默认数据库连接，如果连接失败则记录日志但不影响程序运行"""
    try:
        ConnectionManager.register(key='default', db_connection=MySQLConnection(
            host=settings.mysql.host,
            user=settings.mysql.user,
            password=settings.mysql.password,
            database=settings.mysql.name,
            port=settings.mysql.port,
            charset="utf8mb4",
            mincached=2,
            maxcached=10,
            maxconnections=20,
            blocking=False,
        ), is_default=True)
        BaseDBModel.set_default_db_connection(ConnectionManager.get_default())
        logger.info(f"默认数据库连接注册成功 - host: {settings.mysql.host}, port: {settings.mysql.port}, database: {settings.mysql.name}, user: {settings.mysql.user}")
    except Exception as e:
        logger.warning(f"注册默认数据库连接失败，程序将以无持久化模式运行：{str(e)}")


def register_base_module_connection():
    """注册基础模块数据库连接，如果连接失败则记录日志但不影响程序运行"""
    try:
        ConnectionManager.register(key='base_module', db_connection=MySQLConnection(
            host=settings.mysql.host,
            user=settings.mysql.user,
            password=settings.mysql.password,
            database=settings.base_module.db_name,
            port=settings.mysql.port,
            charset="utf8mb4",
            mincached=2,
            maxcached=10,
            maxconnections=20,
            blocking=False,
        ))
        logger.info(f"基础模块数据库连接注册成功 - host: {settings.mysql.host}, port: {settings.mysql.port}, database: {settings.base_module.db_name}, user: {settings.mysql.user}")
    except Exception as e:
        logger.warning(f"注册基础模块数据库连接失败，相关功能将无法持久化：{str(e)}")


def register_game_helper_connection():
    """注册 GameHelper 模块数据库连接，如果连接失败则记录日志但不影响程序运行"""
    try:
        # 使用 GAME_ 前缀的配置，如果未设置则回退到 DB_ 配置
        db_name = settings.game_helper.db_name or settings.mysql.name
        db_host = settings.game_helper.db_host or settings.mysql.host
        db_port = settings.game_helper.db_port or settings.mysql.port
        db_user = settings.game_helper.db_user or settings.mysql.user
        db_password = settings.game_helper.db_password or settings.mysql.password

        ConnectionManager.register(key='game_helper', db_connection=MySQLConnection(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            port=db_port,
            charset="utf8mb4",
            mincached=2,
            maxcached=10,
            maxconnections=20,
            blocking=False,
        ))
        logger.info(f"GameHelper 数据库连接注册成功 - host: {db_host}, port: {db_port}, database: {db_name}, user: {db_user}")
    except Exception as e:
        logger.warning(f"注册 GameHelper 数据库连接失败，相关功能将无法持久化：{str(e)}")
