import request from './request'

export function getUserList(params) {
  return request.get('/sys/user/list', { params })
}

export function getUserDetail(userId) {
  return request.get(`/sys/user/${userId}`)
}

export function createUser(data) {
  return request.post('/sys/user', data)
}

export function updateUser(userId, data) {
  return request.put(`/sys/user/${userId}`, data)
}

export function deleteUser(userId) {
  return request.delete(`/sys/user/${userId}`)
}

export function toggleUserStatus(userId) {
  return request.put(`/sys/user/${userId}/status`)
}

export function resetUserPassword(userId, data) {
  return request.put(`/sys/user/${userId}/password`, { password: data.new_password })
}

export function getUserRoles(userId) {
  return request.get(`/sys/user/${userId}/roles`)
}

export function assignUserRoles(userId, data) {
  return request.put(`/sys/user/${userId}/roles`, data)
}
