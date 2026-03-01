import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/dashboard' },
  {
    path: '/dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { title: '数据看板' },
  },
  {
    path: '/publish',
    component: () => import('../views/Publish.vue'),
    meta: { title: '内容发布' },
  },
  {
    path: '/search',
    component: () => import('../views/Search.vue'),
    meta: { title: '笔记搜索' },
  },
  {
    path: '/ab-test',
    component: () => import('../views/ABTest.vue'),
    meta: { title: 'A/B 测试' },
  },
  {
    path: '/accounts',
    component: () => import('../views/Accounts.vue'),
    meta: { title: '账号管理' },
  },
  {
    path: '/llm',
    component: () => import('../views/LLMHelper.vue'),
    meta: { title: '文案助手' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
