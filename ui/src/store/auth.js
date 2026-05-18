import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getUserInfo as getUserInfoApi } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('user_info') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const permissions = computed(() => userInfo.value?.permissions || [])
  const roles = computed(() => userInfo.value?.roles || [])
  const username = computed(() => userInfo.value?.username || '')

  async function login(credentials) {
    const res = await loginApi(credentials)
    token.value = res.access_token
    refreshToken.value = res.refresh_token
    localStorage.setItem('access_token', res.access_token)
    localStorage.setItem('refresh_token', res.refresh_token)
    // 登录成功后获取用户信息
    await fetchUserInfo()
  }

  async function fetchUserInfo() {
    try {
      const res = await getUserInfoApi()
      userInfo.value = res
      localStorage.setItem('user_info', JSON.stringify(res))
    } catch {
      // ignore
    }
  }

  function logout() {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
  }

  function hasPermission(code) {
    // admin 角色拥有全部权限
    if (roles.value.includes('admin')) return true
    return permissions.value.includes(code)
  }

  return {
    token,
    refreshToken,
    userInfo,
    isLoggedIn,
    permissions,
    roles,
    username,
    login,
    fetchUserInfo,
    logout,
    hasPermission,
  }
})
