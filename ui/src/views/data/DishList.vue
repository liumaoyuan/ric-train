<template>
  <div class="dish-list">
    <!-- 搜索栏 -->
    <el-card shadow="never" class="search-card">
      <el-form :model="query" inline size="default">
        <el-form-item label="菜品分类">
          <el-select v-model="query.category" placeholder="全部分类" clearable style="width: 130px">
            <el-option v-for="c in categoryOptions" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 100px">
            <el-option label="上架" :value="1" />
            <el-option label="下架" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键字">
          <el-input v-model="query.keyword" placeholder="菜品名称" clearable style="width: 160px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格 -->
    <el-card shadow="never">
      <el-table :data="tableData" v-loading="loading" stripe border style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="菜品名称" min-width="140" />
        <el-table-column prop="category" label="分类" width="90" />
        <el-table-column prop="price" label="价格(元)" width="100" align="right">
          <template #default="{ row }">¥{{ parseFloat(row.price).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="cost" label="成本(元)" width="100" align="right">
          <template #default="{ row }">{{ row.cost ? '¥' + parseFloat(row.cost).toFixed(2) : '—' }}</template>
        </el-table-column>
        <el-table-column label="辣度" width="70" align="center">
          <template #default="{ row }">
            <span v-if="row.spicy_level === 0">不辣</span>
            <span v-else-if="row.spicy_level === 1" style="color: #e6a23c">微辣</span>
            <span v-else-if="row.spicy_level === 2" style="color: #f56c6c">中辣</span>
            <span v-else style="color: #f56c6c">重辣</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="70" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
              {{ row.status === 1 ? '上架' : '下架' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button v-if="hasPerm('data:dish:detail')" text size="small" type="primary" @click="openDetail(row)">
              详情
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

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="菜品详情" width="600px" :close-on-click-modal="false">
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="菜品名称" :span="2">{{ detail.name }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ detail.category }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="detail.status === 1 ? 'success' : 'danger'" size="small">
              {{ detail.status === 1 ? '上架' : '下架' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="价格(元)">{{ parseFloat(detail.price).toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="成本(元)">{{ detail.cost ? '¥' + parseFloat(detail.cost).toFixed(2) : '—' }}</el-descriptions-item>
          <el-descriptions-item label="单位">{{ detail.unit }}</el-descriptions-item>
          <el-descriptions-item label="辣度">
            <span v-if="detail.spicy_level === 0">不辣</span>
            <span v-else-if="detail.spicy_level === 1">微辣</span>
            <span v-else-if="detail.spicy_level === 2">中辣</span>
            <span v-else>重辣</span>
          </el-descriptions-item>
          <el-descriptions-item label=" popularity">{{ detail.popularity }}</el-descriptions-item>
          <el-descriptions-item label="图片" :span="2">
            <el-image v-if="detail.image_url" :src="detail.image_url" style="width: 200px" fit="cover" />
            <span v-else>—</span>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">{{ detail.created_at }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '../../store/auth'
import { getDishList, getDishDetail } from '../../api/data'

const authStore = useAuthStore()
function hasPerm(code) { return authStore.hasPermission(code) }

const query = reactive({ page: 1, page_size: 10, category: '', status: '', keyword: '' })
const tableData = ref([])
const total = ref(0)
const loading = ref(false)

const categoryOptions = ['热菜', '凉菜', '主食', '汤品', '饮品', '配菜']

// 详情
const detailVisible = ref(false)
const detail = ref(null)

async function fetchData() {
  loading.value = true
  try {
    const params = { ...query }
    Object.keys(params).forEach(k => { if (params[k] === '' || params[k] === null) delete params[k] })
    const res = await getDishList(params)
    tableData.value = res.data?.data || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() { query.page = 1; fetchData() }
function handleReset() { query.category = ''; query.status = ''; query.keyword = ''; query.page = 1; fetchData() }

async function openDetail(row) {
  detail.value = null
  detailVisible.value = true
  try {
    const res = await getDishDetail(row.id)
    detail.value = res.data
  } catch { /* ignore */ }
}

onMounted(fetchData)
</script>

<style scoped>
.search-card { margin-bottom: 16px; }
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
