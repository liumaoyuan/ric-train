-- ===========================================
-- 连锁餐饮 AI 系统 - 数据库表结构
-- 版本: V1.0
-- 说明: 营业数据、风评数据、智能备菜等业务表
-- ===========================================

-- 数据库创建（如不存在）
CREATE DATABASE IF NOT EXISTS catering_ai_system
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE catering_ai_system;

-- ===========================================
-- 1. 门店表
-- ===========================================
-- DROP TABLE IF EXISTS `store`;
CREATE TABLE `store` (
    `id`            INT             NOT NULL AUTO_INCREMENT  COMMENT '门店ID',
    `name`          VARCHAR(100)    NOT NULL                 COMMENT '门店名称',
    `province`      VARCHAR(50)     NOT NULL                 COMMENT '所在省份',
    `city`          VARCHAR(50)     NOT NULL                 COMMENT '所在城市',
    `district`      VARCHAR(50)     DEFAULT NULL             COMMENT '所在区/县',
    `address`       VARCHAR(200)    DEFAULT NULL             COMMENT '详细地址',
    `phone`         VARCHAR(20)     DEFAULT NULL             COMMENT '联系电话',
    `open_date`     DATE            DEFAULT NULL             COMMENT '开业日期',
    `status`        TINYINT         DEFAULT 1                COMMENT '状态: 1营业 0停业',
    `level`         TINYINT         DEFAULT 2                COMMENT '门店等级: 1旗舰 2标准 3简配',
    `created_at`    DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`    DATETIME        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_city` (`city`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='门店信息表';


-- ===========================================
-- 2. 菜品表
-- ===========================================
-- DROP TABLE IF EXISTS `dish`;
CREATE TABLE `dish` (
    `id`            INT             NOT NULL AUTO_INCREMENT  COMMENT '菜品ID',
    `name`          VARCHAR(100)    NOT NULL                 COMMENT '菜品名称',
    `category`      VARCHAR(50)     NOT NULL                 COMMENT '分类: 热菜/凉菜/主食/汤品/饮品/配菜',
    `price`         DECIMAL(10,2)   NOT NULL                 COMMENT '标准价格',
    `cost`          DECIMAL(10,2)   DEFAULT NULL             COMMENT '成本',
    `unit`          VARCHAR(10)     DEFAULT '份'             COMMENT '单位',
    `spicy_level`   TINYINT         DEFAULT 0                COMMENT '辣度: 0不辣 1微辣 2中辣 3重辣',
    `popularity`    INT             DEFAULT 50               COMMENT ' popularity 权重(用于生成销量)',
    `image_url`     VARCHAR(255)    DEFAULT NULL             COMMENT '图片URL',
    `status`        TINYINT         DEFAULT 1                COMMENT '状态: 1上架 0下架',
    `created_at`    DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='菜品信息表';


-- ===========================================
-- 3. 会员表（暂不实现，保留 DDL 供后续启用）
-- ===========================================
-- DROP TABLE IF EXISTS `member`;
CREATE TABLE `member` (
    `id`            INT             NOT NULL AUTO_INCREMENT  COMMENT '会员ID',
    `store_id`      INT             NOT NULL                 COMMENT '所属门店ID，关联 store.id',
    `name`          VARCHAR(50)     NOT NULL                 COMMENT '会员姓名',
    `phone`         VARCHAR(20)     DEFAULT NULL             COMMENT '手机号',
    `level`         TINYINT         DEFAULT 1                COMMENT '等级: 1普通 2银卡 3金卡 4钻石',
    `points`        INT             DEFAULT 0                COMMENT '积分',
    `total_spent`   DECIMAL(12,2)   DEFAULT 0.00             COMMENT '累计消费总额',
    `total_orders`  INT             DEFAULT 0                COMMENT '累计消费次数',
    `join_date`     DATE            NOT NULL                 COMMENT '注册日期',
    `status`        TINYINT         DEFAULT 1                COMMENT '状态: 1正常 0冻结',
    `created_at`    DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_store` (`store_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会员信息表';


-- ===========================================
-- 4. 堂食订单表
-- ===========================================
-- DROP TABLE IF EXISTS `order_item`;
-- DROP TABLE IF EXISTS `dine_in_order`;
CREATE TABLE `dine_in_order` (
    `id`                BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '订单ID',
    `store_id`          INT             NOT NULL                 COMMENT '门店ID，关联 store.id',
    `order_no`          VARCHAR(50)     NOT NULL                 COMMENT '订单号',
    `total_amount`      DECIMAL(10,2)   NOT NULL DEFAULT 0.00    COMMENT '订单总金额',
    `payment_method`    VARCHAR(20)     NOT NULL                 COMMENT '支付方式: 微信支付/支付宝支付/现金支付',
    `member_id`         INT             DEFAULT NULL             COMMENT '会员ID（关联 member.id），NULL表示非会员',
    `dish_count`        TINYINT         NOT NULL DEFAULT 0       COMMENT '菜品数量(1~4)',
    `order_time`        DATETIME        NOT NULL                 COMMENT '下单时间',
    `created_at`        DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_order_no` (`order_no`),
    KEY `idx_store_time` (`store_id`, `order_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='堂食订单表';


-- ===========================================
-- 5. 外卖订单表
-- ===========================================
-- DROP TABLE IF EXISTS `takeout_order`;
CREATE TABLE `takeout_order` (
    `id`                BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '订单ID',
    `store_id`          INT             NOT NULL                 COMMENT '门店ID，关联 store.id',
    `order_no`          VARCHAR(50)     NOT NULL                 COMMENT '订单号',
    `total_amount`      DECIMAL(10,2)   NOT NULL DEFAULT 0.00    COMMENT '订单总金额',
    `platform`          VARCHAR(20)     NOT NULL                 COMMENT '外卖平台: 美团/饿了么/抖音',
    `dish_count`        TINYINT         NOT NULL DEFAULT 0       COMMENT '菜品数量(1~4)',
    `order_time`        DATETIME        NOT NULL                 COMMENT '下单时间',
    `created_at`        DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_order_no` (`order_no`),
    KEY `idx_store_time` (`store_id`, `order_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外卖订单表';


-- ===========================================
-- 6. 订单菜品明细表
-- ===========================================
CREATE TABLE `order_item` (
    `id`            BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '明细ID',
    `order_id`      BIGINT          NOT NULL                 COMMENT '订单ID（关联堂食或外卖订单）',
    `store_id`      INT             NOT NULL                 COMMENT '门店ID，关联 store.id',
    `dish_id`       INT             NOT NULL                 COMMENT '菜品ID，关联 dish.id',
    `dish_name`     VARCHAR(100)    NOT NULL                 COMMENT '菜品名称',
    `quantity`      INT             NOT NULL DEFAULT 1        COMMENT '数量',
    `price`         DECIMAL(10,2)   NOT NULL                 COMMENT '单价',
    `amount`        DECIMAL(10,2)   NOT NULL                 COMMENT '小计金额',
    PRIMARY KEY (`id`),
    KEY `idx_order` (`order_id`),
    KEY `idx_store_dish` (`store_id`, `dish_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单菜品明细表';


-- ===========================================
-- 7. 营业汇总表（每日每店一条记录）
-- ===========================================
-- DROP TABLE IF EXISTS `daily_summary`;
CREATE TABLE `daily_summary` (
    `id`                BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '记录ID',
    `store_id`          INT             NOT NULL                 COMMENT '门店ID',
    `summary_date`      DATE            NOT NULL                 COMMENT '日期',
    `total_revenue`     DECIMAL(12,2)   NOT NULL DEFAULT 0.00    COMMENT '总营业额',
    `total_orders`      INT             NOT NULL DEFAULT 0        COMMENT '总订单数',
    `total_customers`   INT             NOT NULL DEFAULT 0        COMMENT '总顾客数',
    `avg_price`         DECIMAL(5,2)    NOT NULL DEFAULT 0.00     COMMENT '客单价',
    `dine_in_revenue`   DECIMAL(12,2)   NOT NULL DEFAULT 0.00     COMMENT '堂食收入',
    `takeout_revenue`   DECIMAL(12,2)   NOT NULL DEFAULT 0.00     COMMENT '外卖收入',
    `peak_hour_revenue` DECIMAL(12,2)   DEFAULT NULL              COMMENT '高峰时段收入(11:00-13:00, 18:00-20:00)',
    `dish_total_count`  INT             NOT NULL DEFAULT 0        COMMENT '菜品销售总份数',
    `is_holiday`        TINYINT         NOT NULL DEFAULT 0         COMMENT '是否节假日: 0否 1是',
    `created_at`        DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_store_date` (`store_id`, `summary_date`),
    KEY `idx_date` (`summary_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='营业汇总表';


-- ===========================================
-- 8. 评论表（风评分析）
-- ===========================================
-- DROP TABLE IF EXISTS `review`;
CREATE TABLE `review` (
    `id`            BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '评论ID',
    `store_id`      INT             NOT NULL                 COMMENT '门店ID，关联 store.id',
    `platform`      VARCHAR(20)     NOT NULL                 COMMENT '平台: 美团/饿了么/大众点评',
    `rating`        TINYINT         NOT NULL                 COMMENT '评分: 1-5星',
    `content`       TEXT            NOT NULL                 COMMENT '评论内容',
    `review_date`   DATE            NOT NULL                 COMMENT '评论日期',
    `review_time`   DATETIME        NOT NULL                 COMMENT '评论时间',
    `tags`          VARCHAR(500)    DEFAULT NULL             COMMENT '标签(逗号分隔)',
    `is_replied`    TINYINT         DEFAULT 0                COMMENT '是否已回复: 0否 1是',
    `reply_content` TEXT            DEFAULT NULL             COMMENT '回复内容',
    `is_positive`   TINYINT         DEFAULT 1                COMMENT '情感: 1正面 0中性 -1负面',
    `created_at`    DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_review_date` (`review_date`),
    KEY `idx_store_rating` (`store_id`, `rating`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论表';


-- ===========================================
-- 9. 库存表（智能备菜）（暂不实现）
-- ===========================================
-- -- DROP TABLE IF EXISTS `inventory`;
-- CREATE TABLE `inventory` (
--     `id`            INT             NOT NULL AUTO_INCREMENT  COMMENT '库存ID',
--     `store_id`      INT             NOT NULL                 COMMENT '门店ID',
--     `dish_id`       INT             NOT NULL                 COMMENT '菜品ID',
--     `current_stock` DECIMAL(10,2)   NOT NULL DEFAULT 0.00     COMMENT '当前库存(份)',
--     `min_stock`     DECIMAL(10,2)   NOT NULL DEFAULT 50.00    COMMENT '最低库存预警线',
--     `max_stock`     DECIMAL(10,2)   NOT NULL DEFAULT 500.00   COMMENT '最大库存容量',
--     `unit`          VARCHAR(10)     DEFAULT '份'              COMMENT '单位',
--     `update_time`   DATETIME        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
--     PRIMARY KEY (`id`),
--     UNIQUE KEY `uk_store_dish` (`store_id`, `dish_id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='库存表';


-- ===========================================
-- 10. 采购单表（智能备菜）（暂不实现）
-- ===========================================
-- -- DROP TABLE IF EXISTS `purchase_order`;
-- CREATE TABLE `purchase_order` (
--     `id`            INT             NOT NULL AUTO_INCREMENT  COMMENT '采购单ID',
--     `store_id`      INT             NOT NULL                 COMMENT '门店ID',
--     `order_no`      VARCHAR(50)     NOT NULL                 COMMENT '采购单号',
--     `supplier`      VARCHAR(100)    DEFAULT NULL             COMMENT '供应商',
--     `total_amount`  DECIMAL(12,2)   NOT NULL DEFAULT 0.00     COMMENT '总金额',
--     `status`        TINYINT         DEFAULT 0                COMMENT '状态: 0待审核 1已通过 2已到货 3已取消',
--     `order_date`    DATE            NOT NULL                 COMMENT '采购日期',
--     `remark`        VARCHAR(500)    DEFAULT NULL             COMMENT '备注',
--     `created_at`    DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
--     PRIMARY KEY (`id`),
--     UNIQUE KEY `uk_order_no` (`order_no`),
--     KEY `idx_store_date` (`store_id`, `order_date`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='采购单表';


-- ===========================================
-- 11. 采购明细表（暂不实现）
-- ===========================================
-- -- DROP TABLE IF EXISTS `purchase_order_item`;
-- CREATE TABLE `purchase_order_item` (
--     `id`                INT             NOT NULL AUTO_INCREMENT  COMMENT '明细ID',
--     `purchase_order_id` INT             NOT NULL                 COMMENT '采购单ID',
--     `dish_id`           INT             NOT NULL                 COMMENT '菜品ID',
--     `quantity`          DECIMAL(10,2)   NOT NULL                 COMMENT '采购数量',
--     `price`             DECIMAL(10,2)   NOT NULL                 COMMENT '单价',
--     `amount`            DECIMAL(12,2)   NOT NULL                 COMMENT '小计金额',
--     PRIMARY KEY (`id`),
--     KEY `idx_purchase_order` (`purchase_order_id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='采购明细表';


-- ===========================================
-- 12. 用户表（RBAC权限系统）
-- ===========================================
-- DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
    `id`            INT             NOT NULL AUTO_INCREMENT  COMMENT '用户ID',
    `username`      VARCHAR(50)     NOT NULL                 COMMENT '用户名',
    `password_hash` VARCHAR(255)    NOT NULL                 COMMENT '密码哈希',
    `display_name`  VARCHAR(100)    DEFAULT NULL             COMMENT '显示名称',
    `role`          VARCHAR(20)     NOT NULL                 COMMENT '角色: boss/employee/franchisee',
    `store_id`      INT             DEFAULT NULL             COMMENT '关联门店(boss/employee可为null)，关联 store.id',
    `phone`         VARCHAR(20)     DEFAULT NULL             COMMENT '手机号',
    `email`         VARCHAR(100)    DEFAULT NULL             COMMENT '邮箱',
    `status`        TINYINT         DEFAULT 1                COMMENT '状态: 1启用 0禁用',
    `last_login`    DATETIME        DEFAULT NULL             COMMENT '最后登录时间',
    `created_at`    DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';


