<template>
  <!-- 目录类型且有子节点 → 可展开的子菜单 -->
  <el-sub-menu v-if="item.menu_type === 0 && hasVisibleChildren" :index="item.path || String(item.id)">
    <template #title>
      <el-icon v-if="iconComp"><component :is="iconComp" /></el-icon>
      <span>{{ item.menu_name }}</span>
    </template>
    <MenuItemTree v-for="child in item.children" :key="child.id" :item="child" />
  </el-sub-menu>

  <!-- 菜单/页面类型且通过权限校验 → 菜单项 -->
  <el-menu-item v-else-if="item.menu_type === 1 && hasPerm(item.permission_code)" :index="resolvedPath">
    <el-icon v-if="iconComp"><component :is="iconComp" /></el-icon>
    <span>{{ item.menu_name }}</span>
  </el-menu-item>
</template>

<script setup>
import { computed, resolveComponent } from 'vue'
import { useAuthStore } from '../store/auth'

const props = defineProps({
  item: { type: Object, required: true },
})

const authStore = useAuthStore()

const iconComp = computed(() => {
  if (!props.item.icon) return null
  return resolveComponent(props.item.icon) || null
})

const resolvedPath = computed(() => {
  const p = props.item.path || ''
  return p.startsWith('/') ? p : `/${p}`
})

// 递归检查子节点中是否有可渲染的菜单项（考虑权限）
const hasVisibleChildren = computed(() => {
  if (!props.item.children || props.item.children.length === 0) return false
  return props.item.children.some(child => isVisibleRecursive(child))
})

function isVisibleRecursive(item) {
  if (item.menu_type === 0) {
    return item.children && item.children.some(c => isVisibleRecursive(c))
  }
  return item.menu_type === 1 && hasPerm(item.permission_code)
}

function hasPerm(code) {
  if (!code) return true
  return authStore.hasPermission(code)
}
</script>
