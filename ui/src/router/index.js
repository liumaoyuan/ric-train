import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../store/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/login/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
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
      {
        path: 'sys/user',
        name: 'SysUser',
        component: () => import('../views/sys/user/UserList.vue'),
        meta: { title: '用户管理', permission: 'sys:user:list' },
      },
      {
        path: 'sys/role',
        name: 'SysRole',
        component: () => import('../views/sys/role/RoleList.vue'),
        meta: { title: '角色管理', permission: 'sys:role:list' },
      },
      {
        path: 'sys/menu',
        name: 'SysMenu',
        component: () => import('../views/sys/menu/MenuList.vue'),
        meta: { title: '菜单管理', permission: 'sys:menu:list' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth === false) {
    next()
    return
  }

  if (!authStore.isLoggedIn) {
    next('/login')
    return
  }

  // 检查页面级权限
  const permission = to.meta.permission
  if (permission && !authStore.hasPermission(permission)) {
    next('/dashboard')
    return
  }

  next()
})

export default router
