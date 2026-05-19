import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getUserInfo as getUserInfoApi } from '../api/auth'
import { getCurrentUserMenus } from '../api/menu'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('user_info') || 'null'))
  const menuTree = ref(JSON.parse(localStorage.getItem('menu_tree') || '[]'))

  const isLoggedIn = computed(() => !!token.value)
  const permissions = computed(() => userInfo.value?.permissions || [])
  const roles = computed(() => userInfo.value?.roles || [])
  const username = computed(() => userInfo.value?.username || '')

  async function login(credentials) {
    const res = await loginApi(credentials)
    token.value = res.data.access_token
    refreshToken.value = res.data.refresh_token
    localStorage.setItem('access_token', res.data.access_token)
    localStorage.setItem('refresh_token', res.data.refresh_token)
    await fetchUserInfo()
    await fetchMenus()
  }

  async function fetchUserInfo() {
    try {
      const res = await getUserInfoApi()
      userInfo.value = res.data
      localStorage.setItem('user_info', JSON.stringify(res.data))
    } catch {
      // ignore
    }
  }

  async function fetchMenus() {
    try {
      const res = await getCurrentUserMenus()
      menuTree.value = res.data || []
      localStorage.setItem('menu_tree', JSON.stringify(menuTree.value))
    } catch {
      menuTree.value = []
    }
  }

  function logout() {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    menuTree.value = []
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
    localStorage.removeItem('menu_tree')
  }

  function hasPermission(code) {
    if (!code) return true
    if (roles.value.includes('admin')) return true
    return permissions.value.includes(code)
  }

  return {
    token,
    refreshToken,
    userInfo,
    menuTree,
    isLoggedIn,
    permissions,
    roles,
    username,
    login,
    fetchUserInfo,
    fetchMenus,
    logout,
    hasPermission,
  }
})
