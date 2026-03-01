import { inject } from 'vue'

/**
 * 获取全局 Naive UI message 实例。
 * App.vue 通过 provide('message', useMessage()) 提供。
 */
export function useMsg() {
  return inject('message')
}
