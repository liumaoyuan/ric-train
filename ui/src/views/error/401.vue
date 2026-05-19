<template>
  <div class="error-page">
    <div class="error-content">
      <h1 class="error-code">401</h1>
      <h2 class="error-title">权限不足</h2>
      <p class="error-desc">抱歉，您没有权限访问该页面</p>
      <el-button type="primary" @click="$router.push('/dashboard')">返回首页</el-button>
    </div>
  </div>
</template>

<style scoped>
.error-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
}
.error-content {
  text-align: center;
}
.error-code {
  font-size: 120px;
  color: #409eff;
  margin: 0;
  line-height: 1;
}
.error-title {
  font-size: 28px;
  color: #303133;
  margin: 20px 0 10px;
}
.error-desc {
  font-size: 14px;
  color: #909399;
  margin-bottom: 30px;
}
</style>
