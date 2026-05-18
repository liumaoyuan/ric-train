from datetime import datetime
from typing import Optional, ClassVar

from pydantic import Field

from Base.Repository.models.defaultDbModel import DefaultDbModel


class SysUser(DefaultDbModel):
    """系统用户表"""
    table_alias: ClassVar[str] = "sys_user"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{{{{table_name}}}}` (
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


class SysRole(DefaultDbModel):
    """角色表"""
    table_alias: ClassVar[str] = "sys_role"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{{{{table_name}}}}` (
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


class SysMenu(DefaultDbModel):
    """菜单权限表（树形结构）"""
    table_alias: ClassVar[str] = "sys_menu"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{{{{table_name}}}}` (
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


class SysRoleMenu(DefaultDbModel):
    """角色菜单关联表"""
    table_alias: ClassVar[str] = "sys_role_menu"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{{{{table_name}}}}` (
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


class SysUserRole(DefaultDbModel):
    """用户角色关联表"""
    table_alias: ClassVar[str] = "sys_user_role"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{{{{table_name}}}}` (
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
