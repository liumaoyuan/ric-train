import logging
from datetime import datetime
from typing import Optional, ClassVar

from pydantic import Field

from Base.Repository.models.defaultDbModel import DefaultDbModel

logger = logging.getLogger(__name__)


class SysRole(DefaultDbModel):
    """角色表"""
    table_alias: ClassVar[str] = "sys_role"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{{table_name}}` (
        `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '角色ID',
        `role_name`   VARCHAR(50)     NOT NULL                 COMMENT '角色名称（显示用）',
        `role_code`   VARCHAR(50)     NOT NULL                 COMMENT '角色编码（如 admin, employee, franchisee）',
        `description` VARCHAR(255)    DEFAULT NULL             COMMENT '角色描述',
        `status`      TINYINT UNSIGNED NOT NULL DEFAULT 1      COMMENT '状态: 0=禁用, 1=启用',
        `sort_order`  INT UNSIGNED    NOT NULL DEFAULT 0       COMMENT '排序序号（越小越靠前）',
        `created_at`  DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at`  DATETIME        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        `created_by`  BIGINT UNSIGNED DEFAULT NULL             COMMENT '创建人ID',
        `updated_by`  BIGINT UNSIGNED DEFAULT NULL             COMMENT '更新人ID',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uk_role_code` (`role_code`),
        KEY `idx_status` (`status`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';
    """

    id: Optional[int] = Field(None, description="角色ID")
    role_name: str = Field(..., description="角色名称")
    role_code: str = Field(..., description="角色编码")
    description: Optional[str] = Field(None, description="角色描述")
    status: int = Field(1, description="状态: 0禁用 1启用")
    sort_order: int = Field(0, description="排序序号")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人ID")
    updated_by: Optional[int] = Field(None, description="更新人ID")

    @classmethod
    def get_paginated_list(cls, page: int = 1, page_size: int = 20,
                           role_name: Optional[str] = None,
                           status: Optional[int] = None) -> dict:
        """分页查询角色列表"""
        try:
            db = cls.get_db_connection()
            if db is None:
                return {"total": 0, "page": page, "page_size": page_size, "data": []}

            table_name = cls.get_table_name_with_db()
            where_clauses = []
            params = []

            if role_name:
                where_clauses.append("`role_name` LIKE %s")
                params.append(f"%{role_name}%")
            if status is not None:
                where_clauses.append("`status` = %s")
                params.append(status)

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            count_sql = f"SELECT COUNT(*) AS total FROM {table_name} {where_sql}"
            count_result = db.execute(count_sql, tuple(params))
            total = count_result[0]["total"] if count_result else 0

            offset = (page - 1) * page_size
            list_sql = f"""SELECT * FROM {table_name}
{where_sql}
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

    @classmethod
    def delete_cascade(cls, role_id: int) -> dict:
        """删除角色及其关联（检查用户关联 + 删除菜单关联）"""
        try:
            db = cls.get_db_connection()
            if db is None:
                return {"success": False, "message": "数据库连接失败"}

            from .sysUserRole import SysUserRole
            from .sysRoleMenu import SysRoleMenu

            user_links = SysUserRole.find_by(role_id=role_id)
            if user_links:
                return {"success": False, "message": f"该角色下存在 {len(user_links)} 个关联用户，无法删除"}

            rm_table = SysRoleMenu.get_table_name_with_db()
            db.execute(f"DELETE FROM {rm_table} WHERE `role_id` = %s", (role_id,), commit=True)

            cls.delete_by_id(role_id)
            return {"success": True, "message": "删除成功"}
        except Exception as e:
            logger.error(f"删除角色失败: {e}")
            return {"success": False, "message": f"删除失败: {e}"}

    @classmethod
    def assign_menus(cls, role_id: int, menu_ids: list) -> bool:
        """全量替换角色的菜单权限"""
        try:
            db = cls.get_db_connection()
            if db is None:
                return False

            from .sysRoleMenu import SysRoleMenu
            table_name = SysRoleMenu.get_table_name_with_db()

            db.execute(f"DELETE FROM {table_name} WHERE `role_id` = %s", (role_id,), commit=True)

            if menu_ids:
                values = ",".join([f"({role_id}, {mid})" for mid in menu_ids])
                sql = f"INSERT INTO {table_name} (`role_id`, `menu_id`) VALUES {values}"
                db.execute(sql, commit=True)

            return True
        except Exception as e:
            logger.error(f"分配菜单权限失败: {e}")
            return False
