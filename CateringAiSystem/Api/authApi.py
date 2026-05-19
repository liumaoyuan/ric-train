from fastapi import APIRouter, Request
from pydantic import BaseModel

from CateringAiSystem.Service.authService import AuthService
from CateringAiSystem.Utils.rbacUtils import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["认证管理"])


class LoginParam(BaseModel):
    username: str
    password: str


class RefreshParam(BaseModel):
    refresh_token: str


@router.post("/login")
def login(param: LoginParam):
    """用户登录"""
    result = AuthService.authenticate(param.username, param.password)
    if result is None:
        return {"code": 401, "msg": "用户名或密码错误", "data": None}
    return {"code": 200, "msg": "登录成功", "data": result}


@router.post("/logout")
def logout():
    """用户登出（前端清除 Token 即可，后端无需持久化操作）"""
    return {"code": 200, "msg": "退出成功", "data": None}


@router.get("/userinfo")
def userinfo(request: Request):
    """获取当前用户信息"""
    user = get_current_user(request)
    info = AuthService.get_user_info(user["user_id"])
    if info is None:
        return {"code": 404, "msg": "用户不存在", "data": None}
    return {"code": 200, "msg": "success", "data": info}


@router.get("/menus")
def current_user_menus(request: Request):
    """获取当前用户的菜单树（根据角色权限过滤）"""
    user = get_current_user(request)
    tree = AuthService.get_user_menu_tree(user["user_id"], user.get("roles", []))
    return {"code": 200, "msg": "success", "data": tree}


@router.post("/refresh")
def refresh_token(param: RefreshParam):
    """刷新访问令牌"""
    result = AuthService.refresh_access_token(param.refresh_token)
    if result is None:
        return {"code": 401, "msg": "刷新令牌无效或已过期", "data": None}
    return {"code": 200, "msg": "刷新成功", "data": result}
