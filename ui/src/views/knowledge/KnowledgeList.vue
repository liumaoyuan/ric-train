<template>
  <div class="knowledge-list">
    <!-- 搜索栏 -->
    <el-card shadow="never" class="search-card">
      <el-form :model="query" inline size="default">
        <el-form-item label="文档标题">
          <el-input v-model="query.title" placeholder="模糊搜索" clearable />
        </el-form-item>
        <el-form-item label="知识分类">
          <el-select v-model="query.category" placeholder="全部" clearable style="width: 140px">
            <el-option label="公司制度" value="公司制度" />
            <el-option label="政策法规" value="政策法规" />
            <el-option label="菜品知识" value="菜品知识" />
            <el-option label="运营流程" value="运营流程" />
            <el-option label="SOP标准" value="SOP标准" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="待处理" :value="0" />
            <el-option label="分块预览中" :value="1" />
            <el-option label="已向量化" :value="2" />
            <el-option label="失败" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 文档列表 -->
    <el-card shadow="never" class="table-card">
      <div class="table-toolbar">
        <div class="toolbar-left">
          <el-button v-if="hasPerm('knowledge:upload')" type="primary" @click="openUpload">
            <el-icon><Plus /></el-icon>上传文档
          </el-button>
        </div>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe border style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="文档标题" min-width="180" show-overflow-tooltip />
        <el-table-column prop="file_name" label="文件名" width="200" show-overflow-tooltip />
        <el-table-column label="大小" width="100">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.category" size="small">{{ row.category }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="permission_scope" label="权限范围" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.permission_scope === 'all'" size="small" type="info">全部</el-tag>
            <el-tag v-else-if="row.permission_scope === 'employee_only'" size="small" type="warning">仅员工</el-tag>
            <el-tag v-else-if="row.permission_scope === 'franchisee_only'" size="small" type="success">仅加盟商</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="分块数" width="70" align="center" />
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 0" type="info" size="small">待处理</el-tag>
            <el-tag v-else-if="row.status === 1" type="warning" size="small">分块预览中</el-tag>
            <el-tag v-else-if="row.status === 2" type="success" size="small">已向量化</el-tag>
            <el-tag v-else type="danger" size="small">失败</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="上传时间" width="170">
          <template #default="{ row }">{{ row.created_at }}</template>
        </el-table-column>
        <el-table-column label="操作" width="350" fixed="right">
          <template #default="{ row }">
            <el-button v-if="hasPerm('knowledge:edit') && row.status !== 2" text size="small" type="primary" @click="openEdit(row)">
              编辑
            </el-button>
            <el-button
              v-if="hasPerm('knowledge:preview')"
              text
              size="small"
              type="primary"
              @click="handlePreview(row)"
              :loading="previewLoading === row.id"
            >
              分块预览
            </el-button>
            <el-button
              v-if="hasPerm('knowledge:vectorize') && row.status === 1"
              text
              size="small"
              type="success"
              @click="handleVectorize(row)"
              :loading="vectorizeLoading === row.id"
            >
              确认向量化
            </el-button>
            <el-button
              v-if="hasPerm('knowledge:vectorize') && row.status === 2"
              text
              size="small"
              type="warning"
              @click="openEvaluate(row)"
            >
              RAGAS评估
            </el-button>
            <el-button
              v-if="hasPerm('knowledge:delete')"
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

    <!-- 上传文档弹窗 -->
    <el-dialog v-model="uploadDialog.visible" title="上传文档" width="550px" :close-on-click-modal="false">
      <el-form ref="uploadFormRef" :model="uploadForm" :rules="uploadRules" label-width="100px">
        <el-form-item label="文档标题" prop="title">
          <el-input v-model="uploadForm.title" placeholder="输入文档标题" />
        </el-form-item>
        <el-form-item label="选择文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :show-file-list="true"
            :limit="1"
            @change="handleFileChange"
            accept=".pdf,.doc,.docx,.txt,.md"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <span class="el-upload__tip">支持 PDF / Word / TXT / MD 格式</span>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="知识分类" prop="category">
          <el-select v-model="uploadForm.category" placeholder="选择分类" style="width: 100%">
            <el-option label="公司制度" value="公司制度" />
            <el-option label="政策法规" value="政策法规" />
            <el-option label="菜品知识" value="菜品知识" />
            <el-option label="运营流程" value="运营流程" />
            <el-option label="SOP标准" value="SOP标准" />
          </el-select>
        </el-form-item>
        <el-form-item label="权限范围" prop="permission_scope">
          <el-radio-group v-model="uploadForm.permission_scope">
            <el-radio value="all">全部可见</el-radio>
            <el-radio value="employee_only">仅员工</el-radio>
            <el-radio value="franchisee_only">仅加盟商</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="分块策略" prop="chunk_strategy">
          <el-select v-model="uploadForm.chunk_strategy" style="width: 100%">
            <el-option label="固定长度（默认）" value="fixed" />
            <el-option label="段落分割" value="paragraph" />
            <el-option label="递归分块" value="recursive" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="uploadForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="uploadSaving" @click="handleUpload">上传</el-button>
      </template>
    </el-dialog>

    <!-- 编辑文档弹窗 -->
    <el-dialog v-model="editDialog.visible" title="编辑文档" width="500px">
      <el-form ref="editFormRef" :model="editForm" label-width="100px">
        <el-form-item label="文档标题">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="知识分类">
          <el-select v-model="editForm.category" style="width: 100%">
            <el-option label="公司制度" value="公司制度" />
            <el-option label="政策法规" value="政策法规" />
            <el-option label="菜品知识" value="菜品知识" />
            <el-option label="运营流程" value="运营流程" />
            <el-option label="SOP标准" value="SOP标准" />
          </el-select>
        </el-form-item>
        <el-form-item label="权限范围">
          <el-radio-group v-model="editForm.permission_scope">
            <el-radio value="all">全部可见</el-radio>
            <el-radio value="employee_only">仅员工</el-radio>
            <el-radio value="franchisee_only">仅加盟商</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="editSaving" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 分块预览弹窗 -->
    <el-dialog v-model="chunkDialog.visible" title="分块预览" width="800px" :close-on-click-modal="false">
      <div v-if="chunkDialog.chunks.length === 0">
        <el-empty description="暂无分块数据" />
      </div>
      <div v-else class="chunk-list">
        <div class="chunk-info">
          共 <strong>{{ chunkDialog.chunks.length }}</strong> 个分块，
          已选择 <strong>{{ chunkDialog.selected.length }}</strong> 个
        </div>
        <el-checkbox
          v-model="chunkDialog.selectAll"
          :indeterminate="chunkDialog.isIndeterminate"
          @change="handleSelectAll"
        >
          全选
        </el-checkbox>
        <el-divider />
        <div v-for="chunk in chunkDialog.chunks" :key="chunk.id" class="chunk-item">
          <el-checkbox
            v-model="chunkDialog.selected"
            :label="chunk.id"
            :value="chunk.id"
          >
            <div class="chunk-header">
              <span class="chunk-index">#{{ chunk.chunk_index + 1 }}</span>
              <span class="chunk-tokens">≈{{ chunk.token_count }} tokens</span>
            </div>
            <div class="chunk-content">{{ chunk.chunk_content_full || chunk.chunk_content }}</div>
          </el-checkbox>
        </div>

        <!-- 已向量化文档的重新分块区域 -->
        <template v-if="chunkDialog.docStatus === 2">
          <el-divider />
          <div class="rechunk-section">
            <span class="rechunk-title">重新分块</span>
            <el-form :inline="true" class="rechunk-form">
              <el-form-item label="分块策略">
                <el-select v-model="chunkDialog.rechunkStrategy" style="width: 160px">
                  <el-option label="固定长度（默认）" value="fixed" />
                  <el-option label="段落分割" value="paragraph" />
                  <el-option label="递归分块" value="recursive" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="rechunkLoading" @click="handleRechunk">
                  重新分块
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </template>
      </div>
      <template #footer>
        <el-button @click="chunkDialog.visible = false">取消</el-button>
        <el-button
          type="success"
          :loading="vectorizeLoading === chunkDialog.docId"
          :disabled="chunkDialog.selected.length === 0"
          @click="handleConfirmVectorize"
        >
          确认向量化（{{ chunkDialog.selected.length }} 个分块）
        </el-button>
      </template>
    </el-dialog>

    <!-- RAGAS 评估弹窗 -->
    <el-dialog v-model="evaluateDialog.visible" title="RAGAS 评估" width="600px" :close-on-click-modal="false">
      <el-form label-width="120px">
        <el-form-item label="评估文档">
          <el-upload
            ref="evaluateUploadRef"
            :auto-upload="false"
            :show-file-list="true"
            :limit="1"
            accept=".json"
            @change="handleEvaluateFileChange"
          >
            <el-button type="primary">选择 JSON 文件</el-button>
            <template #tip>
              <span class="el-upload__tip">上传包含测试用例的 JSON 文件，格式：[{"question": "...", "ground_truth": "..."}]</span>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <div v-if="evaluateDialog.result" class="evaluate-result">
        <el-divider />
        <pre class="evaluate-summary">{{ evaluateDialog.result }}</pre>
      </div>
      <template #footer>
        <el-button @click="evaluateDialog.visible = false">关闭</el-button>
        <el-button type="primary" :disabled="!evaluateFile" @click="handleEvaluate">
          开始评估
        </el-button>
      </template>
    </el-dialog>

    <!-- 任务进度弹窗 -->
    <el-dialog v-model="progressDialog.visible" title="任务进度" width="450px" :close-on-click-modal="false" :close-on-press-escape="false" :show-close="false">
      <div class="progress-body">
        <div class="progress-desc">{{ progressDialog.description }}</div>
        <el-progress :percentage="progressDialog.progress" :status="progressDialog.status === 'exception' ? 'exception' : progressDialog.status === 'success' ? 'success' : ''" :stroke-width="16" :text-inside="true" />
        <div class="progress-message">{{ progressDialog.message }}</div>
      </div>
      <template #footer>
        <el-button v-if="progressDialog.showClose" type="primary" @click="progressDialog.visible = false">关闭</el-button>
        <el-button v-else disabled>执行中...</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../../store/auth'
