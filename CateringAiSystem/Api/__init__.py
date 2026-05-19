from CateringAiSystem.Api.authApi import router as auth_router
from CateringAiSystem.Api.sysUserApi import router as user_router
from CateringAiSystem.Api.sysRoleApi import router as role_router
from CateringAiSystem.Api.sysMenuApi import router as menu_router
from CateringAiSystem.Api.dataApi import router as data_router
from CateringAiSystem.Middleware.authMiddleware import AuthMiddleware


def register(app):
    # 注册中间件
    app.add_middleware(AuthMiddleware)
    # 注册路由
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(role_router)
    app.include_router(menu_router)
    app.include_router(data_router)
