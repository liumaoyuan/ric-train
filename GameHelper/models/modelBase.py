"""
GameHelper 模块数据库模型基类
复用 Base 模块的连接，使用 game_helper 专用连接
"""
from Base.Repository.base.baseDBModel import BaseDBModel
from Base.Repository.base.connectionManager import ConnectionManager


class GameHelperDBModel(BaseDBModel):
    """
    GameHelper 模块数据库模型基类

    所有 GameHelper 的数据库模型都应继承此类，
    自动使用 game_helper 数据库连接。

    使用示例：
        class GameEntityModel(GameHelperDBModel):
            table_alias: ClassVar[str] = "game_entity"
            ...
    """
    # 延迟获取 game_helper 数据库连接（在类初始化时获取）
    _db_connection = None

    @classmethod
    def get_db_connection(cls):
        """重写获取连接的方法，从 ConnectionManager 获取 game_helper 连接"""
        if cls._db_connection is None:
            cls._db_connection = ConnectionManager.get('game_helper')
        return cls._db_connection

    @classmethod
    def set_db_connection(cls, db_connection):
        """为当前模型类设置数据库连接"""
        cls._db_connection = db_connection
