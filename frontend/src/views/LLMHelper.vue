<template>
  <div>
    <n-page-header title="文案助手" subtitle="AI 标题生成、内容改写与相似度检测" />
    <n-divider />

    <n-grid :cols="gridCols" :x-gap="24" :y-gap="20">
      <!-- 左：标题生成 -->
      <n-gi>
        <n-card title="标题生成">
          <n-form label-placement="top">
            <n-form-item label="主题">
              <n-input v-model:value="titleTopic" placeholder="例：减脂早餐食谱" @keyup.enter="generateTitles" />
            </n-form-item>
            <n-form-item label="风格（可选）">
              <n-select v-model:value="titleStyle" :options="styleOptions" clearable placeholder="留空自动选择" />
            </n-form-item>
            <n-form-item label="数量">
              <n-input-number v-model:value="titleN" :min="1" :max="10" style="width:100%" />
            </n-form-item>
            <n-button type="primary" :loading="generatingTitles" @click="generateTitles" block>
              生成标题
            </n-button>
          </n-form>

          <template v-if="generatedTitles.length">
            <n-divider />
            <p style="font-weight:600;margin-bottom:8px">生成结果：</p>
            <n-list bordered>
              <n-list-item v-for="(t, i) in generatedTitles" :key="i">
                <n-space align="center" justify="space-between" style="width:100%">
                  <span style="flex:1;margin-right:8px">{{ t }}</span>
                  <n-button size="tiny" @click="copyText(t)">复制</n-button>
                </n-space>
              </n-list-item>
            </n-list>
          </template>
        </n-card>
      </n-gi>

      <!-- 右：内容改写 -->
      <n-gi>
        <n-card title="内容改写">
          <n-form label-placement="top">
            <n-form-item label="原始正文">
              <n-input v-model:value="originalContent" type="textarea" :rows="6" placeholder="粘贴原始正文..." />
            </n-form-item>
            <n-form-item label="改写风格">
              <n-select v-model:value="rewriteStyle" :options="rewriteStyleOptions" />
            </n-form-item>
            <n-button type="primary" :loading="rewriting" @click="rewriteContent" block>
              改写内容
            </n-button>
          </n-form>

          <template v-if="rewrittenContent">
            <n-divider />
            <n-space align="center" justify="space-between" style="margin-bottom:8px">
              <span style="font-weight:600">改写结果：</span>
              <n-space>
                <n-tooltip>
                  <template #trigger>
                    <n-tag :type="similarityTagType" size="small" style="cursor:help">
                      相似度 {{ (similarity * 100).toFixed(1) }}%
                    </n-tag>
                  </template>
                  {{ similarityTip }}
                </n-tooltip>
                <n-button size="tiny" @click="copyText(rewrittenContent)">复制</n-button>
              </n-space>
            </n-space>
            <n-input :value="rewrittenContent" type="textarea" :rows="7" readonly />
          </template>
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  NPageHeader, NDivider, NGrid, NGi, NCard, NForm, NFormItem,
  NInput, NInputNumber, NSelect, NButton, NList, NListItem,
  NSpace, NTag, NTooltip
} from 'naive-ui'
import http from '../api/http.js'
import { useMsg } from '../composables/useMsg.js'

const msg = useMsg()

const titleTopic = ref('')
const titleStyle = ref(null)
const titleN = ref(3)
const generatingTitles = ref(false)
const generatedTitles = ref([])

const originalContent = ref('')
const rewriteStyle = ref('口语化')
const rewriting = ref(false)
const rewrittenContent = ref('')
const similarity = ref(0)

const styleOptions = [
  { label: '吸引眼球', value: '吸引眼球' }, { label: '问句式', value: '问句式' },
  { label: '数字清单', value: '数字清单' }, { label: '情绪共鸣', value: '情绪共鸣' },
  { label: '悬念式', value: '悬念式' },
]
const rewriteStyleOptions = [
  { label: '口语化', value: '口语化' }, { label: '活泼可爱', value: '活泼可爱' },
  { label: '专业严谨', value: '专业严谨' }, { label: '情绪共鸣', value: '情绪共鸣' },
  { label: '简洁干练', value: '简洁干练' },
]

// 响应式列
const winWidth = ref(window.innerWidth)
const onResize = () => { winWidth.value = window.innerWidth }
onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))
const gridCols = computed(() => winWidth.value > 768 ? 2 : 1)

const similarityTagType = computed(() => similarity.value > 0.7 ? 'error' : similarity.value > 0.5 ? 'warning' : 'success')
const similarityTip = computed(() => {
  if (similarity.value > 0.7) return '相似度过高，建议重新改写'
  if (similarity.value > 0.5) return '相似度偏高，可进一步修改'
  return '相似度适中，改写效果良好'
})

async function generateTitles() {
  if (!titleTopic.value.trim()) { msg.warning('请输入主题'); return }
  generatingTitles.value = true
  try {
    const res = await http.post('/llm/titles', { topic: titleTopic.value, n: titleN.value, style: titleStyle.value || null })
    generatedTitles.value = res.data?.titles || []
    if (generatedTitles.value.length) msg.success(`已生成 ${generatedTitles.value.length} 个标题`)
  } catch (e) {
    msg.error('生成失败：' + e.message)
  } finally {
    generatingTitles.value = false
  }
}

async function rewriteContent() {
  if (!originalContent.value.trim()) { msg.warning('请输入原始正文'); return }
  rewriting.value = true
  try {
    const res = await http.post('/llm/rewrite', { original: originalContent.value, style: rewriteStyle.value })
    rewrittenContent.value = res.data?.rewritten || ''
    if (originalContent.value && rewrittenContent.value) {
      const simRes = await http.post('/llm/similarity', { text_a: originalContent.value, text_b: rewrittenContent.value })
      similarity.value = simRes.data?.similarity ?? 0
    }
    msg.success('改写完成')
  } catch (e) {
    msg.error('改写失败：' + e.message)
  } finally {
    rewriting.value = false
  }
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    msg.success('已复制到剪贴板')
  } catch {
    msg.error('复制失败，请手动选择复制')
  }
}
</script>
