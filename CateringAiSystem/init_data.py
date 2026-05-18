"""
系统初始化脚本 — 创建默认管理员和预置角色

运行方式：python -m CateringAiSystem.init_data
"""
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from CateringAiSystem.Models.sysModels import SysUser, SysRole, SysUserRole
from CateringAiSystem.Utils.authUtils import hash_password


def init():
    """运行系统初始化"""
    logger.info("=" * 50)
    logger.info("开始系统初始化...")
    logger.info("=" * 50)

    # 1. 创建预置角色
    roles_data = [
        ("admin", "老板", "系统最高权限，可访问所有功能模块", 1),
        ("employee", "普通员工", "内部员工，拥有部分运营模块权限", 2),
        ("franchisee", "加盟商", "加盟商用户，仅本门店数据", 3),
    ]
    role_ids = {}
    for code, name, desc, sort in roles_data:
        role = SysRole.find_one_by(role_code=code)
        if role:
            role_ids[code] = role.id
            logger.info(f"  角色 [{name}] 已存在 (id={role.id})")
        else:
            r = SysRole(role_name=name, role_code=code, description=desc, sort_order=sort, status=1)
            rid = r.save()
            role_ids[code] = rid
            logger.info(f"  创建角色 [{name}] (id={rid})")

    # 2. 创建默认管理员
    admin = SysUser.find_one_by(username="admin")
    if admin:
        admin_id = admin.id
        logger.info(f"  管理员 admin 已存在 (id={admin_id})")
    else:
        u = SysUser(
            username="admin",
            password_hash=hash_password("admin123"),
            display_name="系统管理员",
            status=1,
            remark="系统默认管理员",
        )
        admin_id = u.save()
        logger.info(f"  创建管理员 admin (id={admin_id}, password=admin123)")

    # 3. 为管理员分配老板角色
    if admin_id and role_ids.get("admin"):
        link = SysUserRole.find_one_by(user_id=admin_id, role_id=role_ids["admin"])
        if not link:
            ur = SysUserRole(user_id=admin_id, role_id=role_ids["admin"])
            ur.save()
            logger.info(f"  管理员关联角色 [老板] 成功")

    logger.info("=" * 50)
    logger.info("初始化完成！默认登录: admin / admin123")
    logger.info("=" * 50)


if __name__ == "__main__":
    init()
