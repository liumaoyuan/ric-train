import logging
from typing import Optional

from CateringAiSystem.Models import SysUser, SysUserRole
from CateringAiSystem.Utils.authUtils import hash_password

logger = logging.getLogger(__name__)


class SysUserService:

    @staticmethod
    def get_list(page: int = 1, page_size: int = 20, username: Optional[str] = None,
                 status: Optional[int] = None) -> dict:
        """分页查询用户列表"""
        return SysUser.get_paginated_list(page, page_size, username, status)

    @staticmethod
    def get_detail(user_id: int) -> Optional[dict]:
        """获取用户详情"""
        user = SysUser.get_by_id(user_id)
        if user is None:
            return None
        return {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "phone": user.phone,
            "email": user.email,
            "avatar": user.avatar,
            "status": user.status,
            "remark": user.remark,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

    @staticmethod
    def create(data: dict, operator_id: int = 0) -> Optional[int]:
        """新增用户"""
        try:
            # 检查用户名是否已存在
            existing = SysUser.find_one_by(username=data["username"])
            if existing:
                logger.warning(f"创建用户失败：用户名 {data['username']} 已存在")
                return None

            password = data.get("password", "123456")
            user = SysUser(
                username=data["username"],
                password_hash=hash_password(password),
                display_name=data.get("display_name"),
                phone=data.get("phone"),
                email=data.get("email"),
                avatar=data.get("avatar"),
                status=data.get("status", 1),
                remark=data.get("remark"),
                created_by=operator_id,
                updated_by=operator_id,
            )
            user_id = user.save()
            return user_id if user_id > 0 else None
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            return None

    @staticmethod
    def update(user_id: int, data: dict, operator_id: int = 0) -> bool:
        """编辑用户"""
        try:
            user = SysUser.get_by_id(user_id)
            if user is None:
                return False

            update_fields = {}
            for field in ["display_name", "phone", "email", "avatar", "status", "remark"]:
                if field in data:
                    update_fields[field] = data[field]
            update_fields["updated_by"] = operator_id

            return user.update(**update_fields)
        except Exception as e:
            logger.error(f"编辑用户失败: {e}")
            return False

    @staticmethod
    def delete(user_id: int) -> bool:
        """删除用户"""
        return SysUser.delete_cascade(user_id)

    @staticmethod
    def toggle_status(user_id: int) -> Optional[int]:
        """启用/禁用用户，返回新状态"""
        try:
            user = SysUser.get_by_id(user_id)
            if user is None:
                return None
            new_status = 0 if user.status == 1 else 1
            user.update(status=new_status)
            return new_status
        except Exception as e:
            logger.error(f"切换用户状态失败: {e}")
            return None

    @staticmethod
    def reset_password(user_id: int, new_password: str) -> bool:
        """重置用户密码"""
        try:
            user = SysUser.get_by_id(user_id)
            if user is None:
                return False
            return user.update(password_hash=hash_password(new_password))
        except Exception as e:
            logger.error(f"重置密码失败: {e}")
            return False

    @staticmethod
    def get_roles(user_id: int) -> list:
        """获取用户的角色ID列表"""
        try:
            records = SysUserRole.find_by(user_id=user_id)
            return [r.role_id for r in records]
        except Exception as e:
            logger.error(f"获取用户角色失败: {e}")
            return []

    @staticmethod
    def assign_roles(user_id: int, role_ids: list) -> bool:
        """分配角色（全量替换）"""
        return SysUser.assign_roles(user_id, role_ids)
