from typing import Optional, ClassVar

from pydantic import Field

from Base.Repository.models.defaultDbModel import DefaultDbModel


class SysUserRole(DefaultDbModel):
    """用户角色关联表"""
    table_alias: ClassVar[str] = "sys_user_role"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{{table_name}}` (
        `id`      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '关联ID',
        `user_id` BIGINT UNSIGNED NOT NULL                 COMMENT '用户ID（关联 sys_user.id）',
        `role_id` BIGINT UNSIGNED NOT NULL                 COMMENT '角色ID（关联 sys_role.id）',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uk_user_role` (`user_id`, `role_id`),
        KEY `idx_role_id` (`role_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色关联表';
    """

    id: Optional[int] = Field(None, description="关联ID")
    user_id: int = Field(..., description="用户ID")
    role_id: int = Field(..., description="角色ID")
