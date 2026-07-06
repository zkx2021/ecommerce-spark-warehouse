<template>
  <span class="status-badge" :class="`status-badge--${type}`">
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    default: 'loading'
  }
})

const type = computed(() => {
  if (props.status === 'api') return 'api'
  if (props.status === 'mock') return 'mock'
  if (props.status === 'error') return 'error'
  return 'loading'
})

const label = computed(() => {
  if (props.status === 'api') return 'API 数据'
  if (props.status === 'mock') return 'Mock 数据'
  if (props.status === 'error') return '异常降级'
  return '加载中'
})
</script>
