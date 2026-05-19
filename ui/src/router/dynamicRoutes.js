// 组件路径映射表：数据库中的 component 路径 → 实际 Vue 组件导入
const componentMap = {
  'views/dashboard/Dashboard.vue': () => import('../views/dashboard/Dashboard.vue'),
  'views/sys/user/UserList.vue': () => import('../views/sys/user/UserList.vue'),
  'views/sys/role/RoleList.vue': () => import('../views/sys/role/RoleList.vue'),
  'views/sys/menu/MenuList.vue': () => import('../views/sys/menu/MenuList.vue'),
}

const TYPE_MENU = 1

/**
 * 将后端菜单树递归转换为 vue-router 子路由配置
 * 仅 menu_type === 1（菜单/页面）生成实际路由
 * 必须递归遍历子节点，因为菜单树是多层嵌套结构
 */
export function generateRoutes(menuTree) {
  const routes = []
  for (const menu of menuTree) {
    // 类型为菜单且有组件路径 → 生成路由
    if (menu.menu_type === TYPE_MENU && menu.component) {
      const componentFn = componentMap[menu.component]
      if (!componentFn) continue

      // 子路由路径去掉前导 /
      const path = menu.path ? menu.path.replace(/^\//, '') : ''

      const route = {
        path,
        name: menu.permission_code || path.replace(/\//g, '_') || `menu_${menu.id}`,
        component: componentFn,
        meta: {
          title: menu.menu_name,
          icon: menu.icon || null,
          permission: menu.permission_code || null,
          menuId: menu.id,
        },
      }
      routes.push(route)
    }

    // 递归遍历子节点（目录/菜单都可能包含子节点）
    if (menu.children && menu.children.length > 0) {
      routes.push(...generateRoutes(menu.children))
    }
  }
  return routes
}

/**
 * 过滤菜单树用于侧边栏渲染
 * 递归处理，移除隐藏/禁用/按钮类型/空目录
 */
export function filterMenuTree(menuTree) {
  if (!menuTree || !Array.isArray(menuTree)) return []
  return menuTree
    .filter(menu => menu.visible !== 0 && menu.status === 1 && menu.menu_type !== 2)
    .map(menu => ({
      ...menu,
      children: menu.children ? filterMenuTree(menu.children) : [],
    }))
    .filter(menu => menu.menu_type !== 0 || menu.children.length > 0)
}
