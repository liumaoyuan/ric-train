import request from './request'

// 上传文档
export function uploadDocument(formData) {
  return request.post('/knowledge/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// 文档列表
export function getKnowledgeList(params) {
  return request.get('/knowledge/list', { params })
}

// 文档详情
export function getKnowledgeDetail(id) {
  return request.get(`/knowledge/${id}`)
}

// 编辑文档
export function updateKnowledge(id, data) {
  return request.put(`/knowledge/${id}`, data)
}

// 删除文档
export function deleteKnowledge(id) {
  return request.delete(`/knowledge/${id}`)
}

// 分块预览
export function previewChunks(id) {
  return request.post(`/knowledge/${id}/preview`)
}

// 确认向量化
export function vectorizeDocument(id, data = {}) {
  return request.post(`/knowledge/${id}/vectorize`, data)
}

// 知识库检索
export function searchKnowledge(data) {
  return request.post('/knowledge/search', data)
}

// 获取文档分块列表
export function getDocumentChunks(id) {
  return request.get(`/knowledge/${id}/chunks`)
}
