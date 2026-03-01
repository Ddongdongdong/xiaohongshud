<template>
  <n-layout style="height: 100vh">
    <n-layout-header bordered style="padding: 0 16px; display: flex; align-items: center; height: 56px">
      <span style="font-size: 18px; font-weight: 600; color: #ff2442">
        🌸 小红书技能管理平台
      </span>
      <n-space style="margin-left: auto" align="center">
        <n-tag :type="loginStatus === true ? 'success' : loginStatus === false ? 'error' : 'default'" size="small">
          {{ loginStatus === true ? '已登录' : loginStatus === false ? '未登录' : '检测中...' }}
        </n-tag>
        <n-button size="small" @click="checkLogin" :loading="checking">检查登录</n-button>
      </n-space>
    </n-layout-header>

    <n-layout has-sider style="height: calc(100vh - 56px)">
      <n-layout-sider
        bordered
        collapse-mode="width"
        :collapsed-width="64"
        :width="200"
        :collapsed="collapsed"
        show-trigger
        @collapse="collapsed = true"
        @expand="collapsed = false"
      >
        <n-menu
          :collapsed="collapsed"
          :options="menuOptions"
          :value="currentRoute"
          @update:value="navigate"
        />
      </n-layout-sider>

      <n-layout-content content-style="padding: 20px; overflow-y: auto">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup>
import { ref, computed, provide, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NLayout, NLayoutHeader, NLayoutSider, NLayoutContent,
  NMenu, NSpace, NTag, NButton, useMessage
} from 'naive-ui'
import http from './api/http.js'

const router = useRouter()
const route = useRoute()
const message = useMessage()

// 向全局提供 message，所有子组件通过 useMsg() 获取
provide('message', message)

const collapsed = ref(false)
const loginStatus = ref(null)
const checking = ref(false)

const currentRoute = computed(() => route.path)

const menuOptions = [
  { label: '数据看板', key: '/dashboard', icon: () => h('span', { style: 'font-size:16px' }, '📊') },
  { label: '内容发布', key: '/publish',   icon: () => h('span', { style: 'font-size:16px' }, '✏️') },
  { label: '笔记搜索', key: '/search',    icon: () => h('span', { style: 'font-size:16px' }, '🔍') },
  { label: 'A/B 测试', key: '/ab-test',  icon: () => h('span', { style: 'font-size:16px' }, '⚗️') },
  { label: '账号管理', key: '/accounts',  icon: () => h('span', { style: 'font-size:16px' }, '👤') },
  { label: '文案助手', key: '/llm',       icon: () => h('span', { style: 'font-size:16px' }, '🤖') },
]

function navigate(key) {
  router.push(key)
}

async function checkLogin() {
  checking.value = true
  try {
    const res = await http.get('/login/status')
    loginStatus.value = res.data?.logged_in ?? false
    message.info(loginStatus.value ? '已登录' : '未登录，请先扫码')
  } catch (e) {
    loginStatus.value = false
    message.error('检测失败：' + e.message)
  } finally {
    checking.value = false
  }
}

checkLogin()
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
