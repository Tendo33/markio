<template>
  <div class="relative overflow-hidden bg-surface rounded-2xl border border-subtle shadow-[0_1px_2px_rgba(16,24,40,0.06)] p-4 lg:p-5">
    <div class="absolute inset-x-0 top-0 h-0.5" :class="accentBarClass"></div>
    <div class="relative flex items-center justify-between">
      <div class="flex-1 min-w-0">
        <p class="text-xs lg:text-sm font-medium text-secondary uppercase tracking-[0.18em] truncate">{{ title }}</p>
        <p class="mt-2 lg:mt-3 text-2xl lg:text-3xl font-semibold tracking-tight tabular-nums" :class="valueClass">{{ value }}</p>
        <p v-if="subtitle" class="mt-1 lg:mt-2 text-xs lg:text-sm text-secondary truncate">{{ subtitle }}</p>
      </div>
      <div
        v-if="icon"
        :class="iconBgClass"
        class="p-2.5 lg:p-3 rounded-xl border border-subtle flex-shrink-0 ml-2"
      >
        <component :is="icon" :class="iconClass" class="w-5 h-5 lg:w-6 lg:h-6" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, type Component } from 'vue'

const props = withDefaults(defineProps<{
  title: string
  value: string | number
  subtitle?: string
  icon?: Component
  color?: 'gray' | 'yellow' | 'green' | 'red' | 'blue'
}>(), {
  color: 'blue'
})

const valueClass = computed(() => {
  const classMap = {
    gray: 'text-primary',
    yellow: 'text-warning',
    green: 'text-success',
    red: 'text-danger',
    blue: 'text-info',
  }
  return classMap[props.color]
})

const iconBgClass = computed(() => {
  const classMap = {
    gray: 'bg-subtle',
    yellow: 'bg-warning',
    green: 'bg-success',
    red: 'bg-danger',
    blue: 'bg-info',
  }
  return classMap[props.color]
})

const iconClass = computed(() => {
  const classMap = {
    gray: 'text-secondary',
    yellow: 'text-warning',
    green: 'text-success',
    red: 'text-danger',
    blue: 'text-info',
  }
  return classMap[props.color]
})

const accentBarClass = computed(() => {
  const classMap = {
    gray: 'bg-[color:var(--border-strong)]',
    yellow: 'bg-[color:var(--status-warning-text)]',
    green: 'bg-[color:var(--status-success-text)]',
    red: 'bg-[color:var(--status-danger-text)]',
    blue: 'bg-[color:var(--status-info-text)]',
  }
  return classMap[props.color]
})
</script>
