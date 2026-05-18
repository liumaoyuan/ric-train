import logging

from CateringAiSystem.Models.sysModels import SysUser, SysRole, SysUserRole, SysRoleMenu, SysMenu
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
        roles = AuthService._get_user_roles(user.id)
        permissions = AuthService._get_user_permissions(user.id)

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

        roles = AuthService._get_user_roles(user_id)
        permissions = AuthService._get_user_permissions(user_id)

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

        roles = AuthService._get_user_roles(user_id)
        permissions = AuthService._get_user_permissions(user_id)

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

    @staticmethod
    def _get_user_roles(user_id: int) -> list:
        """获取用户的所有角色编码"""
        try:
            db = SysUser.get_db_connection()
            if db is None:
                return []
            table_name = SysUserRole.get_table_name_with_db()
            role_table = SysRole.get_table_name_with_db()
            sql = f"""SELECT r.`role_code`
FROM {table_name} ur
JOIN {role_table} r ON r.`id` = ur.`role_id`
WHERE ur.`user_id` = %s AND r.`status` = 1"""
            results = db.execute(sql, (user_id,))
            return [row["role_code"] for row in results] if results else []
        except Exception as e:
            logger.error(f"获取用户角色失败: {e}")
            return []

    @staticmethod
    def _get_user_permissions(user_id: int) -> list:
        """获取用户的所有权限标识"""
        try:
            db = SysUser.get_db_connection()
            if db is None:
                return []
            ur_table = SysUserRole.get_table_name_with_db()
            rm_table = SysRoleMenu.get_table_name_with_db()
            menu_table = SysMenu.get_table_name_with_db()
            sql = f"""SELECT DISTINCT m.`permission_code`
FROM {ur_table} ur
JOIN {rm_table} rm ON rm.`role_id` = ur.`role_id`
JOIN {menu_table} m ON m.`id` = rm.`menu_id`
WHERE ur.`user_id` = %s AND m.`permission_code` IS NOT NULL AND m.`permission_code` != ''"""
            results = db.execute(sql, (user_id,))
            return [row["permission_code"] for row in results] if results else []
        except Exception as e:
            logger.error(f"获取用户权限失败: {e}")
            return []
