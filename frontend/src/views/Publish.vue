<template>
  <div>
    <n-page-header title="内容发布" subtitle="图文 / 视频发布到小红书" />
    <n-divider />

    <n-tabs v-model:value="tab" type="line">
      <!-- 图文 -->
      <n-tab-pane name="image" tab="图文发布">
        <n-form ref="imageFormRef" :model="imageForm" label-placement="top" style="max-width: 700px" :rules="imageRules">
          <n-form-item label="标题" path="title" required>
            <n-input v-model:value="imageForm.title" placeholder="请输入笔记标题（建议20字以内）" :maxlength="100" show-count />
          </n-form-item>
          <n-form-item label="正文内容" path="content" required>
            <n-input v-model:value="imageForm.content" type="textarea" placeholder="请输入正文，可加 #话题标签" :rows="6" />
          </n-form-item>
          <n-form-item label="图片 URL（每行一个）">
            <n-input v-model:value="imageUrlsRaw" type="textarea" placeholder="https://example.com/img1.jpg" :rows="3" />
          </n-form-item>
          <n-form-item label="本地图片路径（每行一个）">
            <n-input v-model:value="imagePathsRaw" type="textarea" placeholder="C:\path\to\image.jpg" :rows="3" />
          </n-form-item>
          <n-form-item label="账号">
            <n-input v-model:value="imageForm.account" placeholder="留空使用默认账号" />
          </n-form-item>
          <n-form-item>
            <n-space>
              <n-switch v-model:value="imageForm.headless">
                <template #checked>无头模式</template>
                <template #unchecked>显示浏览器</template>
              </n-switch>
              <n-switch v-model:value="imageForm.auto_publish">
                <template #checked>自动发布</template>
                <template #unchecked>仅填写不发布</template>
              </n-switch>
            </n-space>
          </n-form-item>
          <n-button type="primary" :loading="publishing" @click="handlePublishImage">发布图文</n-button>
        </n-form>
      </n-tab-pane>

      <!-- 视频 -->
      <n-tab-pane name="video" tab="视频发布">
        <n-form ref="videoFormRef" :model="videoForm" label-placement="top" style="max-width: 700px" :rules="videoRules">
          <n-form-item label="标题" path="title" required>
            <n-input v-model:value="videoForm.title" placeholder="请输入视频标题" :maxlength="100" show-count />
          </n-form-item>
          <n-form-item label="正文内容" path="content" required>
            <n-input v-model:value="videoForm.content" type="textarea" placeholder="视频简介" :rows="4" />
          </n-form-item>
          <n-form-item label="本地视频路径">
            <n-input v-model:value="videoForm.video" placeholder="C:\path\to\video.mp4" />
          </n-form-item>
          <n-form-item label="视频 URL">
            <n-input v-model:value="videoForm.video_url" placeholder="https://example.com/video.mp4" />
          </n-form-item>
          <n-form-item label="账号">
            <n-input v-model:value="videoForm.account" placeholder="留空使用默认账号" />
          </n-form-item>
          <n-form-item>
            <n-space>
              <n-switch v-model:value="videoForm.headless">
                <template #checked>无头模式</template>
                <template #unchecked>显示浏览器</template>
              </n-switch>
              <n-switch v-model:value="videoForm.auto_publish">
                <template #checked>自动发布</template>
                <template #unchecked>仅填写不发布</template>
              </n-switch>
            </n-space>
          </n-form-item>
          <n-button type="primary" :loading="publishing" @click="handlePublishVideo">发布视频</n-button>
        </n-form>
      </n-tab-pane>
    </n-tabs>

    <!-- 发布确认弹窗 -->
    <n-modal v-model:show="showConfirm" preset="dialog" title="确认发布" type="warning"
      positive-text="确认发布" negative-text="取消"
      @positive-click="doPublish" @negative-click="showConfirm = false">
      <p>即将发布「{{ pendingTitle }}」</p>
      <p v-if="pendingAutoPublish" style="color:#ff2442; margin-top:8px">⚠️ 已开启「自动发布」，将直接提交到小红书</p>
      <p v-else style="margin-top:8px">仅填写表单，不会自动点击发布按钮</p>
    </n-modal>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import {
  NPageHeader, NDivider, NTabs, NTabPane, NForm, NFormItem,
  NInput, NSwitch, NButton, NSpace, NModal
} from 'naive-ui'
import http from '../api/http.js'
import { useMsg } from '../composables/useMsg.js'

const msg = useMsg()
const tab = ref('image')
const publishing = ref(false)
const showConfirm = ref(false)

const imageFormRef = ref(null)
const videoFormRef = ref(null)
const imageUrlsRaw = ref('')
const imagePathsRaw = ref('')

const imageForm = ref({ title: '', content: '', account: '', headless: true, auto_publish: false })
const videoForm = ref({ title: '', content: '', video: '', video_url: '', account: '', headless: true, auto_publish: false })

const imageRules = {
  title: [{ required: true, message: '标题不能为空', trigger: 'blur' }],
  content: [{ required: true, message: '正文不能为空', trigger: 'blur' }],
}
const videoRules = {
  title: [{ required: true, message: '标题不能为空', trigger: 'blur' }],
  content: [{ required: true, message: '正文不能为空', trigger: 'blur' }],
}

// 待发布的信息（用于确认弹窗）
let pendingTitle = ref('')
let pendingAutoPublish = ref(false)
let pendingFn = null

async function handlePublishImage() {
  try { await imageFormRef.value?.validate() } catch { return }
  pendingTitle.value = imageForm.value.title
  pendingAutoPublish.value = imageForm.value.auto_publish
  pendingFn = publishImage
  showConfirm.value = true
}

async function handlePublishVideo() {
  try { await videoFormRef.value?.validate() } catch { return }
  if (!videoForm.value.video && !videoForm.value.video_url) {
    msg.error('请填写本地视频路径或视频 URL')
    return
  }
  pendingTitle.value = videoForm.value.title
  pendingAutoPublish.value = videoForm.value.auto_publish
  pendingFn = publishVideo
  showConfirm.value = true
}

async function doPublish() {
  showConfirm.value = false
  if (pendingFn) await pendingFn()
}

async function publishImage() {
  publishing.value = true
  try {
    const payload = {
      ...imageForm.value,
      image_urls: imageUrlsRaw.value.split('\n').map(s => s.trim()).filter(Boolean),
      images: imagePathsRaw.value.split('\n').map(s => s.trim()).filter(Boolean),
      account: imageForm.value.account || null,
    }
    await http.post('/publish/image', payload)
    msg.success('图文发布成功')
  } catch (e) {
    msg.error('发布失败：' + e.message)
  } finally {
    publishing.value = false
  }
}

async function publishVideo() {
  publishing.value = true
  try {
    const payload = {
      ...videoForm.value,
      account: videoForm.value.account || null,
      video: videoForm.value.video || null,
      video_url: videoForm.value.video_url || null,
    }
    await http.post('/publish/video', payload)
    msg.success('视频发布成功')
  } catch (e) {
    msg.error('发布失败：' + e.message)
  } finally {
    publishing.value = false
  }
}
</script>
