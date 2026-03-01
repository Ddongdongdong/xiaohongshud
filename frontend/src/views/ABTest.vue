<template>
  <div>
    <n-page-header title="A/B 测试" subtitle="创建并追踪内容变体测试">
      <template #extra>
        <n-button type="primary" @click="showCreate = true">新建测试</n-button>
      </template>
    </n-page-header>
    <n-divider />

    <!-- 测试列表 -->
    <n-data-table :columns="testColumns" :data="tests" :loading="loading" :bordered="true" :pagination="{ pageSize: 10 }" />

    <!-- 变体详情 -->
    <n-card v-if="selectedTest" style="margin-top:20px">
      <template #header>
        <n-space align="center">
          <span>测试「{{ selectedTest.name }}」变体对比</span>
          <n-button size="small" @click="loadWinner">查看胜者</n-button>
        </n-space>
      </template>

      <n-alert v-if="winner" type="success" style="margin-bottom:12px">
        🏆 胜者：变体 {{ winner.variant_id }}「{{ winner.title }}」
        （得分 {{ winnerScore }}）
      </n-alert>

      <n-data-table :columns="variantColumns" :data="variants" :loading="loadingVariants" :bordered="true" size="small" />
    </n-card>

    <!-- 新建弹窗 -->
    <n-modal v-model:show="showCreate" preset="card" title="新建 A/B 测试" style="width:600px">
      <n-form :model="createForm" label-placement="top">
        <n-form-item label="测试名称" required>
          <n-input v-model:value="createForm.name" placeholder="例：标题风格测试 2024" />
        </n-form-item>
        <n-form-item label="基础标题" required>
          <n-input v-model:value="createForm.base_title" placeholder="原始标题" />
        </n-form-item>
        <n-form-item label="基础正文" required>
          <n-input v-model:value="createForm.base_content" type="textarea" :rows="4" placeholder="原始正文" />
        </n-form-item>
        <n-grid :cols="2" :x-gap="16">
          <n-gi>
            <n-form-item label="变体数量">
              <n-input-number v-model:value="createForm.n_variants" :min="2" :max="10" style="width:100%" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="内容风格">
              <n-select v-model:value="createForm.content_style" :options="contentStyleOptions" />
            </n-form-item>
          </n-gi>
        </n-grid>
        <n-form-item label="标题风格（可选）">
          <n-input v-model:value="createForm.title_style" placeholder="例：问句式、数字清单（留空则自由生成）" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreate = false">取消</n-button>
          <n-button type="primary" :loading="creating" @click="createTest">
            创建（AI 自动生成变体）
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import {
  NPageHeader, NDivider, NDataTable, NCard, NAlert, NModal, NForm,
  NFormItem, NInput, NInputNumber, NSelect, NButton, NSpace, NTag,
  NGrid, NGi, NProgress
} from 'naive-ui'
import http from '../api/http.js'
import { useMsg } from '../composables/useMsg.js'

const msg = useMsg()
const loading = ref(false)
const tests = ref([])
const selectedTest = ref(null)
const variants = ref([])
const loadingVariants = ref(false)
const winner = ref(null)
const showCreate = ref(false)
const creating = ref(false)

const winnerScore = computed(() => {
  if (!winner.value) return 0
  const w = winner.value
  return (w.likes || 0) * 2 + (w.collects || 0) * 3 + (w.comments || 0) * 1
})

const contentStyleOptions = [
  { label: '口语化', value: '口语化' }, { label: '活泼可爱', value: '活泼可爱' },
  { label: '专业严谨', value: '专业严谨' }, { label: '情绪共鸣', value: '情绪共鸣' },
  { label: '简洁干练', value: '简洁干练' },
]

const createForm = ref({ name: '', base_title: '', base_content: '', n_variants: 3, title_style: '', content_style: '口语化' })

const testColumns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '名称', key: 'name' },
  { title: '状态', key: 'status', width: 90, render: r => h(NTag, { type: r.status === 'active' ? 'success' : 'default', size: 'small' }, { default: () => r.status }) },
  { title: '创建时间', key: 'created_at', width: 160 },
  { title: '操作', key: 'actions', width: 90, render: r => h(NButton, { size: 'small', onClick: () => selectTest(r) }, { default: () => '查看变体' }) },
]

// 计算最高得分，用于进度条基准
const maxScore = computed(() => {
  const scores = variants.value.map(v => (v.likes || 0) * 2 + (v.collects || 0) * 3 + (v.comments || 0))
  return Math.max(...scores, 1)
})

const variantColumns = [
  { title: 'ID', key: 'variant_id', width: 60 },
  { title: '标题', key: 'title', ellipsis: { tooltip: true } },
  { title: '状态', key: 'status', width: 90, render: r => h(NTag, { type: r.status === 'published' ? 'success' : 'default', size: 'small' }, { default: () => r.status || 'pending' }) },
  { title: '点赞', key: 'likes', width: 70 },
  { title: '收藏', key: 'collects', width: 70 },
  { title: '评论', key: 'comments', width: 70 },
  {
    title: '得分',
    key: 'score',
    width: 120,
    render: r => {
      const score = (r.likes || 0) * 2 + (r.collects || 0) * 3 + (r.comments || 0)
      const pct = Math.round(score / maxScore.value * 100)
      const isWinner = winner.value && winner.value.variant_id === r.variant_id
      return h(NSpace, { vertical: true, size: 2 }, {
        default: () => [
          h('span', { style: `font-size:12px;color:${isWinner ? '#18a058' : '#666'}` }, `${score}分`),
          h(NProgress, { type: 'line', percentage: pct, color: isWinner ? '#18a058' : '#7ec8e3', showIndicator: false, height: 8 }),
        ]
      })
    }
  },
]

async function loadTests() {
  loading.value = true
  try {
    const res = await http.get('/ab-tests')
    tests.value = res.data || []
  } catch (e) {
    msg.error('加载测试失败：' + e.message)
  } finally {
    loading.value = false
  }
}

async function selectTest(test) {
  selectedTest.value = test
  winner.value = null
  loadingVariants.value = true
  try {
    const res = await http.get(`/ab-tests/${test.id}/variants`)
    variants.value = res.data || []
  } catch (e) {
    msg.error('加载变体失败：' + e.message)
  } finally {
    loadingVariants.value = false
  }
}

async function loadWinner() {
  if (!selectedTest.value) return
  try {
    const res = await http.get(`/ab-tests/${selectedTest.value.id}/winner`)
    winner.value = res.data
    if (res.data) msg.success(`胜者：${res.data.title}`)
    else msg.info(res.message || '暂无足够数据')
  } catch (e) {
    msg.error('查询胜者失败：' + e.message)
  }
}

async function createTest() {
  if (!createForm.value.name.trim() || !createForm.value.base_title.trim() || !createForm.value.base_content.trim()) {
    msg.warning('请填写测试名称、基础标题和基础正文')
    return
  }
  creating.value = true
  try {
    const payload = { ...createForm.value, title_style: createForm.value.title_style || null }
    await http.post('/ab-tests', payload)
    msg.success('测试已创建，AI 正在生成变体...')
    showCreate.value = false
    createForm.value = { name: '', base_title: '', base_content: '', n_variants: 3, title_style: '', content_style: '口语化' }
    await loadTests()
  } catch (e) {
    msg.error('创建失败：' + e.message)
  } finally {
    creating.value = false
  }
}

onMounted(loadTests)
</script>
