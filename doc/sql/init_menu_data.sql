-- ===========================================
-- 连锁餐饮 AI 系统 - 菜单初始化数据
-- 版本: V1.0
-- 说明: 基于开发计划文档的完整菜单树 + 三员角色菜单权限分配
-- 数据库: ric_ai_base.sys_menu / sys_role_menu
-- ===========================================

-- ===========================================
-- 注意：先清空已有数据（避免重复插入冲突）
-- ===========================================
-- DELETE FROM sys_role_menu;
-- DELETE FROM sys_menu;

-- ===========================================
-- 一级目录（parent_id = 0）
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `path`, `component`, `icon`, `sort_order`, `visible`, `status`) VALUES
(1, 0, '首页', 1, NULL, NULL, 'views/dashboard/Dashboard.vue', 'HomeFilled', 1, 1, 1),
(2, 0, '数据中心',   0, 'menu:data',       NULL,   NULL,                  'DataBoard',  2, 1, 1),
(3, 0, '运营中心',   0, 'menu:operation',  NULL,   NULL,                  'Tools',      3, 1, 1),
(4, 0, '智能助手',   0, 'menu:chat',       NULL,   NULL,                  'ChatDotRound',4, 1, 1),
(5, 0, '系统管理',   0, 'menu:system',     NULL,   NULL,                  'Setting',    5, 1, 1);

-- ===========================================
-- 二级 — 数据中心
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `path`, `component`, `icon`, `sort_order`, `visible`, `status`) VALUES
(20, 2, '原始数据',   0, 'data:raw',       NULL,   NULL,                  'List',        1, 1, 1),
(21, 2, '营业分析',   1, 'analysis:sales',       '/analysis/sales',     'views/analysis/Sales.vue',      'TrendCharts', 2, 1, 1),
(22, 2, '行业分析',   1, 'analysis:industry',    '/analysis/industry',  'views/analysis/Industry.vue',   'DataAnalysis',3, 1, 1);

-- ===========================================
-- 三级 — 原始数据子菜单
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `path`, `component`, `icon`, `sort_order`, `visible`, `status`) VALUES
(205, 20, '堂食订单', 1, 'data:dine-in:list',   '/data/dine-in-orders',   'views/data/DineInOrderList.vue',    'CoffeeCup',   1, 1, 1),
(206, 20, '外卖订单', 1, 'data:takeout:list', '/data/takeout-orders',  'views/data/TakeoutOrderList.vue',   'TakeoutBox',  2, 1, 1),
(201, 20, '营业汇总', 1, 'data:summary:list', '/data/summary',  'views/data/SummaryList.vue',  'DataBoard',   3, 1, 1),
(202, 20, '菜品管理', 1, 'data:dish:list',    '/data/dishes',   'views/data/DishList.vue',     'Apple',       4, 1, 1),
(203, 20, '门店管理', 1, 'data:store:list',   '/data/stores',   'views/data/StoreList.vue',    'OfficeBuilding',5,1, 1),
(204, 20, '评论查看', 1, 'data:review:list',  '/data/reviews',  'views/data/ReviewList.vue',   'ChatLineSquare',6,1, 1);

-- ===========================================
-- 四级 — 堂食订单按钮
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `sort_order`) VALUES
(2050, 205, '查询列表', 2, 'data:dine-in:list',   1),
(2051, 205, '查看详情', 2, 'data:dine-in:detail', 2);

-- ===========================================
-- 四级 — 外卖订单按钮
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `sort_order`) VALUES
(2060, 206, '查询列表', 2, 'data:takeout:list',   1),
(2061, 206, '查看详情', 2, 'data:takeout:detail', 2);

-- 营业汇总按钮
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `sort_order`) VALUES
(2010, 201, '查询列表', 2, 'data:summary:list', 1);

-- 菜品管理按钮
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `sort_order`) VALUES
(2020, 202, '查询列表', 2, 'data:dish:list',   1),
(2021, 202, '查看详情', 2, 'data:dish:detail', 2);

