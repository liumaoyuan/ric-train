<template>
  <div class="store-list">
    <!-- 搜索栏 -->
    <el-card shadow="never" class="search-card">
      <el-form :model="query" inline size="default">
        <el-form-item label="省份">
          <el-input v-model="query.province" placeholder="省份" clearable style="width: 120px" />
        </el-form-item>
        <el-form-item label="城市">
          <el-input v-model="query.city" placeholder="城市" clearable style="width: 120px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 100px">
            <el-option label="营业" :value="1" />
            <el-option label="停业" :value="0" />
          </el-select>
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
        <el-table-column prop="name" label="门店名称" min-width="160" />
        <el-table-column prop="province" label="省份" width="100" />
        <el-table-column prop="city" label="城市" width="100" />
        <el-table-column prop="address" label="地址" min-width="200" show-overflow-tooltip />
        <el-table-column prop="phone" label="联系电话" width="130" />
        <el-table-column prop="open_date" label="开业日期" width="110" />
        <el-table-column label="等级" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.level === 1" type="danger" size="small">旗舰</el-tag>
            <el-tag v-else-if="row.level === 2" type="primary" size="small">标准</el-tag>
            <el-tag v-else size="small">简配</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="70" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
              {{ row.status === 1 ? '营业' : '停业' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button v-if="hasPerm('data:store:detail')" text size="small" type="primary" @click="openDetail(row)">
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
    <el-dialog v-model="detailVisible" title="门店详情" width="650px" :close-on-click-modal="false">
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="门店名称" :span="2">{{ detail.name }}</el-descriptions-item>
          <el-descriptions-item label="所在省份">{{ detail.province }}</el-descriptions-item>
          <el-descriptions-item label="所在城市">{{ detail.city }}</el-descriptions-item>
          <el-descriptions-item label="区/县">{{ detail.district || '—' }}</el-descriptions-item>
          <el-descriptions-item label="详细地址" :span="2">{{ detail.address || '—' }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ detail.phone || '—' }}</el-descriptions-item>
          <el-descriptions-item label="开业日期">{{ detail.open_date || '—' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="detail.status === 1 ? 'success' : 'danger'" size="small">
              {{ detail.status === 1 ? '营业' : '停业' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="等级">
            <el-tag v-if="detail.level === 1" type="danger" size="small">旗舰店</el-tag>
            <el-tag v-else-if="detail.level === 2" type="primary" size="small">标准店</el-tag>
            <el-tag v-else size="small">简配店</el-tag>
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
import { getStoreList, getStoreDetail } from '../../api/data'

const authStore = useAuthStore()
function hasPerm(code) { return authStore.hasPermission(code) }

const query = reactive({ page: 1, page_size: 10, province: '', city: '', status: '' })
const tableData = ref([])
const total = ref(0)
const loading = ref(false)

const detailVisible = ref(false)
const detail = ref(null)

async function fetchData() {
  loading.value = true
  try {
    const params = { ...query }
    Object.keys(params).forEach(k => { if (params[k] === '' || params[k] === null) delete params[k] })
    const res = await getStoreList(params)
    tableData.value = res.data?.data || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() { query.page = 1; fetchData() }
function handleReset() { query.province = ''; query.city = ''; query.status = ''; query.page = 1; fetchData() }

async function openDetail(row) {
  detail.value = null
  detailVisible.value = true
  try {
    const res = await getStoreDetail(row.id)
    detail.value = res.data
  } catch { /* ignore */ }
}

onMounted(fetchData)
</script>

<style scoped>
.search-card { margin-bottom: 16px; }
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
