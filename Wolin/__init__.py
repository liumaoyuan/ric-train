# Wolin 包初始化
# 在导入 Wolin 包时自动注册数据库连接

from Wolin.db.connectionInit import register_wolin_connection, WolinModuleDBModel

# 自动执行注册
register_wolin_connection()

__all__ = ['register_wolin_connection', 'WolinModuleDBModel']