-- 门店管理按钮
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `sort_order`) VALUES
(2030, 203, '查询列表', 2, 'data:store:list',   1),
(2031, 203, '查看详情', 2, 'data:store:detail', 2);

-- 评论查看按钮
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `sort_order`) VALUES
(2040, 204, '查询列表', 2, 'data:review:list',   1),
(2041, 204, '查看详情', 2, 'data:review:detail', 2);

-- ===========================================
-- 四级 — 营业分析按钮
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `sort_order`) VALUES
(2100, 21, '数据查询', 2, 'analysis:sales:query',      1),
(2101, 21, '生成报告', 2, 'analysis:report:generate',  2),
(2102, 21, '同比环比', 2, 'analysis:compare:view',     3),
(2103, 21, '趋势预测', 2, 'analysis:trend:view',       4);

-- ===========================================
-- 四级 — 行业分析按钮
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `sort_order`) VALUES
(2200, 22, '联网搜索', 2, 'analysis:industry:search', 1),
(2201, 22, '生成报告', 2, 'analysis:industry:report', 2);

-- ===========================================
-- 二级 — 运营中心
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `path`, `component`, `icon`, `sort_order`, `visible`, `status`) VALUES
(30, 3, '风评分析',   1, 'review:overview',   '/review',      'views/review/ReviewList.vue',     'ChatLineSquare', 1, 1, 1),
(31, 3, '知识库',     1, 'knowledge:overview','/knowledge',   'views/knowledge/KnowledgeList.vue','FolderOpened',   2, 1, 1),
(32, 3, '加盟商培训', 1, 'training:overview', '/training',    'views/training/TrainingList.vue', 'Reading',        3, 1, 1),
(33, 3, '素材中心',   1, 'material:overview', '/material',    'views/material/MaterialList.vue', 'PictureFilled',  4, 1, 1),
(34, 3, '选址评估',   1, 'location:overview', '/location',    'views/location/LocationList.vue', 'MapLocation',    5, 1, 1);

-- ===========================================
-- 三级 — 风评分析按钮
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `sort_order`) VALUES
(3000, 30, '评论列表', 2, 'review:list',      1),
(3001, 30, '情感分析', 2, 'review:sentiment', 2),
(3002, 30, '标签提取', 2, 'review:tags',      3),
(3003, 30, '生成回复', 2, 'review:reply',     4),
(3004, 30, '差评预警', 2, 'review:warning',   5);

-- ===========================================
-- 三级 — 知识库按钮
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `sort_order`) VALUES
(3100, 31, '上传文档',   2, 'knowledge:upload',    1),
(3101, 31, '文档列表',   2, 'knowledge:list',      2),
(3102, 31, '编辑文档',   2, 'knowledge:edit',      3),
(3103, 31, '删除文档',   2, 'knowledge:delete',    4),
(3104, 31, '预览分块',   2, 'knowledge:preview',   5),
(3105, 31, '确认向量化', 2, 'knowledge:vectorize', 6),
(3106, 31, '重新处理',   2, 'knowledge:reprocess', 7);

-- ===========================================
-- 三级 — 加盟商培训按钮
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `sort_order`) VALUES
(3200, 32, '课程管理', 2, 'training:course:manage',  1),
(3201, 32, '进度查看', 2, 'training:progress:view',  2),
(3202, 32, '在线考核', 2, 'training:exam:manage',    3);

-- ===========================================
-- 三级 — 素材中心按钮
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `sort_order`) VALUES
(3300, 33, '菜品生图',   2, 'material:generate-image', 1),
(3301, 33, '视频生成',   2, 'material:generate-video', 2),
(3302, 33, '上传素材',   2, 'material:upload',         3),
(3303, 33, '素材列表',   2, 'material:list',           4),
(3304, 33, '删除素材',   2, 'material:delete',         5);