import {
  getKnowledgeList, uploadDocument, updateKnowledge, deleteKnowledge,
  previewChunks, vectorizeDocument, evaluateDocument, getTaskProgress,
} from '../../api/knowledge'

const authStore = useAuthStore()
function hasPerm(code) { return authStore.hasPermission(code) }

// 查询参数
const query = reactive({ page: 1, page_size: 10, title: '', category: '', status: '' })
const tableData = ref([])
const total = ref(0)
const loading = ref(false)
const previewLoading = ref(null)
const vectorizeLoading = ref(null)
const rechunkLoading = ref(false)

// ====== 任务进度轮询 ======
const progressDialog = reactive({
  visible: false, progress: 0, description: '', message: '', status: '', showClose: false,
})
let pollTimer = null

function stopPolling() {
  if (pollTimer) { clearTimeout(pollTimer); pollTimer = null }
}

function startPolling(taskId, { onComplete, onFail }) {
  const poll = async () => {
    try {
      const res = await getTaskProgress(taskId)
      const task = res.data
      if (!task) { pollTimer = setTimeout(poll, 2000); return }

      progressDialog.progress = task.progress
      progressDialog.message = task.message

      if (task.status === 'completed') {
        stopPolling()
        progressDialog.status = 'success'
        progressDialog.message = '任务已完成'
        progressDialog.showClose = true
        onComplete?.(task.result)
      } else if (task.status === 'failed') {
        stopPolling()
        progressDialog.status = 'exception'
        progressDialog.message = task.error || '任务失败'
        progressDialog.showClose = true
        onFail?.(task.error)
      } else {
        pollTimer = setTimeout(poll, 1500)
      }
    } catch {
      pollTimer = setTimeout(poll, 3000)
    }
  }
  poll()
}

