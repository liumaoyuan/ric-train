import request from './request'

export function getCurrentUserMenus() {
  return request.get('/auth/menus')
}

export function getMenuTree() {
  return request.get('/sys/menu/tree')
}

export function getMenuList() {
  return request.get('/sys/menu/list')
}

export function getMenuDetail(menuId) {
  return request.get(`/sys/menu/${menuId}`)
}

export function createMenu(data) {
  return request.post('/sys/menu', data)
}

export function updateMenu(menuId, data) {
  return request.put(`/sys/menu/${menuId}`, data)
}

export function deleteMenu(menuId) {
  return request.delete(`/sys/menu/${menuId}`)
}
