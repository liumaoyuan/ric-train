import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { generateRoutes } from './dynamicRoutes'

// 固定路由 — 不依赖后端菜单，始终可访问
export const fixedRoutes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/login/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/401',
    name: 'NotAuth',
    component: () => import('../views/error/401.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('../views/error/404.vue'),
    meta: { requiresAuth: false },
  },
]

// 布局路由 — Dashboard 是固定子路由，其他由动态路由填充
const LAYOUT_NAME = 'Layout'

const layoutRoute = {
  path: '/',
  name: LAYOUT_NAME,
  component: () => import('../layout/MainLayout.vue'),
  meta: { requiresAuth: true },
  redirect: '/dashboard',
  children: [
    {
      path: 'dashboard',
      name: 'Dashboard',
      component: () => import('../views/dashboard/Dashboard.vue'),
      meta: { title: '首页' },
    },
  ],
}

const router = createRouter({
  history: createWebHistory(),
  routes: [...fixedRoutes, layoutRoute],
})

// 记录已添加的动态路由 name，用于重复添加时清理
let dynamicRouteNames = []

// 防止未匹配路由时无限重试
let _menuFetchRetried = false

/**
 * 根据 store 中的菜单树重建动态路由
 * 在登录完成或页面刷新时调用
 */
export function rebuildDynamicRoutes() {
  // 移除旧的动态路由
  dynamicRouteNames.forEach(name => {
    if (router.hasRoute(name)) {
      router.removeRoute(name)
    }
  })
  dynamicRouteNames = []

  const authStore = useAuthStore()
  if (!authStore.isLoggedIn) return

  const menuTree = authStore.menuTree
  if (!menuTree || menuTree.length === 0) return

  const children = generateRoutes(menuTree)
  children.forEach(route => {
    router.addRoute(LAYOUT_NAME, route)
    dynamicRouteNames.push(route.name)
  })
}

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 公开页面直接放行
  if (to.meta.requiresAuth === false) {
    next()
    return
  }

  // 未登录跳转登录页
  if (!authStore.isLoggedIn) {
    next('/login')
    return
  }

  // 确保动态路由已加载
  if (dynamicRouteNames.length === 0) {
    rebuildDynamicRoutes()

    if (dynamicRouteNames.length === 0) {
      try {
        await authStore.fetchMenus()
        rebuildDynamicRoutes()
      } catch {
        next('/dashboard')
        return
      }
    }

    next({ ...to, replace: true })
    return
  }

  // 权限校验
  const permission = to.meta.permission
  if (permission && !authStore.hasPermission(permission)) {
    next('/401')
    return
  }

  // 未匹配任何路由 → 尝试从后端重新获取菜单后重试，仍不匹配则 404
  if (to.matched.length === 0) {
    if (_menuFetchRetried) {
      _menuFetchRetried = false
      next({ name: 'NotFound' })
      return
    }
    _menuFetchRetried = true
    try {
      await authStore.fetchMenus()
      rebuildDynamicRoutes()
    } catch {
      _menuFetchRetried = false
      next({ name: 'NotFound' })
      return
    }
    // 路由已重建，重新解析目标路由
    next({ ...to, replace: true })
    return
  }

  next()
})

export default router
