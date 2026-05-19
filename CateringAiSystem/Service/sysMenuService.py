import logging
from typing import Optional, List

from CateringAiSystem.Models import SysMenu, SysRoleMenu

logger = logging.getLogger(__name__)


class SysMenuService:

    @staticmethod
    def get_tree() -> List[dict]:
        """获取菜单树（完整的嵌套树形结构）"""
        try:
            menus = SysMenu.get_all(order_by="sort_order", order="ASC")
            if not menus:
                return []

            menu_list = [m.to_dict() for m in menus]
            return SysMenuService._build_tree(menu_list, parent_id=0)
        except Exception as e:
            logger.error(f"获取菜单树失败: {e}")
            return []

    @staticmethod
    def get_filtered_tree(allowed_ids: set) -> list:
        """根据菜单 ID 集合过滤菜单树（保留祖先节点以保证树结构完整）"""
        try:
            menus = SysMenu.get_all(order_by="sort_order", order="ASC")
            if not menus:
                return []

            menu_list = [m.to_dict() for m in menus]

            # 收集所有需要保留的 ID（包含祖先节点）
            all_ids = set(allowed_ids)
            id_to_parent = {m["id"]: m["parent_id"] for m in menu_list}

            for mid in list(allowed_ids):
                parent = id_to_parent.get(mid, 0)
                while parent != 0:
                    all_ids.add(parent)
                    parent = id_to_parent.get(parent, 0)

            filtered = [m for m in menu_list if m["id"] in all_ids]
            return SysMenuService._build_tree(filtered, parent_id=0)
        except Exception as e:
            logger.error(f"获取过滤菜单树失败: {e}")
            return []

    @staticmethod
    def _build_tree(menu_list: list, parent_id: int) -> list:
        """递归构建菜单树"""
        tree = []
        for menu in menu_list:
            if menu.get("parent_id") == parent_id:
                children = SysMenuService._build_tree(menu_list, menu["id"])
                if children:
                    menu["children"] = children
                tree.append(menu)
        return tree

    @staticmethod
    def get_flat_list() -> list:
        """获取扁平菜单列表"""
        try:
            menus = SysMenu.get_all(order_by="sort_order", order="ASC")
            return [m.to_dict() for m in menus] if menus else []
        except Exception as e:
            logger.error(f"获取菜单列表失败: {e}")
            return []

    @staticmethod
    def get_detail(menu_id: int) -> Optional[dict]:
        """获取菜单详情"""
        menu = SysMenu.get_by_id(menu_id)
        if menu is None:
            return None
        return menu.to_dict()

    @staticmethod
    def create(data: dict, operator_id: int = 0) -> Optional[int]:
        """新增菜单"""
        try:
            menu = SysMenu(
                parent_id=data.get("parent_id", 0),
                menu_name=data["menu_name"],
                menu_type=data.get("menu_type", 0),
                permission_code=data.get("permission_code"),
                path=data.get("path"),
                component=data.get("component"),
                icon=data.get("icon"),
                sort_order=data.get("sort_order", 0),
                status=data.get("status", 1),
                visible=data.get("visible", 1),
                created_by=operator_id,
                updated_by=operator_id,
            )
            menu_id = menu.save()
            return menu_id if menu_id > 0 else None
        except Exception as e:
            logger.error(f"创建菜单失败: {e}")
            return None

    @staticmethod
    def update(menu_id: int, data: dict, operator_id: int = 0) -> bool:
        """编辑菜单"""
        try:
            menu = SysMenu.get_by_id(menu_id)
            if menu is None:
                return False

            update_fields = {}
            for field in ["parent_id", "menu_name", "menu_type", "permission_code",
                          "path", "component", "icon", "sort_order", "status", "visible"]:
                if field in data:
                    update_fields[field] = data[field]
            update_fields["updated_by"] = operator_id

            return menu.update(**update_fields)
        except Exception as e:
            logger.error(f"编辑菜单失败: {e}")
            return False

    @staticmethod
    def delete(menu_id: int) -> dict:
        """删除菜单，返回操作结果"""
        try:
            db = SysMenu.get_db_connection()
            if db is None:
                return {"success": False, "message": "数据库连接失败"}

            # 检查是否有子节点
            children = SysMenu.find_by(parent_id=menu_id)
            if children:
                return {"success": False, "message": f"该菜单下存在 {len(children)} 个子节点，请先删除子节点"}

            # 删除角色-菜单关联
            rm_table = SysRoleMenu.get_table_name_with_db()
            db.execute(f"DELETE FROM {rm_table} WHERE `menu_id` = %s", (menu_id,), commit=True)

            SysMenu.delete_by_id(menu_id)
            return {"success": True, "message": "删除成功"}
        except Exception as e:
            logger.error(f"删除菜单失败: {e}")
            return {"success": False, "message": f"删除失败: {e}"}
