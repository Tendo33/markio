<template>
  <div class="relative overflow-hidden rounded-xl border border-subtle bg-surface p-4 lg:p-5">
    <div class="flex items-start justify-between gap-4">
      <div class="flex-1 min-w-0">
        <p class="truncate text-[11px] font-medium uppercase tracking-[0.18em] text-secondary lg:text-xs">{{ title }}</p>
        <p class="mt-3 text-2xl font-semibold tracking-tight tabular-nums lg:text-3xl" :class="valueClass">{{ value }}</p>
        <p v-if="subtitle" class="mt-2 text-sm leading-5 text-secondary">{{ subtitle }}</p>
      </div>
      <div
        v-if="icon"
        :class="iconBgClass"
        class="ml-2 flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-full"
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
    gray: 'bg-muted',
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

</script>