-- ===========================================
-- 三级 — 选址评估按钮
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `sort_order`) VALUES
(3400, 34, '商圈分析', 2, 'location:analysis', 1),
(3401, 34, '生成报告', 2, 'location:report',   2);

-- ===========================================
-- 二级 — 智能助手
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `path`, `component`, `icon`, `sort_order`, `visible`, `status`) VALUES
(40, 4, 'AI 聊天助手', 1, 'chat:overview', '/chat', 'views/chat/ChatView.vue', 'ChatDotRound', 1, 1, 1);

-- ===========================================
-- 三级 — AI 聊天助手按钮
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `sort_order`) VALUES
(4000, 40, '发送消息',   2, 'chat:send',            1),
(4001, 40, '会话管理',   2, 'chat:session:manage',  2),
(4002, 40, '联网搜索',   2, 'chat:web-search',      3);

-- ===========================================
-- 二级 — 系统管理
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `path`, `component`, `icon`, `sort_order`, `visible`, `status`) VALUES
(50, 5, '用户管理', 1, 'sys:user:overview', '/system/user', 'views/sys/user/UserList.vue', 'User',   1, 1, 1),
(51, 5, '角色管理', 1, 'sys:role:overview', '/system/role', 'views/sys/role/RoleList.vue', 'Avatar', 2, 1, 1),
(52, 5, '菜单管理', 1, 'sys:menu:overview', '/system/menu', 'views/sys/menu/MenuList.vue', 'Menu',   3, 1, 1),
(53, 5, '定时任务', 1, 'sys:task:overview', '/system/task', 'views/sys/task/TaskList.vue', 'Timer',  4, 1, 1);

-- ===========================================
-- 三级 — 用户管理按钮
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `sort_order`) VALUES
(5000, 50, '查询',     2, 'sys:user:list',        1),
(5001, 50, '新增',     2, 'sys:user:add',         2),
(5002, 50, '编辑',     2, 'sys:user:edit',        3),
(5003, 50, '删除',     2, 'sys:user:delete',      4),
(5004, 50, '启停',     2, 'sys:user:toggle',      5),
(5005, 50, '分配角色', 2, 'sys:user:assign-role', 6);

-- ===========================================
-- 三级 — 角色管理按钮
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `sort_order`) VALUES
(5100, 51, '查询',     2, 'sys:role:list',         1),
(5101, 51, '新增',     2, 'sys:role:add',          2),
(5102, 51, '编辑',     2, 'sys:role:edit',         3),
(5103, 51, '删除',     2, 'sys:role:delete',       4),
(5104, 51, '启停',     2, 'sys:role:toggle',       5),
(5105, 51, '分配菜单', 2, 'sys:role:assign-menu',  6);

-- ===========================================
-- 三级 — 菜单管理按钮
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `sort_order`) VALUES
(5200, 52, '查询', 2, 'sys:menu:list', 1),
(5201, 52, '新增', 2, 'sys:menu:add',  2),
(5202, 52, '编辑', 2, 'sys:menu:edit', 3),
(5203, 52, '删除', 2, 'sys:menu:delete', 4);

-- ===========================================
-- 三级 — 定时任务按钮
-- ===========================================
INSERT INTO `sys_menu` (`id`, `parent_id`, `menu_name`, `menu_type`, `permission_code`, `sort_order`) VALUES
(5300, 53, '查询',     2, 'sys:task:list',   1),
(5301, 53, '新增',     2, 'sys:task:add',    2),
(5302, 53, '编辑',     2, 'sys:task:edit',   3),
(5303, 53, '删除',     2, 'sys:task:delete', 4),
(5304, 53, '执行一次', 2, 'sys:task:run',    5),
(5305, 53, '启停',     2, 'sys:task:toggle', 6);

-- ===========================================
-- 角色-菜单权限分配
-- 预置角色ID: 1=老板(admin), 2=普通员工(employee), 3=加盟商(franchisee)
-- ===========================================

