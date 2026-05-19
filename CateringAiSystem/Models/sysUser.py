from datetime import datetime
from typing import Optional, ClassVar

from pydantic import Field

from Base.Repository.models.defaultDbModel import DefaultDbModel


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
