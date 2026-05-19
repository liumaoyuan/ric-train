<template>
  <div class="icon-selector">
    <el-input
      :model-value="modelValue"
      readonly
      placeholder="点击选择图标"
      @click="visible = true"
    >
      <template #prefix>
        <el-icon v-if="modelValue" style="font-size: 16px;">
          <component :is="modelValue" />
        </el-icon>
      </template>
      <template #append>
        <el-button @click="visible = true">
          <el-icon><Search /></el-icon>
        </el-button>
      </template>
    </el-input>

    <el-dialog v-model="visible" title="选择图标" width="680px" :close-on-click-modal="false" top="5vh">
      <el-input
        v-model="search"
        placeholder="搜索图标名称"
        clearable
        prefix-icon="Search"
        style="margin-bottom: 16px"
      />
      <div class="icon-grid">
        <div
          v-for="name in filteredIcons"
          :key="name"
          class="icon-item"
          :class="{ active: modelValue === name }"
          @click="selectIcon(name)"
        >
          <el-icon :size="22"><component :is="name" /></el-icon>
          <span class="icon-name">{{ name }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const visible = ref(false)
const search = ref('')

const allIcons = Object.keys(ElementPlusIconsVue)

const filteredIcons = computed(() => {
  if (!search.value) return allIcons
  const q = search.value.toLowerCase()
  return allIcons.filter(name => name.toLowerCase().includes(q))
})

function selectIcon(name) {
  emit('update:modelValue', name)
  visible.value = false
}
</script>

<style scoped>
.icon-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 8px;
  max-height: 420px;
  overflow-y: auto;
}
.icon-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 4px 8px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}
.icon-item:hover {
  border-color: #409eff;
  color: #409eff;
  background: #ecf5ff;
}
.icon-item.active {
  border-color: #409eff;
  color: #409eff;
  background: #ecf5ff;
}
.icon-name {
  font-size: 11px;
  margin-top: 6px;
  text-align: center;
  word-break: break-all;
  line-height: 1.3;
}
</style>
