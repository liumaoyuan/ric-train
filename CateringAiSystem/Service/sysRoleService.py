import logging
from typing import Optional

from CateringAiSystem.Models import SysRole, SysRoleMenu

logger = logging.getLogger(__name__)


class SysRoleService:

    @staticmethod
    def get_list(page: int = 1, page_size: int = 20, role_name: Optional[str] = None,
                 status: Optional[int] = None) -> dict:
        """分页查询角色列表"""
        return SysRole.get_paginated_list(page, page_size, role_name, status)

    @staticmethod
    def get_detail(role_id: int) -> Optional[dict]:
        """获取角色详情"""
        role = SysRole.get_by_id(role_id)
        if role is None:
            return None
        return role.to_dict()

    @staticmethod
    def create(data: dict, operator_id: int = 0) -> Optional[int]:
        """新增角色"""
        try:
            existing = SysRole.find_one_by(role_code=data["role_code"])
            if existing:
                logger.warning(f"创建角色失败：编码 {data['role_code']} 已存在")
                return None

            role = SysRole(
                role_name=data["role_name"],
                role_code=data["role_code"],
                description=data.get("description"),
                status=data.get("status", 1),
                sort_order=data.get("sort_order", 0),
                created_by=operator_id,
                updated_by=operator_id,
            )
            role_id = role.save()
            return role_id if role_id > 0 else None
        except Exception as e:
            logger.error(f"创建角色失败: {e}")
            return None

    @staticmethod
    def update(role_id: int, data: dict, operator_id: int = 0) -> bool:
        """编辑角色"""
        try:
            role = SysRole.get_by_id(role_id)
            if role is None:
                return False

            update_fields = {}
            for field in ["role_name", "description", "status", "sort_order"]:
                if field in data:
                    update_fields[field] = data[field]
            update_fields["updated_by"] = operator_id

            return role.update(**update_fields)
        except Exception as e:
            logger.error(f"编辑角色失败: {e}")
            return False

    @staticmethod
    def delete(role_id: int) -> dict:
        """删除角色，返回操作结果"""
        return SysRole.delete_cascade(role_id)

    @staticmethod
    def toggle_status(role_id: int) -> Optional[int]:
        """启用/禁用角色"""
        try:
            role = SysRole.get_by_id(role_id)
            if role is None:
                return None
            new_status = 0 if role.status == 1 else 1
            role.update(status=new_status)
            return new_status
        except Exception as e:
            logger.error(f"切换角色状态失败: {e}")
            return None

    @staticmethod
    def get_menu_ids(role_id: int) -> list:
        """获取角色的菜单ID列表"""
        try:
            records = SysRoleMenu.find_by(role_id=role_id)
            return [r.menu_id for r in records]
        except Exception as e:
            logger.error(f"获取角色菜单失败: {e}")
            return []

    @staticmethod
    def assign_menus(role_id: int, menu_ids: list) -> bool:
        """分配菜单权限（全量替换，事务中完成）"""
        return SysRole.assign_menus(role_id, menu_ids)

    @staticmethod
    def get_all_roles() -> list:
        """获取所有启用角色列表（供选择器用）"""
        try:
            roles = SysRole.find_by(status=1)
            return [{"id": r.id, "role_name": r.role_name, "role_code": r.role_code} for r in roles]
        except Exception as e:
            logger.error(f"获取全部角色失败: {e}")
            return []
