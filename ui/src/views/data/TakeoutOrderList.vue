<template>
  <div class="takeout-order-list">
    <el-card shadow="never" class="search-card">
      <el-form :model="query" inline size="default">
        <el-form-item label="门店">
          <el-select v-model="query.store_id" placeholder="全部门店" clearable filterable style="width: 180px">
            <el-option v-for="s in storeOptions" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
            @change="handleDateChange"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="tableData" v-loading="loading" stripe border style="width: 100%">
        <el-table-column prop="order_no" label="订单号" min-width="180">
          <template #default="{ row }">
            <el-link type="primary" underline @click="openDetail(row)">{{ row.order_no }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="store_name" label="门店名称" min-width="140" />
        <el-table-column prop="total_amount" label="金额(元)" width="110" align="right">
          <template #default="{ row }">{{ row.total_amount.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="platform" label="外卖平台" width="130" />
        <el-table-column prop="order_time" label="下单时间" width="170">
          <template #default="{ row }">{{ formatDateTime(row.order_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button v-if="hasPerm('data:order:detail')" text size="small" type="primary" @click="openDetail(row)">
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

    <el-dialog v-model="detailVisible" title="订单详情" width="800px" :close-on-click-modal="false">
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单号" :span="2">{{ detail.order_no }}</el-descriptions-item>
          <el-descriptions-item label="门店">{{ detail.store_name }}</el-descriptions-item>
          <el-descriptions-item label="订单类型">外卖</el-descriptions-item>
          <el-descriptions-item label="外卖平台">{{ detail.platform }}</el-descriptions-item>
          <el-descriptions-item label="金额(元)">{{ detail.total_amount.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="下单时间">{{ formatDateTime(detail.order_time) }}</el-descriptions-item>
          <el-descriptions-item label="会员ID">{{ detail.member_id || '—' }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin: 16px 0 8px">菜品明细</h4>
        <el-table :data="detail.items" stripe border style="width: 100%">
          <el-table-column prop="dish_name" label="菜品名称" min-width="140" />
          <el-table-column prop="quantity" label="数量" width="70" align="center" />
          <el-table-column prop="price" label="单价(元)" width="100" align="right">
            <template #default="{ row }">{{ row.price.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="amount" label="小计(元)" width="100" align="right">
            <template #default="{ row }">{{ row.amount.toFixed(2) }}</template>
          </el-table-column>
        </el-table>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '../../store/auth'
import { getTakeoutOrderList, getTakeoutOrderDetail, getStoreOptions } from '../../api/data'

const authStore = useAuthStore()
function hasPerm(code) { return authStore.hasPermission(code) }

function formatDateTime(dateStr) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
}

const query = reactive({ page: 1, page_size: 10, store_id: '', date_from: '', date_to: '' })
const dateRange = ref(null)
const tableData = ref([])
const total = ref(0)
const loading = ref(false)
const storeOptions = ref([])

const detailVisible = ref(false)
const detail = ref(null)

function handleDateChange(val) {
  if (val) {
    query.date_from = val[0]
    query.date_to = val[1]
  } else {
    query.date_from = ''
    query.date_to = ''
  }
}

async function fetchData() {
  loading.value = true
  try {
    const params = { ...query }
    Object.keys(params).forEach(k => { if (params[k] === '' || params[k] === null) delete params[k] })
    const res = await getTakeoutOrderList(params)
    tableData.value = res.data?.data || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

async function loadStoreOptions() {
  storeOptions.value = await getStoreOptions()
}

function handleSearch() { query.page = 1; fetchData() }
function handleReset() {
  query.store_id = ''; query.date_from = ''; query.date_to = ''
  dateRange.value = null; query.page = 1; fetchData()
}

async function openDetail(row) {
  detail.value = null
  detailVisible.value = true
  try {
    const res = await getTakeoutOrderDetail(row.order_no)
    detail.value = res.data
  } catch { /* ignore */ }
}

onMounted(() => { fetchData(); loadStoreOptions() })
</script>

<style scoped>
.search-card { margin-bottom: 16px; }
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
h4 { font-weight: 600; color: var(--el-text-color-primary); }
</style>
