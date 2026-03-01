<template>
  <div>
    <n-page-header title="笔记搜索" subtitle="搜索小红书笔记并互动" />
    <n-divider />

    <n-space align="center" style="margin-bottom: 16px">
      <n-input v-model:value="keyword" placeholder="输入关键词搜索..." style="width: 280px"
        clearable @keyup.enter="doSearch" />
      <n-select v-model:value="filters.sort_by" placeholder="排序方式" :options="sortOptions" style="width: 140px" clearable />
      <n-select v-model:value="filters.note_type" placeholder="笔记类型" :options="noteTypeOptions" style="width: 120px" clearable />
      <n-button type="primary" :loading="searching" @click="doSearch">搜索</n-button>
    </n-space>

    <n-spin :show="searching">
      <n-grid v-if="results.length" :cols="gridCols" :x-gap="16" :y-gap="16">
        <n-gi v-for="item in results" :key="item.id || item.note_id">
          <n-card hoverable style="cursor:pointer" @click="openDetail(item)">
            <template #cover>
              <img v-if="item.cover || item.image_url" :src="item.cover || item.image_url"
                style="width:100%;height:160px;object-fit:cover" @error="$event.target.style.display='none'" />
            </template>
            <n-ellipsis :line-clamp="2" style="font-weight:500">
              {{ item.title || item.display_title || '（无标题）' }}
            </n-ellipsis>
            <n-space style="margin-top:8px">
              <n-tag size="small">❤️ {{ item.likes || item.liked_count || 0 }}</n-tag>
              <n-tag size="small">⭐ {{ item.collects || item.collected_count || 0 }}</n-tag>
              <n-tag size="small">💬 {{ item.comments || item.comment_count || 0 }}</n-tag>
            </n-space>
          </n-card>
        </n-gi>
      </n-grid>
      <n-empty v-else-if="!searching && searched" description="暂无搜索结果" style="padding:40px 0" />
    </n-spin>

    <!-- 详情抽屉 -->
    <n-drawer v-model:show="drawerVisible" :width="480" placement="right">
      <n-drawer-content :title="selectedItem?.title || '笔记详情'" closable>
        <n-spin :show="loadingDetail">
          <div v-if="detail">
            <n-descriptions bordered :column="1" size="small">
              <n-descriptions-item label="笔记ID">{{ detail.note_id || selectedItem?.id }}</n-descriptions-item>
              <n-descriptions-item label="作者">{{ detail.author?.nickname || detail.user?.nickname || '-' }}</n-descriptions-item>
              <n-descriptions-item label="发布时间">{{ detail.time || detail.created_at || '-' }}</n-descriptions-item>
              <n-descriptions-item label="点赞">{{ detail.liked_count || detail.likes || 0 }}</n-descriptions-item>
              <n-descriptions-item label="收藏">{{ detail.collected_count || detail.collects || 0 }}</n-descriptions-item>
              <n-descriptions-item label="评论">{{ detail.comment_count || detail.comments || 0 }}</n-descriptions-item>
            </n-descriptions>
            <n-divider />
            <div style="white-space:pre-wrap;font-size:14px;line-height:1.6">
              {{ detail.desc || detail.content || '（无正文）' }}
            </div>
            <n-divider />
            <p style="font-weight:600;margin-bottom:8px">发表评论</p>
            <n-input v-model:value="commentContent" type="textarea" placeholder="输入评论内容..." :rows="3" style="margin-bottom:8px" />
            <n-button type="primary" size="small" :loading="commenting" @click="postComment">发表评论</n-button>
          </div>
        </n-spin>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  NPageHeader, NDivider, NSpace, NInput, NSelect, NButton, NSpin,
  NGrid, NGi, NCard, NEllipsis, NTag, NEmpty, NDrawer, NDrawerContent,
  NDescriptions, NDescriptionsItem
} from 'naive-ui'
import http from '../api/http.js'
import { useMsg } from '../composables/useMsg.js'

const msg = useMsg()
const keyword = ref('')
const searching = ref(false)
const searched = ref(false)
const results = ref([])
const filters = ref({ sort_by: null, note_type: null })

const sortOptions = [
  { label: '综合', value: '综合' }, { label: '最新', value: '最新' },
  { label: '最多点赞', value: '最多点赞' }, { label: '最多评论', value: '最多评论' },
  { label: '最多收藏', value: '最多收藏' },
]
const noteTypeOptions = [
  { label: '全部', value: '' }, { label: '图文', value: '图文' }, { label: '视频', value: '视频' },
]

const drawerVisible = ref(false)
const selectedItem = ref(null)
const detail = ref(null)
const loadingDetail = ref(false)
const commentContent = ref('')
const commenting = ref(false)

// 响应式列
const winWidth = ref(window.innerWidth)
const onResize = () => { winWidth.value = window.innerWidth }
onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))
const gridCols = computed(() => winWidth.value > 1024 ? 3 : winWidth.value > 768 ? 2 : 1)

async function doSearch() {
  if (!keyword.value.trim()) return
  searching.value = true
  searched.value = false
  try {
    const params = { keyword: keyword.value }
    if (filters.value.sort_by) params.sort_by = filters.value.sort_by
    if (filters.value.note_type) params.note_type = filters.value.note_type
    const res = await http.get('/feeds', { params })
    results.value = res.data?.feeds || res.data || []
    searched.value = true
    if (results.value.length === 0) msg.info('未找到相关笔记')
  } catch (e) {
    msg.error('搜索失败：' + e.message)
  } finally {
    searching.value = false
  }
}

async function openDetail(item) {
  selectedItem.value = item
  drawerVisible.value = true
  loadingDetail.value = true
  detail.value = null
  commentContent.value = ''
  try {
    const feedId = item.id || item.note_id
    const xsecToken = item.xsec_token || ''
    if (feedId) {
      const res = await http.get(`/feeds/${feedId}`, { params: { xsec_token: xsecToken } })
      detail.value = res.data || item
    } else {
      detail.value = item
    }
  } catch {
    detail.value = item
  } finally {
    loadingDetail.value = false
  }
}

async function postComment() {
  if (!commentContent.value.trim()) { msg.warning('评论内容不能为空'); return }
  commenting.value = true
  try {
    const feedId = selectedItem.value?.id || selectedItem.value?.note_id
    const xsecToken = selectedItem.value?.xsec_token || ''
    await http.post(`/feeds/${feedId}/comment`, { xsec_token: xsecToken, content: commentContent.value })
    msg.success('评论已发表')
    commentContent.value = ''
  } catch (e) {
    msg.error('评论失败：' + e.message)
  } finally {
    commenting.value = false
  }
}
</script>
