<template>
  <div class="summary-list">
    <!-- 搜索栏 -->
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

    <!-- 统计概览 -->
    <el-row :gutter="16" class="stat-row" v-if="stat.store_count > 0">
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">总营业额</div>
          <div class="stat-value primary">¥{{ stat.total_revenue.toLocaleString() }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">总订单数</div>
          <div class="stat-value success">{{ stat.total_orders.toLocaleString() }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">平均客单价</div>
          <div class="stat-value warning">¥{{ stat.avg_price.toFixed(2) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">门店数 / 天数</div>
          <div class="stat-value info">{{ stat.store_count }}店 / {{ stat.day_count }}天</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 表格 -->
    <el-card shadow="never">
      <el-table :data="tableData" v-loading="loading" stripe border style="width: 100%">
        <el-table-column prop="summary_date" label="日期" width="110" />
        <el-table-column prop="store_name" label="门店名称" min-width="140" />
        <el-table-column prop="total_revenue" label="总营业额" width="120" align="right">
          <template #default="{ row }">¥{{ parseFloat(row.total_revenue).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="total_orders" label="总订单数" width="90" align="center" />
        <el-table-column prop="avg_price" label="客单价" width="90" align="right">
          <template #default="{ row }">¥{{ parseFloat(row.avg_price).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="dine_in_revenue" label="堂食收入" width="120" align="right">
          <template #default="{ row }">¥{{ parseFloat(row.dine_in_revenue).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="takeout_revenue" label="外卖收入" width="120" align="right">
          <template #default="{ row }">¥{{ parseFloat(row.takeout_revenue).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="peak_hour_revenue" label="高峰收入" width="120" align="right">
          <template #default="{ row }">¥{{ parseFloat(row.peak_hour_revenue || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="dish_total_count" label="菜品总份数" width="100" align="center" />
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { getDailySummaryList, getDailySummaryStat, getStoreOptions } from '../../api/data'

const query = reactive({ page: 1, page_size: 10, store_id: '', date_from: '', date_to: '' })
const dateRange = ref(null)
const tableData = ref([])
const total = ref(0)
const loading = ref(false)
const storeOptions = ref([])
const stat = ref({})

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
    const res = await getDailySummaryList(params)
    tableData.value = res.data?.data || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

async function fetchStat() {
  const params = {}
  if (query.store_id) params.store_id = query.store_id
  if (query.date_from) params.date_from = query.date_from
  if (query.date_to) params.date_to = query.date_to
  const res = await getDailySummaryStat(params)
  stat.value = res.data || {}
}

async function loadStoreOptions() {
  storeOptions.value = await getStoreOptions()
}

function handleSearch() { query.page = 1; fetchData(); fetchStat() }
function handleReset() {
  query.store_id = ''; query.date_from = ''; query.date_to = ''
  dateRange.value = null; query.page = 1; fetchData(); fetchStat()
}

onMounted(() => { fetchData(); fetchStat(); loadStoreOptions() })
</script>

<style scoped>
.search-card { margin-bottom: 16px; }
.stat-row { margin-bottom: 16px; }
.stat-card { text-align: center; }
.stat-label { font-size: 13px; color: var(--el-text-color-secondary); margin-bottom: 8px; }
.stat-value { font-size: 22px; font-weight: 700; }
.stat-value.primary { color: var(--el-color-primary); }
.stat-value.success { color: var(--el-color-success); }
.stat-value.warning { color: var(--el-color-warning); }
.stat-value.info { color: var(--el-color-info); }
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
