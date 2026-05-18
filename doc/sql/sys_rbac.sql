-- ===========================================
-- 连锁餐饮 AI 系统 - RBAC 权限管理表结构
-- 版本: V1.0
-- 说明: 系统管理模块 RBAC 五张表
-- 数据库: catering_ai_system（通过 Base 框架自动建表，此文件仅作参考和手动执行用）
-- ===========================================

-- 数据库创建（如不存在）
CREATE DATABASE IF NOT EXISTS `catering_ai_system`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE `catering_ai_system`;

-- ===========================================
-- 1. sys_user — 系统用户表
-- 说明: 存储登录账号信息，密码使用 bcrypt 哈希加密
-- ===========================================
-- DROP TABLE IF EXISTS `sys_user`;
CREATE TABLE IF NOT EXISTS `sys_user` (
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


-- ===========================================
-- 2. sys_role — 角色表
-- 说明: 角色定义，通过 role_code 唯一标识
-- ===========================================
-- DROP TABLE IF EXISTS `sys_role`;
CREATE TABLE IF NOT EXISTS `sys_role` (
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


-- ===========================================
-- 3. sys_menu — 菜单权限表
-- 说明: 树形组织（parent_id 自关联），含目录/菜单/按钮三种类型
-- ===========================================
-- DROP TABLE IF EXISTS `sys_menu`;
CREATE TABLE IF NOT EXISTS `sys_menu` (
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


-- ===========================================
-- 4. sys_role_menu — 角色菜单关联表
-- 说明: 角色与菜单的多对多关系
-- ===========================================
-- DROP TABLE IF EXISTS `sys_role_menu`;
CREATE TABLE IF NOT EXISTS `sys_role_menu` (
    `id`       BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '关联ID',
    `role_id`  BIGINT UNSIGNED NOT NULL                 COMMENT '角色ID（关联 sys_role.id）',
    `menu_id`  BIGINT UNSIGNED NOT NULL                 COMMENT '菜单ID（关联 sys_menu.id）',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_role_menu` (`role_id`, `menu_id`),
    KEY `idx_menu_id` (`menu_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色菜单关联表';


-- ===========================================
-- 5. sys_user_role — 用户角色关联表
-- 说明: 用户与角色的多对多关系
-- ===========================================
-- DROP TABLE IF EXISTS `sys_user_role`;
CREATE TABLE IF NOT EXISTS `sys_user_role` (
    `id`      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '关联ID',
    `user_id` BIGINT UNSIGNED NOT NULL                 COMMENT '用户ID（关联 sys_user.id）',
    `role_id` BIGINT UNSIGNED NOT NULL                 COMMENT '角色ID（关联 sys_role.id）',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_role` (`user_id`, `role_id`),
    KEY `idx_role_id` (`role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色关联表';


-- ===========================================
-- 预置数据 — 三个基础角色
-- ===========================================
INSERT INTO `sys_role` (`role_name`, `role_code`, `description`, `sort_order`) VALUES
('老板', 'admin', '系统最高权限，可访问所有功能模块', 1),
('普通员工', 'employee', '内部员工，拥有部分运营模块权限', 2),
('加盟商', 'franchisee', '加盟商用户，仅本门店数据', 3);


-- ===========================================
-- 预置数据 — 管理员用户（密码: admin123）
-- 密码哈希通过代码生成，此处为占位，实际通过 init 脚本写入
-- ===========================================
-- INSERT INTO `sys_user` (`username`, `password_hash`, `display_name`, `status`) VALUES
-- ('admin', '<由代码生成的 bcrypt hash>', '系统管理员', 1);
