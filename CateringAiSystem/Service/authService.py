import logging

from CateringAiSystem.Models import SysUser
from CateringAiSystem.Service.sysMenuService import SysMenuService
from CateringAiSystem.Utils.authUtils import (
    verify_password,
    hash_password,
    create_tokens,
    decode_token,
    create_access_token,
)

logger = logging.getLogger(__name__)


class AuthService:

    @staticmethod
    def authenticate(username: str, password: str) -> dict | None:
        """
        用户认证
        Args:
            username: 用户名
            password: 明文密码
        Returns:
            成功返回令牌信息，失败返回 None
        """
        user = SysUser.find_one_by(username=username)
        if user is None:
            logger.warning(f"登录失败：用户 {username} 不存在")
            return None

        if user.status == 0:
            logger.warning(f"登录失败：用户 {username} 已被禁用")
            return None

        if not verify_password(password, user.password_hash):
            logger.warning(f"登录失败：用户 {username} 密码错误")
            return None

        # 获取角色和权限
        roles = SysUser.get_role_codes(user.id)
        permissions = SysUser.get_permission_codes(user.id)

        # 生成令牌
        tokens = create_tokens(user.id, user.username, roles, permissions)

        return {
            **tokens,
            "user_id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "roles": roles,
            "permissions": permissions,
        }

    @staticmethod
    def get_user_info(user_id: int) -> dict | None:
        """获取用户信息（含角色和权限）"""
        user = SysUser.get_by_id(user_id)
        if user is None:
            return None

        roles = SysUser.get_role_codes(user_id)
        permissions = SysUser.get_permission_codes(user_id)

        return {
            "user_id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "phone": user.phone,
            "email": user.email,
            "avatar": user.avatar,
            "status": user.status,
            "roles": roles,
            "permissions": permissions,
        }

    @staticmethod
    def get_user_menu_tree(user_id: int, user_roles: list) -> list:
        """获取当前用户有权限的菜单树（admin 拥有全部菜单）"""
        if "admin" in user_roles:
            return SysMenuService.get_tree()

        menu_ids = SysUser.get_user_menu_ids(user_id)
        if not menu_ids:
            return []

        return SysMenuService.get_filtered_tree(menu_ids)

    @staticmethod
    def refresh_access_token(refresh_token: str) -> dict | None:
        """
        刷新访问令牌
        Args:
            refresh_token: 刷新令牌
        Returns:
            新的令牌信息，失败返回 None
        """
        payload = decode_token(refresh_token)
        if payload is None:
            return None
        if payload.get("type") != "refresh":
            return None

        user_id = payload.get("user_id")
        username = payload.get("username")

        roles = SysUser.get_role_codes(user_id)
        permissions = SysUser.get_permission_codes(user_id)

        new_access_token = create_access_token({
            "user_id": user_id,
            "username": username,
            "roles": roles,
            "permissions": permissions,
        })

        return {
            "access_token": new_access_token,
            "token_type": "Bearer",
        }
