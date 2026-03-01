<template>
  <div>
    <n-page-header title="数据看板" subtitle="笔记指标总览">
      <template #extra>
        <n-button type="primary" :loading="fetching" @click="triggerFetch">
          手动抓取指标
        </n-button>
      </template>
    </n-page-header>

    <n-divider />

    <!-- 统计卡片 -->
    <n-grid :cols="gridCols" :x-gap="16" :y-gap="16" style="margin-bottom: 20px">
      <n-gi>
        <n-card size="small"><n-statistic label="帖子总数" :value="stats.total" /></n-card>
      </n-gi>
      <n-gi>
        <n-card size="small"><n-statistic label="总曝光量" :value="stats.totalExposure"><template #suffix>次</template></n-statistic></n-card>
      </n-gi>
      <n-gi>
        <n-card size="small"><n-statistic label="平均 CTR" :value="stats.avgCtr" :precision="2"><template #suffix>%</template></n-statistic></n-card>
      </n-gi>
      <n-gi>
        <n-card size="small">
          <n-statistic label="低效帖数" :value="lowPerfRows.length">
            <template #prefix>
              <n-tag v-if="lowPerfRows.length > 0" type="error" size="small" style="margin-right:4px">!</n-tag>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 低效帖告警 -->
    <n-card v-if="lowPerfRows.length > 0" title="⚠️ 低效帖告警" style="margin-bottom: 20px">
      <n-alert type="warning" style="margin-bottom: 12px">
        以下帖子表现低于阈值，建议优化标题/封面或重新发布
      </n-alert>
      <n-data-table :columns="lowPerfColumns" :data="lowPerfRows" :bordered="false" size="small" :max-height="200" />
    </n-card>

    <!-- 全量指标表格 -->
    <n-card title="所有帖子指标">
      <n-spin :show="loading">
        <n-empty v-if="!loading && metricsRows.length === 0" description="暂无数据，请先手动抓取指标" style="padding: 40px 0" />
        <n-data-table
          v-else
          :columns="metricsColumns"
          :data="metricsRows"
          :bordered="true"
          :pagination="{ pageSize: 10 }"
          size="small"
        />
      </n-spin>
    </n-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  NPageHeader, NDivider, NGrid, NGi, NStatistic, NCard, NDataTable,
  NAlert, NTag, NButton, NSpin, NEmpty
} from 'naive-ui'
import http from '../api/http.js'
import { useMsg } from '../composables/useMsg.js'

const msg = useMsg()
const loading = ref(false)
const fetching = ref(false)
const metricsRows = ref([])
const lowPerfRows = ref([])

// 响应式列数
const winWidth = ref(window.innerWidth)
const onResize = () => { winWidth.value = window.innerWidth }
onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))
const gridCols = computed(() => winWidth.value > 1024 ? 4 : winWidth.value > 768 ? 2 : 1)

const stats = computed(() => {
  const rows = metricsRows.value
  const total = rows.length
  const totalExposure = rows.reduce((s, r) => s + (r.exposure || 0), 0)
  const avgCtr = total > 0 ? rows.reduce((s, r) => s + (r.ctr || 0), 0) / total : 0
  return { total, totalExposure, avgCtr }
})

const metricsColumns = [
  { title: '标题', key: 'title', ellipsis: { tooltip: true } },
  { title: '发布时间', key: 'publish_time', width: 160 },
  { title: '曝光', key: 'exposure', sorter: (a, b) => (a.exposure || 0) - (b.exposure || 0) },
  { title: 'CTR%', key: 'ctr', render: r => r.ctr?.toFixed(2) ?? '-', sorter: (a, b) => (a.ctr || 0) - (b.ctr || 0) },
  { title: '点赞', key: 'likes', sorter: (a, b) => (a.likes || 0) - (b.likes || 0) },
  { title: '收藏', key: 'collects', sorter: (a, b) => (a.collects || 0) - (b.collects || 0) },
  { title: '评论', key: 'comments' },
  { title: '分享', key: 'shares' },
  { title: '涨粉', key: 'followers' },
]

const lowPerfColumns = [
  { title: '标题', key: 'title', ellipsis: { tooltip: true } },
  { title: '曝光', key: 'exposure' },
  { title: 'CTR%', key: 'ctr', render: r => r.ctr?.toFixed(2) ?? '-' },
  { title: '点赞', key: 'likes' },
  { title: '收藏', key: 'collects' },
]

async function loadMetrics() {
  loading.value = true
  try {
    const [mr, lr] = await Promise.all([
      http.get('/metrics'),
      http.get('/metrics/low-perf'),
    ])
    metricsRows.value = mr.data || []
    lowPerfRows.value = lr.data || []
  } catch (e) {
    msg.error('加载指标失败：' + e.message)
  } finally {
    loading.value = false
  }
}

async function triggerFetch() {
  fetching.value = true
  try {
    await http.post('/metrics/fetch')
    msg.info('抓取任务已提交，稍后刷新查看结果')
    setTimeout(loadMetrics, 3000)
  } catch (e) {
    msg.error('提交抓取失败：' + e.message)
  } finally {
    fetching.value = false
  }
}

onMounted(loadMetrics)
</script>