async function fetchData() {
  loading.value = true
  try {
    const params = { ...query }
    if (!params.title) delete params.title
    if (!params.category) delete params.category
    if (params.status === '' || params.status === null) delete params.status
    const res = await getKnowledgeList(params)
    tableData.value = res.data?.data || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() { query.page = 1; fetchData() }
function handleReset() { query.title = ''; query.category = ''; query.status = ''; query.page = 1; fetchData() }

// 文件大小格式化
function formatSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// ====== 上传文档 ======
const uploadDialog = reactive({ visible: false })
const uploadFormRef = ref()
const uploadRef = ref()
const uploadSaving = ref(false)
const uploadFile = ref(null)

const defaultUploadForm = () => ({
  title: '', category: '', permission_scope: 'all',
  chunk_strategy: 'fixed', remark: '',
})
const uploadForm = reactive(defaultUploadForm())
const uploadRules = {
  title: [{ required: true, message: '请输入文档标题', trigger: 'blur' }],
  category: [{ required: true, message: '请选择知识分类', trigger: 'change' }],
}

function handleFileChange(file) {
  uploadFile.value = file.raw
}

function openUpload() {
  Object.assign(uploadForm, defaultUploadForm())
  uploadFile.value = null
  uploadRef.value?.clearFiles()
  uploadDialog.visible = true
}

async function handleUpload() {
  const valid = await uploadFormRef.value.validate().catch(() => false)
  if (!valid) return
  if (!uploadFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  uploadSaving.value = true
  try {
    const formData = new FormData()
    formData.append('file', uploadFile.value)
    formData.append('title', uploadForm.title)
    formData.append('category', uploadForm.category)
    formData.append('permission_scope', uploadForm.permission_scope)
    formData.append('chunk_strategy', uploadForm.chunk_strategy)
    formData.append('remark', uploadForm.remark)
    await uploadDocument(formData)
    ElMessage.success('上传成功')
    uploadDialog.visible = false
    fetchData()
  } finally {
    uploadSaving.value = false
  }
}

// ====== 编辑文档 ======
const editDialog = reactive({ visible: false, id: null })
const editFormRef = ref()
const editSaving = ref(false)
const editForm = reactive({ title: '', category: '', permission_scope: 'all', remark: '' })

function openEdit(row) {
  editDialog.id = row.id
  editForm.title = row.title
  editForm.category = row.category || ''
  editForm.permission_scope = row.permission_scope || 'all'
  editForm.remark = row.remark || ''
  editDialog.visible = true
}

async function handleSaveEdit() {
  editSaving.value = true
  try {
    await updateKnowledge(editDialog.id, { ...editForm })
    ElMessage.success('更新成功')
    editDialog.visible = false
    fetchData()
  } finally {
    editSaving.value = false
  }
}

// ====== 删除 ======
function handleDelete(row) {
  ElMessageBox.confirm(`确定删除文档「${row.title}」吗？删除后不可恢复。`, '警告', {
    type: 'warning',
    confirmButtonText: '删除',
    confirmButtonClass: 'el-button--danger',
  }).then(async () => {
    await deleteKnowledge(row.id)
    ElMessage.success('已删除')
    fetchData()
  }).catch(() => {})
}

// ====== 分块预览与向量化 ======
const chunkDialog = reactive({
  visible: false, docId: null, docStatus: null, chunks: [],
  selected: [], selectAll: false, isIndeterminate: false,
  rechunkStrategy: 'fixed',
})

async function handlePreview(row) {
  previewLoading.value = row.id
  try {
    const res = await previewChunks(row.id)
    const chunks = res.data?.chunks || []
    chunkDialog.docId = row.id
    chunkDialog.docStatus = row.status
    chunkDialog.chunks = chunks
    chunkDialog.selected = chunks.map(c => c.id)
    chunkDialog.selectAll = true
    chunkDialog.isIndeterminate = false
    chunkDialog.rechunkStrategy = row.chunk_strategy || 'fixed'
    chunkDialog.visible = true
  } catch (e) {
    ElMessage.error('分块预览失败')
  } finally {
    previewLoading.value = null
  }
}

async function handleRechunk() {
  rechunkLoading.value = true
  try {
    const res = await previewChunks(chunkDialog.docId, { chunk_strategy: chunkDialog.rechunkStrategy })
    const chunks = res.data?.chunks || []
    chunkDialog.chunks = chunks
    chunkDialog.selected = chunks.map(c => c.id)
    chunkDialog.selectAll = true
    chunkDialog.isIndeterminate = false
    chunkDialog.docStatus = 1
    ElMessage.success('重新分块完成')
  } catch (e) {
    ElMessage.error('重新分块失败')
  } finally {
    rechunkLoading.value = false
  }
}

function handleSelectAll(val) {
  chunkDialog.selected = val ? chunkDialog.chunks.map(c => c.id) : []
  chunkDialog.isIndeterminate = false
}

async function handleConfirmVectorize() {
  if (chunkDialog.selected.length === 0) {
    ElMessage.warning('请至少选择一个分块')
    return
  }
  doVectorize(chunkDialog.docId, { chunk_ids: chunkDialog.selected })
}

// 表格行上的"确认向量化"按钮
async function handleVectorize(row) {
  doVectorize(row.id)
}

async function doVectorize(docId, extraData = {}) {
  progressDialog.description = '文档向量化中...'
  progressDialog.progress = 0
  progressDialog.message = '正在提交任务...'
  progressDialog.status = ''
  progressDialog.showClose = false
  progressDialog.visible = true

  try {
    const res = await vectorizeDocument(docId, extraData)
    if (res.code === 200 && res.data?.task_id) {
      startPolling(res.data.task_id, {
        onComplete: () => {
          ElMessage.success('向量化成功！')
          chunkDialog.visible = false
          fetchData()
          setTimeout(() => { progressDialog.visible = false }, 1500)
        },
        onFail: (err) => {
          ElMessage.error('向量化失败：' + err)
        },
      })
    } else {
      progressDialog.status = 'exception'
      progressDialog.message = res.msg || '提交失败'
      progressDialog.showClose = true
    }
  } catch (e) {
    progressDialog.status = 'exception'
    progressDialog.message = e.message || '请求失败'
    progressDialog.showClose = true
  }
}

// ====== RAGAS 评估 ======
const evaluateDialog = reactive({ visible: false, docId: null, result: '' })
const evaluateUploadRef = ref()
const evaluateFile = ref(null)

function handleEvaluateFileChange(file) {
  evaluateFile.value = file.raw
}

function openEvaluate(row) {
  evaluateDialog.docId = row.id
  evaluateDialog.visible = true
  evaluateDialog.result = ''
  evaluateFile.value = null
  evaluateUploadRef.value?.clearFiles()
}

async function handleEvaluate() {
  if (!evaluateFile.value) {
    ElMessage.warning('请选择评估文件')
    return
  }

  evaluateDialog.visible = false

  progressDialog.description = 'RAGAS 评估中...'
  progressDialog.progress = 0
  progressDialog.message = '正在提交评估任务...'
  progressDialog.status = ''
  progressDialog.showClose = false
  progressDialog.visible = true

  try {
    const formData = new FormData()
    formData.append('file', evaluateFile.value)
    const res = await evaluateDocument(evaluateDialog.docId, formData)
    if (res.code === 200 && res.data?.task_id) {
      startPolling(res.data.task_id, {
        onComplete: (result) => {
          evaluateDialog.visible = true
          // 把评估报告显示在评估对话框里
          evaluateDialog.result = result?.summary || '评估完成，但无摘要信息'
          progressDialog.visible = false
        },
        onFail: (err) => {
          ElMessage.error('RAGAS 评估失败：' + err)
        },
      })
    } else {
      progressDialog.status = 'exception'
      progressDialog.message = res.msg || '提交失败'
      progressDialog.showClose = true
    }
  } catch (e) {
    progressDialog.status = 'exception'
    progressDialog.message = e.message || '请求失败'
    progressDialog.showClose = true
  }
}

onMounted(fetchData)
onUnmounted(stopPolling)
</script>

<style scoped>
.search-card { margin-bottom: 16px; }
.table-toolbar { margin-bottom: 16px; }
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
.chunk-list { max-height: 500px; overflow-y: auto; }
.chunk-info { margin-bottom: 12px; color: #606266; font-size: 14px; }
.chunk-item {
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}
.chunk-item:last-child { border-bottom: none; }
.chunk-item :deep(.el-checkbox) {
  display: flex;
  align-items: flex-start;
  width: 100%;
}
.chunk-item :deep(.el-checkbox__input) {
  margin-top: 2px;
  flex-shrink: 0;
}
.chunk-item :deep(.el-checkbox__label) {
  width: 0;
  flex: 1;
}
.chunk-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.chunk-index {
  font-weight: bold;
  color: #409eff;
  font-size: 13px;
}
.chunk-tokens {
  color: #909399;
  font-size: 12px;
}
.chunk-content {
  font-size: 13px;
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
  overflow-wrap: break-word;
  word-break: break-word;
}
.rechunk-section {
  padding: 8px 0;
}
.rechunk-title {
  font-weight: bold;
  font-size: 14px;
  color: #303133;
  margin-bottom: 8px;
  display: block;
}
.rechunk-form {
  margin-top: 8px;
}
.evaluate-result {
  max-height: 400px;
  overflow-y: auto;
}
.evaluate-summary {
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
}
.progress-body { text-align: center; padding: 16px 0; }
.progress-desc { font-size: 15px; color: #303133; margin-bottom: 20px; font-weight: 500; }
.progress-message { font-size: 13px; color: #909399; margin-top: 12px; }
</style>
