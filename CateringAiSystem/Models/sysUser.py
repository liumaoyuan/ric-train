import logging
from datetime import datetime
from typing import Optional, ClassVar

from pydantic import Field

from Base.Repository.models.defaultDbModel import DefaultDbModel

logger = logging.getLogger(__name__)


class SysUser(DefaultDbModel):
    """系统用户表"""
    table_alias: ClassVar[str] = "sys_user"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{{table_name}}` (
        `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
        `username`      VARCHAR(50)     NOT NULL                 COMMENT '用户名（登录用）',
        `password_hash` VARCHAR(255)    NOT NULL                 COMMENT '密码哈希（bcrypt）',
        `display_name`  VARCHAR(100)    DEFAULT NULL             COMMENT '显示名称（如姓名）',
        `phone`         VARCHAR(20)     DEFAULT NULL             COMMENT '手机号',
        `email`         VARCHAR(100)    DEFAULT NULL             COMMENT '邮箱',
        `avatar`        VARCHAR(255)    DEFAULT NULL             COMMENT '头像URL',
        `status`        TINYINT UNSIGNED NOT NULL DEFAULT 1      COMMENT '状态: 0=禁用, 1=启用',
        `remark`        VARCHAR(500)    DEFAULT NULL             COMMENT '备注',
        `created_at`    DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at`    DATETIME        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        `created_by`    BIGINT UNSIGNED DEFAULT NULL             COMMENT '创建人ID',
        `updated_by`    BIGINT UNSIGNED DEFAULT NULL             COMMENT '更新人ID',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uk_username` (`username`),
        KEY `idx_status` (`status`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统用户表';
    """

    id: Optional[int] = Field(None, description="用户ID")
    username: str = Field(..., description="用户名")
    password_hash: str = Field(..., description="密码哈希(bcrypt)")
    display_name: Optional[str] = Field(None, description="显示名称")
    phone: Optional[str] = Field(None, description="手机号")
    email: Optional[str] = Field(None, description="邮箱")
    avatar: Optional[str] = Field(None, description="头像URL")
    status: int = Field(1, description="状态: 0禁用 1启用")
    remark: Optional[str] = Field(None, description="备注")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人ID")
    updated_by: Optional[int] = Field(None, description="更新人ID")

    @classmethod
    def get_paginated_list(cls, page: int = 1, page_size: int = 20,
                           username: Optional[str] = None,
                           status: Optional[int] = None) -> dict:
        """分页查询用户列表"""
        try:
            db = cls.get_db_connection()
            if db is None:
                return {"total": 0, "page": page, "page_size": page_size, "data": []}

            table_name = cls.get_table_name_with_db()
            where_clauses = []
            params = []

            if username:
                where_clauses.append("`username` LIKE %s")
                params.append(f"%{username}%")
            if status is not None:
                where_clauses.append("`status` = %s")
                params.append(status)

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            count_sql = f"SELECT COUNT(*) AS total FROM {table_name} {where_sql}"
            count_result = db.execute(count_sql, tuple(params))
            total = count_result[0]["total"] if count_result else 0

            offset = (page - 1) * page_size
            list_sql = f"""SELECT `id`, `username`, `display_name`, `phone`, `email`,
`avatar`, `status`, `remark`, `created_at`, `updated_at`
FROM {table_name}
{where_sql}
ORDER BY `created_at` DESC
LIMIT {offset}, {page_size}"""
            results = db.execute(list_sql, tuple(params))

            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "data": results or [],
            }
        except Exception as e:
            logger.error(f"查询用户列表失败: {e}")
            return {"total": 0, "page": page, "page_size": page_size, "data": []}

    @classmethod
    def delete_cascade(cls, user_id: int) -> bool:
        """删除用户及其关联的角色"""
        try:
            db = cls.get_db_connection()
            if db is None:
                return False
            from .sysUserRole import SysUserRole
            ur_table = SysUserRole.get_table_name_with_db()
            db.execute(f"DELETE FROM {ur_table} WHERE `user_id` = %s", (user_id,), commit=True)
            return cls.delete_by_id(user_id)
        except Exception as e:
            logger.error(f"删除用户失败: {e}")
            return False

    @classmethod
    def assign_roles(cls, user_id: int, role_ids: list) -> bool:
        """全量替换用户角色"""
        try:
            db = cls.get_db_connection()
            if db is None:
                return False
            from .sysUserRole import SysUserRole
            table_name = SysUserRole.get_table_name_with_db()

            db.execute(f"DELETE FROM {table_name} WHERE `user_id` = %s", (user_id,), commit=True)

            if role_ids:
                values = ",".join([f"({user_id}, {rid})" for rid in role_ids])
                sql = f"INSERT INTO {table_name} (`user_id`, `role_id`) VALUES {values}"
                db.execute(sql, commit=True)

            return True
        except Exception as e:
            logger.error(f"分配角色失败: {e}")
            return False

    @classmethod
    def get_user_menu_ids(cls, user_id: int) -> set:
        """获取用户有权限的菜单ID集合"""
        try:
            from .sysUserRole import SysUserRole
            from .sysRoleMenu import SysRoleMenu
            db = cls.get_db_connection()
            if db is None:
                return set()

            ur_table = SysUserRole.get_table_name_with_db()
            rm_table = SysRoleMenu.get_table_name_with_db()

            sql = f"""SELECT DISTINCT rm.`menu_id`
FROM {ur_table} ur
JOIN {rm_table} rm ON rm.`role_id` = ur.`role_id`
WHERE ur.`user_id` = %s"""
            results = db.execute(sql, (user_id,))
            return set(row["menu_id"] for row in results) if results else set()
        except Exception as e:
            logger.error(f"获取用户菜单ID失败: {e}")
            return set()

    @classmethod
    def get_role_codes(cls, user_id: int) -> list:
        """获取用户的所有角色编码"""
        try:
            from .sysUserRole import SysUserRole
            from .sysRole import SysRole
            db = cls.get_db_connection()
            if db is None:
                return []
            ur_table = SysUserRole.get_table_name_with_db()
            role_table = SysRole.get_table_name_with_db()
            sql = f"""SELECT r.`role_code`
FROM {ur_table} ur
JOIN {role_table} r ON r.`id` = ur.`role_id`
WHERE ur.`user_id` = %s AND r.`status` = 1"""
            results = db.execute(sql, (user_id,))
            return [row["role_code"] for row in results] if results else []
        except Exception as e:
            logger.error(f"获取用户角色失败: {e}")
            return []

    @classmethod
    def get_permission_codes(cls, user_id: int) -> list:
        """获取用户的所有权限标识"""
        try:
            from .sysUserRole import SysUserRole
            from .sysRoleMenu import SysRoleMenu
            from .sysMenu import SysMenu
            db = cls.get_db_connection()
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
