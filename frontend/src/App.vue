<template>
  <n-config-provider :theme="null">
    <n-message-provider>
      <AppInner />
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { NConfigProvider, NMessageProvider } from 'naive-ui'
import AppInner from './AppInner.vue'
</script>
