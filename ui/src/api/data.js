import request from './request'

// ==================== 订单 ====================
export function getOrderList(params) {
  return request.get('/data/orders', { params })
}

export function getOrderDetail(orderNo) {
  return request.get(`/data/orders/${encodeURIComponent(orderNo)}`)
}

// ==================== 营业汇总 ====================
export function getDailySummaryList(params) {
  return request.get('/data/daily-summary', { params })
}

export function getDailySummaryStat(params) {
  return request.get('/data/daily-summary/stat', { params })
}

// ==================== 菜品 ====================
export function getDishList(params) {
  return request.get('/data/dishes', { params })
}

export function getDishDetail(dishId) {
  return request.get(`/data/dishes/${dishId}`)
}

// ==================== 门店 ====================
export function getStoreList(params) {
  return request.get('/data/stores', { params })
}

export function getStoreDetail(storeId) {
  return request.get(`/data/stores/${storeId}`)
}

// ==================== 评论 ====================
export function getReviewList(params) {
  return request.get('/data/reviews', { params })
}

export function getReviewDetail(reviewId) {
  return request.get(`/data/reviews/${reviewId}`)
}
