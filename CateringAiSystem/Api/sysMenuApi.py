from fastapi import APIRouter, Request

from CateringAiSystem.Service.sysMenuService import SysMenuService
from CateringAiSystem.Utils.rbacUtils import get_current_user, require_permission

router = APIRouter(prefix="/api/v1/sys/menu", tags=["菜单管理"])


@router.get("/tree")
@require_permission("sys:menu:list")
def menu_tree(request: Request):
    """获取菜单树（完整树形结构）"""
    data = SysMenuService.get_tree()
    return {"code": 200, "msg": "success", "data": data}


@router.get("/list")
@require_permission("sys:menu:list")
def menu_list(request: Request):
    """获取扁平菜单列表（供下拉选择用）"""
    data = SysMenuService.get_flat_list()
    return {"code": 200, "msg": "success", "data": data}


@router.get("/{menu_id}")
@require_permission("sys:menu:list")
def get_menu(menu_id: int, request: Request):
    """菜单详情"""
    data = SysMenuService.get_detail(menu_id)
    if data is None:
        return {"code": 404, "msg": "菜单不存在", "data": None}
    return {"code": 200, "msg": "success", "data": data}


@router.post("")
@require_permission("sys:menu:add")
def create_menu(data: dict, request: Request):
    """新增菜单"""
    user = get_current_user(request)
    menu_id = SysMenuService.create(data, operator_id=user["user_id"])
    if menu_id is None:
        return {"code": 400, "msg": "创建失败", "data": None}
    return {"code": 200, "msg": "创建成功", "data": {"id": menu_id}}


@router.put("/{menu_id}")
@require_permission("sys:menu:edit")
def update_menu(menu_id: int, data: dict, request: Request):
    """编辑菜单"""
    user = get_current_user(request)
    success = SysMenuService.update(menu_id, data, operator_id=user["user_id"])
    if not success:
        return {"code": 404, "msg": "菜单不存在或更新失败", "data": None}
    return {"code": 200, "msg": "更新成功", "data": None}


@router.delete("/{menu_id}")
@require_permission("sys:menu:delete")
def delete_menu(menu_id: int, request: Request):
    """删除菜单"""
    result = SysMenuService.delete(menu_id)
    if not result["success"]:
        return {"code": 400, "msg": result["message"], "data": None}
    return {"code": 200, "msg": "删除成功", "data": None}
