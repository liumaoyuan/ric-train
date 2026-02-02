from Base.Config.setting import settings
from Base.Repository.base.baseDBModel import BaseDBModel
from Base.Repository.connections.mysqlConnection import MySQLConnection
from Base.Repository.base.connectionManager import ConnectionManager


def register_default_connection():
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


def register_base_module_connection():
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
