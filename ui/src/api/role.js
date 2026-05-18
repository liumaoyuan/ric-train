import request from './request'

export function getRoleList(params) {
  return request.get('/sys/role/list', { params })
}

export function getAllRoles() {
  return request.get('/sys/role/all')
}

export function getRoleDetail(roleId) {
  return request.get(`/sys/role/${roleId}`)
}

export function createRole(data) {
  return request.post('/sys/role', data)
}

export function updateRole(roleId, data) {
  return request.put(`/sys/role/${roleId}`, data)
}

export function deleteRole(roleId) {
  return request.delete(`/sys/role/${roleId}`)
}

export function toggleRoleStatus(roleId) {
  return request.put(`/sys/role/${roleId}/status`)
}

export function getRoleMenus(roleId) {
  return request.get(`/sys/role/${roleId}/menus`)
}

export function assignRoleMenus(roleId, data) {
  return request.put(`/sys/role/${roleId}/menus`, data)
}
