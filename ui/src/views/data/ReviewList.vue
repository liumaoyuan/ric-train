<template>
  <div class="review-list">
    <!-- 搜索栏 -->
    <el-card shadow="never" class="search-card">
      <el-form :model="query" inline size="default">
        <el-form-item label="门店">
          <el-select v-model="query.store_id" placeholder="全部门店" clearable filterable style="width: 180px">
            <el-option v-for="s in storeOptions" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="平台">
          <el-select v-model="query.platform" placeholder="全部平台" clearable style="width: 120px">
            <el-option label="美团" value="美团" />
            <el-option label="饿了么" value="饿了么" />
            <el-option label="大众点评" value="大众点评" />
          </el-select>
        </el-form-item>
        <el-form-item label="评分">
          <el-select v-model="query.rating" placeholder="全部" clearable style="width: 100px">
            <el-option v-for="i in 5" :key="i" :label="i + '星'" :value="i" />
          </el-select>
        </el-form-item>
        <el-form-item label="情感">
          <el-select v-model="query.is_positive" placeholder="全部" clearable style="width: 100px">
            <el-option label="正面" :value="1" />
            <el-option label="中性" :value="0" />
            <el-option label="负面" :value="-1" />
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

    <!-- 表格 -->
    <el-card shadow="never">
      <el-table :data="tableData" v-loading="loading" stripe border style="width: 100%">
        <el-table-column prop="store_name" label="门店名称" min-width="140" />
        <el-table-column prop="platform" label="平台" width="100" />
        <el-table-column label="评分" width="80" align="center">
          <template #default="{ row }">
            <el-rate :model-value="row.rating" disabled size="small" />
          </template>
        </el-table-column>
        <el-table-column prop="content" label="评论内容" min-width="300" show-overflow-tooltip />
        <el-table-column label="情感" width="70" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.is_positive === 1 ? 'success' : row.is_positive === -1 ? 'danger' : 'info'"
              size="small"
            >
              {{ row.is_positive === 1 ? '正面' : row.is_positive === -1 ? '负面' : '中性' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="review_date" label="评论日期" width="110" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button v-if="hasPerm('data:review:detail')" text size="small" type="primary" @click="openDetail(row)">
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
    <el-dialog v-model="detailVisible" title="评论详情" width="700px" :close-on-click-modal="false">
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="门店" :span="2">{{ detail.store_name || ('门店ID: ' + detail.store_id) }}</el-descriptions-item>
          <el-descriptions-item label="平台">{{ detail.platform }}</el-descriptions-item>
          <el-descriptions-item label="评分">
            <el-rate :model-value="detail.rating" disabled size="small" />
          </el-descriptions-item>
          <el-descriptions-item label="情感">
            <el-tag
              :type="detail.is_positive === 1 ? 'success' : detail.is_positive === -1 ? 'danger' : 'info'"
              size="small"
            >
              {{ detail.is_positive === 1 ? '正面' : detail.is_positive === -1 ? '负面' : '中性' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="评论日期">{{ detail.review_date }}</el-descriptions-item>
          <el-descriptions-item label="评论时间">{{ detail.review_time }}</el-descriptions-item>
          <el-descriptions-item label="标签" :span="2">{{ detail.tags || '—' }}</el-descriptions-item>
          <el-descriptions-item label="评论内容" :span="2">
            <div style="white-space: pre-wrap; background: var(--el-fill-color-light); padding: 8px; border-radius: 4px;">{{ detail.content }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="回复状态" :span="1">
            <el-tag :type="detail.is_replied === 1 ? 'success' : 'info'" size="small">
              {{ detail.is_replied === 1 ? '已回复' : '未回复' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label=" " :span="1"></el-descriptions-item>
          <el-descriptions-item v-if="detail.is_replied === 1 && detail.reply_content" label="回复内容" :span="2">
            <div style="white-space: pre-wrap; background: var(--el-fill-color-light); padding: 8px; border-radius: 4px;">{{ detail.reply_content }}</div>
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
import { getReviewList, getReviewDetail, getStoreOptions } from '../../api/data'

const authStore = useAuthStore()
function hasPerm(code) { return authStore.hasPermission(code) }

const query = reactive({ page: 1, page_size: 10, store_id: '', platform: '', rating: '', is_positive: '', date_from: '', date_to: '' })
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
    const res = await getReviewList(params)
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
  query.store_id = ''; query.platform = ''; query.rating = ''; query.is_positive = ''
  query.date_from = ''; query.date_to = ''
  dateRange.value = null; query.page = 1; fetchData()
}

async function openDetail(row) {
  detail.value = null
  detailVisible.value = true
  try {
    const res = await getReviewDetail(row.id)
    detail.value = res.data
  } catch { /* ignore */ }
}

onMounted(() => { fetchData(); loadStoreOptions() })
</script>

<style scoped>
.search-card { margin-bottom: 16px; }
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
