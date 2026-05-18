<template>
  <div class="role-list">
    <!-- 搜索栏 -->
    <el-card shadow="never" class="search-card">
      <el-form :model="query" inline size="default">
        <el-form-item label="角色名称">
          <el-input v-model="query.role_name" placeholder="模糊搜索" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格 -->
    <el-card shadow="never" class="table-card">
      <div class="table-toolbar">
        <el-button v-if="hasPerm('sys:role:add')" type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>新增角色
        </el-button>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="role_name" label="角色名称" width="150" />
        <el-table-column prop="role_code" label="角色编码" width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="sort_order" label="排序" width="70" align="center" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button v-if="hasPerm('sys:role:edit')" text size="small" type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button v-if="hasPerm('sys:role:assign-menu')" text size="small" type="primary" @click="openAssignMenu(row)">分配菜单</el-button>
            <el-button v-if="hasPerm('sys:role:toggle')" text size="small" :type="row.status === 1 ? 'warning' : 'success'" @click="handleToggleStatus(row)">
              {{ row.status === 1 ? '禁用' : '启用' }}
            </el-button>
            <el-button v-if="hasPerm('sys:role:delete') && row.role_code !== 'admin'" text size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.page_size"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑角色' : '新增角色'" width="500px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="90px">
        <el-form-item label="角色名称" prop="role_name">
          <el-input v-model="form.role_name" />
        </el-form-item>
        <el-form-item label="角色编码" prop="role_code">
          <el-input v-model="form.role_code" :disabled="dialog.isEdit" placeholder="如 admin, employee" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="form.sort_order" :min="0" />
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

    <!-- 分配菜单弹窗 -->
    <el-dialog v-model="menuDialog.visible" title="分配菜单权限" width="400px">
      <el-tree
        ref="menuTreeRef"
        :data="menuDialog.treeData"
        show-checkbox
        node-key="id"
        :props="{ label: 'menu_name', children: 'children' }"
        default-expand-all
        check-strictly
      />
      <template #footer>
        <el-button @click="menuDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="menuDialog.saving" @click="handleSaveMenus">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../../../store/auth'
import { getRoleList, createRole, updateRole, deleteRole, toggleRoleStatus, getRoleMenus, assignRoleMenus } from '../../../api/role'
import { getMenuTree } from '../../../api/menu'

const authStore = useAuthStore()
function hasPerm(code) { return authStore.hasPermission(code) }

const query = reactive({ page: 1, page_size: 10, role_name: '', status: '' })
const tableData = ref([])
const total = ref(0)
const loading = ref(false)

async function fetchData() {
  loading.value = true
  try {
    const params = { ...query }
    if (params.status === '' || params.status === null) delete params.status
    if (!params.role_name) delete params.role_name
    const res = await getRoleList(params)
    tableData.value = res.items || res.records || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() { query.page = 1; fetchData() }
function handleReset() { query.role_name = ''; query.status = ''; query.page = 1; fetchData() }

// 新增/编辑
const dialog = reactive({ visible: false, isEdit: false, id: null })
const formRef = ref()
const saving = ref(false)
const defaultForm = () => ({ role_name: '', role_code: '', description: '', sort_order: 0, status: 1 })
const form = reactive(defaultForm())
const formRules = {
  role_name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
  role_code: [{ required: true, message: '请输入角色编码', trigger: 'blur' }],
}

function openCreate() { dialog.isEdit = false; dialog.id = null; Object.assign(form, defaultForm()); dialog.visible = true }

function openEdit(row) {
  dialog.isEdit = true; dialog.id = row.id
  form.role_name = row.role_name; form.role_code = row.role_code
  form.description = row.description || ''
  form.sort_order = row.sort_order; form.status = row.status
  dialog.visible = true
}

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (dialog.isEdit) {
      await updateRole(dialog.id, { role_name: form.role_name, description: form.description, sort_order: form.sort_order, status: form.status })
      ElMessage.success('修改成功')
    } else {
      await createRole({ ...form })
      ElMessage.success('创建成功')
    }
    dialog.visible = false; fetchData()
  } finally { saving.value = false }
}

// 删除
function handleDelete(row) {
  ElMessageBox.confirm(`确定删除角色「${row.role_name}」吗？`, '警告', { type: 'warning', confirmButtonText: '删除' })
    .then(async () => { await deleteRole(row.id); ElMessage.success('已删除'); fetchData() })
    .catch(() => {})
}

// 切换状态
async function handleToggleStatus(row) {
  const action = row.status === 1 ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定${action}角色「${row.role_name}」吗？`, '提示')
    await toggleRoleStatus(row.id)
    ElMessage.success(`${action}成功`); fetchData()
  } catch { /* 取消 */ }
}

// 分配菜单
const menuTreeRef = ref()
const menuDialog = reactive({ visible: false, saving: false, roleId: null, treeData: [], checkedMenus: [] })

async function openAssignMenu(row) {
  menuDialog.roleId = row.id
  const [treeRes, menusRes] = await Promise.all([getMenuTree(), getRoleMenus(row.id)])
  menuDialog.treeData = Array.isArray(treeRes) ? treeRes : (treeRes.children || [])
  menuDialog.checkedMenus = Array.isArray(menusRes) ? menusRes : (menusRes.menu_ids || [])
  menuDialog.visible = true
  // 下一帧设置勾选
  setTimeout(() => { menuTreeRef.value?.setCheckedKeys(menuDialog.checkedMenus) }, 100)
}

async function handleSaveMenus() {
  menuDialog.saving = true
  try {
    const checkedKeys = menuTreeRef.value?.getCheckedKeys() || []
    await assignRoleMenus(menuDialog.roleId, { menu_ids: checkedKeys })
    ElMessage.success('分配成功')
    menuDialog.visible = false
  } finally { menuDialog.saving = false }
}

onMounted(fetchData)
</script>

<style scoped>
.search-card { margin-bottom: 16px; }
.table-toolbar { margin-bottom: 16px; }
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
