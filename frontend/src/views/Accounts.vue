<template>
  <div>
    <n-page-header title="账号管理" subtitle="管理多个小红书账号">
      <template #extra>
        <n-button type="primary" @click="showAdd = true">添加账号</n-button>
      </template>
    </n-page-header>
    <n-divider />

    <n-data-table :columns="columns" :data="accounts" :loading="loading" :bordered="true" />

    <!-- 浏览器控制 -->
    <n-card title="浏览器控制" style="margin-top: 20px">
      <n-space align="center" wrap>
        <n-input v-model:value="browserAccount" placeholder="账号名（留空用默认）" style="width:200px" />
        <n-switch v-model:value="headless">
          <template #checked>无头</template>
          <template #unchecked>显示</template>
        </n-switch>
        <n-button @click="startBrowser" :loading="browserLoading">启动浏览器</n-button>
        <n-button @click="stopBrowser" :loading="browserLoading">停止浏览器</n-button>
        <n-button type="primary" @click="openLogin" :loading="browserLoading">打开登录页</n-button>
      </n-space>
    </n-card>

    <!-- 添加账号弹窗 -->
    <n-modal v-model:show="showAdd" preset="card" title="添加账号" style="width:400px">
      <n-form :model="addForm" label-placement="top">
        <n-form-item label="账号名（唯一标识）" required>
          <n-input v-model:value="addForm.name" placeholder="例：account1" />
        </n-form-item>
        <n-form-item label="显示名称">
          <n-input v-model:value="addForm.alias" placeholder="例：主号" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAdd = false">取消</n-button>
          <n-button type="primary" :loading="adding" @click="addAccount">添加</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 删除确认弹窗 -->
    <n-modal v-model:show="showDeleteConfirm" preset="dialog" title="确认删除" type="error"
      positive-text="确认删除" negative-text="取消"
      @positive-click="doDelete" @negative-click="showDeleteConfirm = false">
      <p>确定要删除账号「<b>{{ deletingName }}</b>」吗？此操作不可撤销。</p>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, h } from 'vue'
import {
  NPageHeader, NDivider, NDataTable, NButton, NSpace, NModal,
  NForm, NFormItem, NInput, NTag, NCard, NSwitch
} from 'naive-ui'
import http from '../api/http.js'
import { useMsg } from '../composables/useMsg.js'

const msg = useMsg()
const loading = ref(false)
const accounts = ref([])
const showAdd = ref(false)
const adding = ref(false)
const addForm = ref({ name: '', alias: '' })

const showDeleteConfirm = ref(false)
const deletingName = ref('')

const browserAccount = ref('')
const headless = ref(false)
const browserLoading = ref(false)

const columns = [
  { title: '账号名', key: 'name' },
  { title: '显示名称', key: 'alias' },
  { title: '默认', key: 'is_default', width: 80, render: r => r.is_default ? h(NTag, { type: 'success', size: 'small' }, { default: () => '默认' }) : '' },
  { title: 'Profile 目录', key: 'profile_dir', ellipsis: { tooltip: true } },
  {
    title: '操作', key: 'actions', width: 160,
    render: r => h(NSpace, {}, {
      default: () => [
        h(NButton, { size: 'small', disabled: r.is_default, onClick: () => setDefault(r.name) }, { default: () => '设为默认' }),
        h(NButton, { size: 'small', type: 'error', onClick: () => confirmDelete(r.name) }, { default: () => '删除' }),
      ]
    }),
  },
]

async function loadAccounts() {
  loading.value = true
  try {
    const res = await http.get('/accounts')
    accounts.value = res.data || []
  } catch (e) {
    msg.error('加载账号失败：' + e.message)
  } finally {
    loading.value = false
  }
}

async function addAccount() {
  if (!addForm.value.name.trim()) { msg.warning('账号名不能为空'); return }
  adding.value = true
  try {
    await http.post('/accounts', addForm.value)
    msg.success(`账号「${addForm.value.name}」已添加`)
    showAdd.value = false
    addForm.value = { name: '', alias: '' }
    await loadAccounts()
  } catch (e) {
    msg.error('添加失败：' + e.message)
  } finally {
    adding.value = false
  }
}

function confirmDelete(name) {
  deletingName.value = name
  showDeleteConfirm.value = true
}

async function doDelete() {
  try {
    await http.delete(`/accounts/${deletingName.value}`)
    msg.success(`账号「${deletingName.value}」已删除`)
    await loadAccounts()
  } catch (e) {
    msg.error('删除失败：' + e.message)
  }
}

async function setDefault(name) {
  try {
    await http.put(`/accounts/${name}/default`)
    msg.success(`「${name}」已设为默认账号`)
    await loadAccounts()
  } catch (e) {
    msg.error('设置失败：' + e.message)
  }
}

async function startBrowser() {
  browserLoading.value = true
  try {
    const res = await http.post('/browser/start', { headless: headless.value, port: 9222, account: browserAccount.value || null })
    msg.success(res.message || '浏览器已启动')
  } catch (e) {
    msg.error('启动失败：' + e.message)
  } finally {
    browserLoading.value = false
  }
}

async function stopBrowser() {
  browserLoading.value = true
  try {
    const res = await http.post('/browser/stop', { port: 9222 })
    msg.info(res.message || '浏览器已停止')
  } catch (e) {
    msg.error('停止失败：' + e.message)
  } finally {
    browserLoading.value = false
  }
}

async function openLogin() {
  browserLoading.value = true
  try {
    const res = await http.post('/login')
    msg.info(res.message || '已打开登录页')
  } catch (e) {
    msg.error('打开失败：' + e.message)
  } finally {
    browserLoading.value = false
  }
}

onMounted(loadAccounts)
</script>
