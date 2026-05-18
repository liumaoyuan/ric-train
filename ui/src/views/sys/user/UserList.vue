<template>
  <div class="user-list">
    <!-- 搜索栏 -->
    <el-card shadow="never" class="search-card">
      <el-form :model="query" inline size="default">
        <el-form-item label="用户名">
          <el-input v-model="query.username" placeholder="模糊搜索" clearable />
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

    <!-- 表格工具栏 -->
    <el-card shadow="never" class="table-card">
      <div class="table-toolbar">
        <div class="toolbar-left">
          <el-button v-if="hasPerm('sys:user:add')" type="primary" @click="openCreate">
            <el-icon><Plus /></el-icon>新增用户
          </el-button>
        </div>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe border style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="display_name" label="显示名称" width="120" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">{{ row.created_at }}</template>
        </el-table-column>
        <el-table-column label="操作" width="320" fixed="right">
          <template #default="{ row }">
            <el-button v-if="hasPerm('sys:user:edit')" text size="small" type="primary" @click="openEdit(row)">
              编辑
            </el-button>
            <el-button v-if="hasPerm('sys:user:assign-role')" text size="small" type="primary" @click="openAssignRole(row)">
              分配角色
            </el-button>
            <el-button v-if="hasPerm('sys:user:edit')" text size="small" type="primary" @click="openResetPwd(row)">
              重置密码
            </el-button>
            <el-button
              v-if="hasPerm('sys:user:toggle')"
              text
              size="small"
              :type="row.status === 1 ? 'warning' : 'success'"
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 1 ? '禁用' : '启用' }}
            </el-button>
            <el-button
              v-if="hasPerm('sys:user:delete') && row.username !== 'admin'"
              text
              size="small"
              type="danger"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
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
    <el-dialog
      v-model="dialog.visible"
      :title="dialog.isEdit ? '编辑用户' : '新增用户'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="90px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="dialog.isEdit" />
        </el-form-item>
        <el-form-item label="显示名称" prop="display_name">
          <el-input v-model="form.display_name" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item v-if="!dialog.isEdit" label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
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

    <!-- 分配角色弹窗 -->
    <el-dialog v-model="roleDialog.visible" title="分配角色" width="450px">
      <el-checkbox-group v-model="roleDialog.selected">
        <el-checkbox v-for="r in roleDialog.allRoles" :key="r.id" :label="r.id" :value="r.id">
          {{ r.role_name }} ({{ r.role_code }})
        </el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="roleDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="roleDialog.saving" @click="handleSaveRoles">保存</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码弹窗 -->
    <el-dialog v-model="pwdDialog.visible" title="重置密码" width="400px">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="90px">
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="pwdDialog.saving" @click="handleSavePwd">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../../../store/auth'
import { getUserList, createUser, updateUser, deleteUser, toggleUserStatus, resetUserPassword, getUserRoles, assignUserRoles } from '../../../api/user'
import { getAllRoles } from '../../../api/role'

const authStore = useAuthStore()
function hasPerm(code) { return authStore.hasPermission(code) }

// 查询参数
const query = reactive({ page: 1, page_size: 10, username: '', status: '' })
const tableData = ref([])
const total = ref(0)
const loading = ref(false)

async function fetchData() {
  loading.value = true
  try {
    const params = { ...query }
    if (params.status === '' || params.status === null) delete params.status
    if (!params.username) delete params.username
    const res = await getUserList(params)
    tableData.value = res.items || res.records || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() { query.page = 1; fetchData() }
function handleReset() { query.username = ''; query.status = ''; query.page = 1; fetchData() }

// 新增/编辑
const dialog = reactive({ visible: false, isEdit: false, id: null })
const formRef = ref()
const saving = ref(false)
const defaultForm = () => ({ username: '', display_name: '', phone: '', email: '', password: '', remark: '', status: 1 })
const form = reactive(defaultForm())
const formRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

function openCreate() {
  dialog.isEdit = false
  dialog.id = null
  Object.assign(form, defaultForm())
  dialog.visible = true
}

function openEdit(row) {
  dialog.isEdit = true
  dialog.id = row.id
  form.username = row.username
  form.display_name = row.display_name || ''
  form.phone = row.phone || ''
  form.email = row.email || ''
  form.password = ''
  form.remark = row.remark || ''
  form.status = row.status
  dialog.visible = true
}

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (dialog.isEdit) {
      const payload = { display_name: form.display_name, phone: form.phone, email: form.email, remark: form.remark, status: form.status }
      await updateUser(dialog.id, payload)
      ElMessage.success('修改成功')
    } else {
      await createUser({ ...form })
      ElMessage.success('创建成功')
    }
    dialog.visible = false
    fetchData()
  } finally {
    saving.value = false
  }
}

// 删除
function handleDelete(row) {
  ElMessageBox.confirm(`确定删除用户「${row.username}」吗？`, '警告', {
    type: 'warning',
    confirmButtonText: '删除',
    confirmButtonClass: 'el-button--danger',
  }).then(async () => {
    await deleteUser(row.id)
    ElMessage.success('已删除')
    fetchData()
  }).catch(() => {})
}

// 切换状态
async function handleToggleStatus(row) {
  const action = row.status === 1 ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定${action}用户「${row.username}」吗？`, '提示')
    await toggleUserStatus(row.id)
    ElMessage.success(`${action}成功`)
    fetchData()
  } catch { /* 取消 */ }
}

// 分配角色
const roleDialog = reactive({ visible: false, saving: false, userId: null, selected: [], allRoles: [] })

async function openAssignRole(row) {
  roleDialog.userId = row.id
  roleDialog.selected = []
  try {
    const [rolesRes, userRolesRes] = await Promise.all([getAllRoles(), getUserRoles(row.id)])
    roleDialog.allRoles = Array.isArray(rolesRes) ? rolesRes : (rolesRes.items || rolesRes.records || [])
    roleDialog.selected = Array.isArray(userRolesRes) ? userRolesRes.map(r => r.role_id || r.id) : (userRolesRes.role_ids || [])
  } catch { /* ignore */ }
  roleDialog.visible = true
}

async function handleSaveRoles() {
  roleDialog.saving = true
  try {
    await assignUserRoles(roleDialog.userId, { role_ids: roleDialog.selected })
    ElMessage.success('分配成功')
    roleDialog.visible = false
  } finally {
    roleDialog.saving = false
  }
}

// 重置密码
const pwdDialog = reactive({ visible: false, saving: false, userId: null })
const pwdFormRef = ref()
const pwdForm = reactive({ new_password: '' })
const pwdRules = { new_password: [{ required: true, message: '请输入新密码', trigger: 'blur' }] }

function openResetPwd(row) {
  pwdDialog.userId = row.id
  pwdForm.new_password = ''
  pwdDialog.visible = true
}

async function handleSavePwd() {
  const valid = await pwdFormRef.value.validate().catch(() => false)
  if (!valid) return
  pwdDialog.saving = true
  try {
    await resetUserPassword(pwdDialog.userId, { new_password: pwdForm.new_password })
    ElMessage.success('密码已重置')
    pwdDialog.visible = false
  } finally {
    pwdDialog.saving = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.search-card { margin-bottom: 16px; }
.table-card { }
.table-toolbar { margin-bottom: 16px; }
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
