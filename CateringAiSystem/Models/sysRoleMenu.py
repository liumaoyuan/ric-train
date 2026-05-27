from typing import Optional, ClassVar

from pydantic import Field

from Base.Repository.models.defaultDbModel import DefaultDbModel


class SysRoleMenu(DefaultDbModel):
    """角色菜单关联表"""
    table_alias: ClassVar[str] = "sys_role_menu"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{table_alias}` (
        `id`       BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '关联ID',
        `role_id`  BIGINT UNSIGNED NOT NULL                 COMMENT '角色ID（关联 sys_role.id）',
        `menu_id`  BIGINT UNSIGNED NOT NULL                 COMMENT '菜单ID（关联 sys_menu.id）',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uk_role_menu` (`role_id`, `menu_id`),
        KEY `idx_menu_id` (`menu_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色菜单关联表';
    """

    id: Optional[int] = Field(None, description="关联ID")
    role_id: int = Field(..., description="角色ID")
    menu_id: int = Field(..., description="菜单ID")
