from typing import Optional

from fastapi import APIRouter, Request, Query

from CateringAiSystem.Service.sysRoleService import SysRoleService
from CateringAiSystem.Utils.rbacUtils import get_current_user, require_permission

router = APIRouter(prefix="/api/v1/sys/role", tags=["角色管理"])


@router.get("/list")
@require_permission("sys:role:list")
def list_roles(request: Request, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
               role_name: Optional[str] = None, status: Optional[int] = None):
    """角色分页列表"""
    data = SysRoleService.get_list(page, page_size, role_name, status)
    return {"code": 200, "msg": "success", "data": data}


@router.get("/all")
@require_permission("sys:role:list")
def all_roles(request: Request):
    """获取所有启用角色列表（供选择器用）"""
    data = SysRoleService.get_all_roles()
    return {"code": 200, "msg": "success", "data": data}


@router.get("/{role_id}")
@require_permission("sys:role:list")
def get_role(role_id: int, request: Request):
    """角色详情"""
    data = SysRoleService.get_detail(role_id)
    if data is None:
        return {"code": 404, "msg": "角色不存在", "data": None}
    return {"code": 200, "msg": "success", "data": data}


@router.post("")
@require_permission("sys:role:add")
def create_role(data: dict, request: Request):
    """新增角色"""
    user = get_current_user(request)
    role_id = SysRoleService.create(data, operator_id=user["user_id"])
    if role_id is None:
        return {"code": 400, "msg": "角色编码已存在", "data": None}
    return {"code": 200, "msg": "创建成功", "data": {"id": role_id}}


@router.put("/{role_id}")
@require_permission("sys:role:edit")
def update_role(role_id: int, data: dict, request: Request):
    """编辑角色"""
    user = get_current_user(request)
    success = SysRoleService.update(role_id, data, operator_id=user["user_id"])
    if not success:
        return {"code": 404, "msg": "角色不存在或更新失败", "data": None}
    return {"code": 200, "msg": "更新成功", "data": None}


@router.delete("/{role_id}")
@require_permission("sys:role:delete")
def delete_role(role_id: int, request: Request):
    """删除角色"""
    result = SysRoleService.delete(role_id)
    if not result["success"]:
        return {"code": 400, "msg": result["message"], "data": None}
    return {"code": 200, "msg": "删除成功", "data": None}


@router.put("/{role_id}/status")
@require_permission("sys:role:toggle")
def toggle_role_status(role_id: int, request: Request):
    """启用/禁用角色"""
    new_status = SysRoleService.toggle_status(role_id)
    if new_status is None:
        return {"code": 404, "msg": "角色不存在", "data": None}
    return {"code": 200, "msg": "操作成功", "data": {"status": new_status}}


@router.get("/{role_id}/menus")
@require_permission("sys:role:list")
def get_role_menus(role_id: int, request: Request):
    """获取角色的菜单权限ID列表"""
    menu_ids = SysRoleService.get_menu_ids(role_id)
    return {"code": 200, "msg": "success", "data": {"menu_ids": menu_ids}}


@router.put("/{role_id}/menus")
@require_permission("sys:role:assign-menu")
def assign_role_menus(role_id: int, data: dict, request: Request):
    """分配菜单权限（全量替换）"""
    menu_ids = data.get("menu_ids", [])
    success = SysRoleService.assign_menus(role_id, menu_ids)
    if not success:
        return {"code": 500, "msg": "分配失败", "data": None}
    return {"code": 200, "msg": "分配成功", "data": None}
