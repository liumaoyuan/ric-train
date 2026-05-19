from datetime import datetime
from typing import Optional, ClassVar

from pydantic import Field

from Base.Repository.models.defaultDbModel import DefaultDbModel


class SysMenu(DefaultDbModel):
    """菜单权限表（树形结构）"""
    table_alias: ClassVar[str] = "sys_menu"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{{table_name}}` (
        `id`              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '菜单ID',
        `parent_id`       BIGINT UNSIGNED NOT NULL DEFAULT 0      COMMENT '父菜单ID（0表示根节点）',
        `menu_name`       VARCHAR(100)    NOT NULL                 COMMENT '菜单名称',
        `menu_type`       TINYINT UNSIGNED NOT NULL DEFAULT 0      COMMENT '类型: 0=目录, 1=菜单, 2=按钮',
        `permission_code` VARCHAR(100)    DEFAULT NULL             COMMENT '权限标识（如 sys:user:add）',
        `path`            VARCHAR(200)    DEFAULT NULL             COMMENT '前端路由路径',
        `component`       VARCHAR(200)    DEFAULT NULL             COMMENT '前端组件路径',
        `icon`            VARCHAR(100)    DEFAULT NULL             COMMENT '菜单图标',
        `sort_order`      INT UNSIGNED    NOT NULL DEFAULT 0       COMMENT '排序序号（同级排序）',
        `status`          TINYINT UNSIGNED NOT NULL DEFAULT 1      COMMENT '状态: 0=禁用, 1=启用',
        `visible`         TINYINT UNSIGNED NOT NULL DEFAULT 1      COMMENT '显示: 0=隐藏, 1=显示',
        `created_at`      DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at`      DATETIME        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        `created_by`      BIGINT UNSIGNED DEFAULT NULL             COMMENT '创建人ID',
        `updated_by`      BIGINT UNSIGNED DEFAULT NULL             COMMENT '更新人ID',
        PRIMARY KEY (`id`),
        KEY `idx_parent_id` (`parent_id`),
        KEY `idx_menu_type` (`menu_type`),
        KEY `idx_status` (`status`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='菜单权限表';
    """

    id: Optional[int] = Field(None, description="菜单ID")
    parent_id: int = Field(0, description="父菜单ID(0表示根)")
    menu_name: str = Field(..., description="菜单名称")
    menu_type: int = Field(0, description="类型: 0目录 1菜单 2按钮")
    permission_code: Optional[str] = Field(None, description="权限标识")
    path: Optional[str] = Field(None, description="路由路径")
    component: Optional[str] = Field(None, description="组件路径")
    icon: Optional[str] = Field(None, description="图标")
    sort_order: int = Field(0, description="排序序号")
    status: int = Field(1, description="状态: 0禁用 1启用")
    visible: int = Field(1, description="显示: 0隐藏 1显示")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人ID")
    updated_by: Optional[int] = Field(None, description="更新人ID")
