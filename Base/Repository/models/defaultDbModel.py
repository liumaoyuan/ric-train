from Base.Repository.base.baseDBModel import BaseDBModel
from Base.Repository.base.connectionManager import ConnectionManager


class DefaultDbModel(BaseDBModel):
    _db_connection = ConnectionManager.get_default()