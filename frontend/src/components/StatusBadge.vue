<template>
  <span :class="badgeClass" class="inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium">
    <span :class="dotClass" class="w-1.5 h-1.5 rounded-full mr-1.5"></span>
    {{ statusText }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { TaskStatus } from '@/api/types'

const props = defineProps<{
  status: TaskStatus
}>()

const statusText = computed(() => {
  const mapping: Record<TaskStatus, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
    canceled: '已取消',
  }
  return mapping[props.status]
})

const badgeClass = computed(() => {
  const classMap: Record<TaskStatus, string> = {
    pending: 'bg-muted text-tertiary border-subtle',
    processing: 'bg-warning text-warning border-warning',
    completed: 'bg-success text-success border-[color:var(--status-success-border)]',
    failed: 'bg-danger text-danger border-danger',
    canceled: 'bg-muted text-secondary border-subtle',
  }
  return classMap[props.status]
})

const dotClass = computed(() => {
  const classMap: Record<TaskStatus, string> = {
    pending: 'bg-[color:var(--border-strong)]',
    processing: 'bg-[color:var(--status-warning-text)] animate-pulse',
    completed: 'bg-[color:var(--status-success-text)]',
    failed: 'bg-[color:var(--status-danger-text)]',
    canceled: 'bg-[color:var(--text-tertiary)]',
  }
  return classMap[props.status]
})
</script>
