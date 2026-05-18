<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6" v-for="card in statsCards" :key="card.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="welcome-card">
      <template #header>
        <span>欢迎使用</span>
      </template>
      <p>连锁餐饮 AI 系统管理后台，请通过左侧菜单导航进行系统管理操作。</p>
      <p>当前用户：<strong>{{ authStore.username }}</strong></p>
      <p>角色：<strong>{{ authStore.roles.join(', ') || '无' }}</strong></p>
    </el-card>
  </div>
</template>

<script setup>
import { useAuthStore } from '../../store/auth'

const authStore = useAuthStore()

const statsCards = [
  { label: '系统用户', value: '—' },
  { label: '系统角色', value: '—' },
  { label: '菜单权限', value: '—' },
  { label: '登录状态', value: '正常' },
]
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
}
.stat-card {
  text-align: center;
  margin-bottom: 20px;
}
.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
}
.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}
.welcome-card {
  margin-top: 20px;
}
.welcome-card p {
  margin: 8px 0;
  font-size: 14px;
  color: #606266;
}
</style>
