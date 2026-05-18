from typing import Optional

from fastapi import APIRouter, Request, Query

from CateringAiSystem.Service.sysUserService import SysUserService
from CateringAiSystem.Utils.rbacUtils import get_current_user, require_permission

router = APIRouter(prefix="/api/v1/sys/user", tags=["用户管理"])


@router.get("/list")
@require_permission("sys:user:list")
def list_users(request: Request, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
               username: Optional[str] = None, status: Optional[int] = None):
    """用户分页列表"""
    data = SysUserService.get_list(page, page_size, username, status)
    return {"code": 200, "msg": "success", "data": data}


@router.get("/{user_id}")
@require_permission("sys:user:list")
def get_user(user_id: int, request: Request):
    """用户详情"""
    data = SysUserService.get_detail(user_id)
    if data is None:
        return {"code": 404, "msg": "用户不存在", "data": None}
    return {"code": 200, "msg": "success", "data": data}


@router.post("")
@require_permission("sys:user:add")
def create_user(data: dict, request: Request):
    """新增用户"""
    user = get_current_user(request)
    user_id = SysUserService.create(data, operator_id=user["user_id"])
    if user_id is None:
        return {"code": 400, "msg": "用户名已存在", "data": None}
    return {"code": 200, "msg": "创建成功", "data": {"id": user_id}}


@router.put("/{user_id}")
@require_permission("sys:user:edit")
def update_user(user_id: int, data: dict, request: Request):
    """编辑用户"""
    user = get_current_user(request)
    success = SysUserService.update(user_id, data, operator_id=user["user_id"])
    if not success:
        return {"code": 404, "msg": "用户不存在或更新失败", "data": None}
    return {"code": 200, "msg": "更新成功", "data": None}


@router.delete("/{user_id}")
@require_permission("sys:user:delete")
def delete_user(user_id: int, request: Request):
    """删除用户"""
    success = SysUserService.delete(user_id)
    if not success:
        return {"code": 404, "msg": "用户不存在或删除失败", "data": None}
    return {"code": 200, "msg": "删除成功", "data": None}


@router.put("/{user_id}/status")
@require_permission("sys:user:toggle")
def toggle_user_status(user_id: int, request: Request):
    """启用/禁用用户"""
    new_status = SysUserService.toggle_status(user_id)
    if new_status is None:
        return {"code": 404, "msg": "用户不存在", "data": None}
    return {"code": 200, "msg": "操作成功", "data": {"status": new_status}}


@router.put("/{user_id}/password")
@require_permission("sys:user:edit")
def reset_password(user_id: int, data: dict, request: Request):
    """重置密码"""
    new_password = data.get("password", "123456")
    success = SysUserService.reset_password(user_id, new_password)
    if not success:
        return {"code": 404, "msg": "用户不存在", "data": None}
    return {"code": 200, "msg": "密码重置成功", "data": None}


@router.get("/{user_id}/roles")
@require_permission("sys:user:list")
def get_user_roles(user_id: int, request: Request):
    """获取用户角色ID列表"""
    roles = SysUserService.get_roles(user_id)
    return {"code": 200, "msg": "success", "data": {"role_ids": roles}}


@router.put("/{user_id}/roles")
@require_permission("sys:user:assign-role")
def assign_user_roles(user_id: int, data: dict, request: Request):
    """分配用户角色（全量替换）"""
    role_ids = data.get("role_ids", [])
    success = SysUserService.assign_roles(user_id, role_ids)
    if not success:
        return {"code": 500, "msg": "分配失败", "data": None}
    return {"code": 200, "msg": "分配成功", "data": None}
