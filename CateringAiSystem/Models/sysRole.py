from datetime import datetime
from typing import Optional, ClassVar

from pydantic import Field

from Base.Repository.models.defaultDbModel import DefaultDbModel


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
