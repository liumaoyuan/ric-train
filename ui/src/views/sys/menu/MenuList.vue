<template>
  <div class="menu-list">
    <el-card shadow="never">
      <div class="table-toolbar">
        <el-button v-if="hasPerm('sys:menu:add')" type="primary" @click="openCreate(0)">
          <el-icon><Plus /></el-icon>新增目录
        </el-button>
      </div>

      <el-table
        :data="tableData"
        v-loading="loading"
        stripe
        border
        row-key="id"
        default-expand-all
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
      >
        <el-table-column prop="menu_name" label="菜单名称" min-width="200">
          <template #default="{ row }">
            <span v-if="row.menu_type === 0">📁 {{ row.menu_name }}</span>
            <span v-else-if="row.menu_type === 1">📄 {{ row.menu_name }}</span>
            <span v-else>🔘 {{ row.menu_name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="icon" label="图标" width="80" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.icon"><component :is="row.icon" /></el-icon>
          </template>
        </el-table-column>
        <el-table-column prop="menu_type" label="类型" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.menu_type === 0" size="small">目录</el-tag>
            <el-tag v-else-if="row.menu_type === 1" type="success" size="small">菜单</el-tag>
            <el-tag v-else type="info" size="small">按钮</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="permission_code" label="权限标识" width="160" />
        <el-table-column prop="path" label="路由路径" width="180" />
        <el-table-column prop="component" label="组件路径" width="200" show-overflow-tooltip />
        <el-table-column prop="sort_order" label="排序" width="60" align="center" />
        <el-table-column label="状态" width="70" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button v-if="hasPerm('sys:menu:add')" text size="small" type="primary" @click="openCreate(row.id)">新增子项</el-button>
            <el-button v-if="hasPerm('sys:menu:edit')" text size="small" type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button v-if="hasPerm('sys:menu:delete')" text size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑菜单' : '新增菜单'" width="550px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="90px">
        <el-form-item label="上级菜单" prop="parent_id">
          <el-tree-select
            v-model="form.parent_id"
            :data="parentTree"
            :props="{ label: 'menu_name', value: 'id', children: 'children', disabled: (d) => dialog.isEdit && d.id === dialog.id }"
            placeholder="顶级目录"
            clearable
            check-strictly
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="菜单名称" prop="menu_name">
          <el-input v-model="form.menu_name" />
        </el-form-item>
        <el-form-item label="菜单类型" prop="menu_type">
          <el-radio-group v-model="form.menu_type">
            <el-radio :value="0">目录</el-radio>
            <el-radio :value="1">菜单</el-radio>
            <el-radio :value="2">按钮</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.menu_type <= 1" label="图标" prop="icon">
          <el-input v-model="form.icon" placeholder="如 Menu, User, Setting" />
        </el-form-item>
        <el-form-item v-if="form.menu_type <= 1" label="路由路径" prop="path">
          <el-input v-model="form.path" placeholder="如 /sys/user" />
        </el-form-item>
        <el-form-item v-if="form.menu_type === 1" label="组件路径" prop="component">
          <el-input v-model="form.component" placeholder="如 views/sys/user/UserList.vue" />
        </el-form-item>
        <el-form-item label="权限标识" prop="permission_code">
          <el-input v-model="form.permission_code" placeholder="如 sys:user:list" />
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="显示" prop="visible">
          <el-radio-group v-model="form.visible">
            <el-radio :value="1">显示</el-radio>
            <el-radio :value="0">隐藏</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../../../store/auth'
import { getMenuTree, getMenuDetail, createMenu, updateMenu, deleteMenu } from '../../../api/menu'

const authStore = useAuthStore()
function hasPerm(code) { return authStore.hasPermission(code) }

const loading = ref(false)
const tableData = ref([])
const parentTree = ref([])

async function fetchTree() {
  loading.value = true
  try {
    const res = await getMenuTree()
    const tree = Array.isArray(res) ? res : (res.children || [])
    tableData.value = tree
    // 深拷贝一份供上级菜单选择器使用
    parentTree.value = JSON.parse(JSON.stringify(tree))
    // 插入顶级选项
    parentTree.value.unshift({ id: 0, menu_name: '顶级目录', children: [] })
  } finally {
    loading.value = false
  }
}

// 新增/编辑
const dialog = reactive({ visible: false, isEdit: false, id: null })
const formRef = ref()
const saving = ref(false)
const defaultForm = () => ({
  parent_id: 0, menu_name: '', menu_type: 1,
  icon: '', path: '', component: '',
  permission_code: '', sort_order: 0,
  visible: 1, status: 1,
})
const form = reactive(defaultForm())
const formRules = {
  menu_name: [{ required: true, message: '请输入菜单名称', trigger: 'blur' }],
}

function openCreate(parentId) {
  dialog.isEdit = false; dialog.id = null
  Object.assign(form, defaultForm(), { parent_id: parentId })
  dialog.visible = true
}

async function openEdit(row) {
  dialog.isEdit = true; dialog.id = row.id
  try {
    const detail = row.id ? await getMenuDetail(row.id) : row
    form.parent_id = detail.parent_id ?? 0
    form.menu_name = detail.menu_name
    form.menu_type = detail.menu_type
    form.icon = detail.icon || ''
    form.path = detail.path || ''
    form.component = detail.component || ''
    form.permission_code = detail.permission_code || ''
    form.sort_order = detail.sort_order
    form.visible = detail.visible
    form.status = detail.status
  } catch { /* ignore */ }
  dialog.visible = true
}

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload = { ...form }
    if (dialog.isEdit) {
      await updateMenu(dialog.id, payload)
      ElMessage.success('修改成功')
    } else {
      await createMenu(payload)
      ElMessage.success('创建成功')
    }
    dialog.visible = false; fetchTree()
  } finally { saving.value = false }
}

// 删除
function handleDelete(row) {
  ElMessageBox.confirm(`确定删除菜单「${row.menu_name}」吗？<br>如果存在子节点将一并删除！`, '警告', {
    type: 'warning', confirmButtonText: '删除', dangerouslyUseHTMLString: true,
  }).then(async () => {
    await deleteMenu(row.id)
    ElMessage.success('已删除'); fetchTree()
  }).catch(() => {})
}

onMounted(fetchTree)
</script>

<style scoped>
.table-toolbar { margin-bottom: 16px; }
</style>
