import logging
from typing import Optional

from CateringAiSystem.Models.sysModels import SysRole, SysRoleMenu, SysUserRole

logger = logging.getLogger(__name__)


class SysRoleService:

    @staticmethod
    def get_list(page: int = 1, page_size: int = 20, role_name: Optional[str] = None,
                 status: Optional[int] = None) -> dict:
        """分页查询角色列表"""
        try:
            db = SysRole.get_db_connection()
            if db is None:
                return {"total": 0, "page": page, "page_size": page_size, "data": []}

            table_name = SysRole.get_table_name_with_db()
            where_clauses = []
            params = []

            if role_name:
                where_clauses.append("`role_name` LIKE %s")
                params.append(f"%{role_name}%")
            if status is not None:
                where_clauses.append("`status` = %s")
                params.append(status)

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            count_sql = f"SELECT COUNT(*) AS total FROM {table_name} WHERE {where_sql}"
            count_result = db.execute(count_sql, tuple(params))
            total = count_result[0]["total"] if count_result else 0

            offset = (page - 1) * page_size
            list_sql = f"""SELECT * FROM {table_name}
WHERE {where_sql}
ORDER BY `sort_order` ASC, `id` ASC
LIMIT {offset}, {page_size}"""
            results = db.execute(list_sql, tuple(params))

            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "data": results or [],
            }
        except Exception as e:
            logger.error(f"查询角色列表失败: {e}")
            return {"total": 0, "page": page, "page_size": page_size, "data": []}

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
        try:
            db = SysRole.get_db_connection()
            if db is None:
                return {"success": False, "message": "数据库连接失败"}

            # 检查是否有关联用户
            user_links = SysUserRole.find_by(role_id=role_id)
            if user_links:
                return {"success": False, "message": f"该角色下存在 {len(user_links)} 个关联用户，无法删除"}

            # 删除角色-菜单关联
            rm_table = SysRoleMenu.get_table_name_with_db()
            db.execute(f"DELETE FROM {rm_table} WHERE `role_id` = %s", (role_id,), commit=True)

            SysRole.delete_by_id(role_id)
            return {"success": True, "message": "删除成功"}
        except Exception as e:
            logger.error(f"删除角色失败: {e}")
            return {"success": False, "message": f"删除失败: {e}"}

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
        try:
            db = SysRole.get_db_connection()
            if db is None:
                return False

            table_name = SysRoleMenu.get_table_name_with_db()

            # 删除旧关联
            db.execute(f"DELETE FROM {table_name} WHERE `role_id` = %s", (role_id,), commit=True)

            # 批量插入新关联
            if menu_ids:
                values = ",".join([f"({role_id}, {mid})" for mid in menu_ids])
                sql = f"INSERT INTO {table_name} (`role_id`, `menu_id`) VALUES {values}"
                db.execute(sql, commit=True)

            return True
        except Exception as e:
            logger.error(f"分配菜单权限失败: {e}")
            return False

    @staticmethod
    def get_all_roles() -> list:
        """获取所有启用角色列表（供选择器用）"""
        try:
            roles = SysRole.find_by(status=1)
            return [{"id": r.id, "role_name": r.role_name, "role_code": r.role_code} for r in roles]
        except Exception as e:
            logger.error(f"获取全部角色失败: {e}")
            return []