-- -------------------------------------------
-- 1. 老板（admin）— 全部菜单
-- -------------------------------------------
# INSERT INTO `sys_role_menu` (`role_id`, `menu_id`)
# SELECT 1, `id` FROM `sys_menu`;
#
# -- -------------------------------------------
# -- 2. 普通员工（employee）
# --    可见范围：除系统管理外的全部菜单
# -- -------------------------------------------
# INSERT INTO `sys_role_menu` (`role_id`, `menu_id`) VALUES
# -- 工作台
# (2, 1), (2, 10),
# -- 数据中心目录 + 原始数据目录
# (2, 2), (2, 20),
# -- 堂食订单及其按钮
# (2, 205), (2, 2050), (2, 2051),
# -- 外卖订单及其按钮
# (2, 206), (2, 2060), (2, 2061),
# -- 营业汇总及其按钮
# (2, 201), (2, 2010),
# -- 菜品管理及其按钮
# (2, 202), (2, 2020), (2, 2021),
# -- 门店管理及其按钮
# (2, 203), (2, 2030), (2, 2031),
# -- 评论查看及其按钮
# (2, 204), (2, 2040), (2, 2041),
# -- 营业分析及其按钮
# (2, 21), (2, 2100), (2, 2101), (2, 2102), (2, 2103),
# -- 行业分析及其按钮
# (2, 22), (2, 2200), (2, 2201),
# -- 运营中心目录
# (2, 3),
# -- 风评分析及其按钮
# (2, 30), (2, 3000), (2, 3001), (2, 3002), (2, 3003), (2, 3004),
# -- 知识库及其按钮
# (2, 31), (2, 3100), (2, 3101), (2, 3102), (2, 3103), (2, 3104), (2, 3105), (2, 3106),
# -- 加盟商培训及其按钮
# (2, 32), (2, 3200), (2, 3201), (2, 3202),
# -- 素材中心及其按钮
# (2, 33), (2, 3300), (2, 3301), (2, 3302), (2, 3303), (2, 3304),
# -- 选址评估及其按钮
# (2, 34), (2, 3400), (2, 3401),
# -- 智能助手目录 + AI聊天助手及其按钮
# (2, 4), (2, 40), (2, 4000), (2, 4001), (2, 4002);
#
# -- -------------------------------------------
# -- 3. 加盟商（franchisee）
# --    可见范围：工作台 + 数据中心(不含门店管理/行业分析) +
# --    运营中心(风评+知识库+培训, 不含素材/选址) + 智能助手
# -- -------------------------------------------
# INSERT INTO `sys_role_menu` (`role_id`, `menu_id`) VALUES
# -- 工作台
# (3, 1), (3, 10),
# -- 数据中心目录 + 原始数据目录
# (3, 2), (3, 20),
# -- 堂食订单及其按钮
# (3, 205), (3, 2050), (3, 2051),
# -- 外卖订单及其按钮
# (3, 206), (3, 2060), (3, 2061),
# -- 营业汇总及其按钮
# (3, 201), (3, 2010),
# -- 菜品管理及其按钮
# (3, 202), (3, 2020), (3, 2021),
# -- 评论查看及其按钮
# (3, 204), (3, 2040), (3, 2041),
# -- 营业分析及其按钮
# (3, 21), (3, 2100), (3, 2101), (3, 2102), (3, 2103),
# -- 运营中心目录
# (3, 3),
# -- 风评分析及其按钮
# (3, 30), (3, 3000), (3, 3001), (3, 3002), (3, 3003), (3, 3004),
# -- 知识库及其按钮
# (3, 31), (3, 3100), (3, 3101), (3, 3102), (3, 3103), (3, 3104), (3, 3105), (3, 3106),
# -- 加盟商培训及其按钮
# (3, 32), (3, 3200), (3, 3201), (3, 3202),
# -- 智能助手目录 + AI聊天助手及其按钮
# (3, 4), (3, 40), (3, 4000), (3, 4001);
