<template>
  <div class="relative overflow-hidden bg-white rounded-2xl border border-[#e5e5eb] shadow-[0_1px_2px_rgba(16,24,40,0.06)] p-4 lg:p-5">
    <div class="relative flex items-center justify-between">
      <div class="flex-1 min-w-0">
        <p class="text-xs lg:text-sm font-medium text-[#6e6e80] uppercase tracking-wide truncate">{{ title }}</p>
        <p class="mt-2 lg:mt-3 text-2xl lg:text-3xl font-semibold" :class="valueClass">{{ value }}</p>
        <p v-if="subtitle" class="mt-1 lg:mt-2 text-xs lg:text-sm text-[#6e6e80] truncate">{{ subtitle }}</p>
      </div>
      <div
        v-if="icon"
        :class="iconBgClass"
        class="p-2.5 lg:p-3 rounded-xl border border-[#ececf1] flex-shrink-0 ml-2"
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
    gray: 'text-[#202123]',
    yellow: 'text-[#a16207]',
    green: 'text-[#0f8b6d]',
    red: 'text-[#b42318]',
    blue: 'text-[#2056cf]',
  }
  return classMap[props.color]
})

const iconBgClass = computed(() => {
  const classMap = {
    gray: 'bg-[#f7f7f8]',
    yellow: 'bg-[#fffbeb]',
    green: 'bg-[#ecfdf3]',
    red: 'bg-[#fef3f2]',
    blue: 'bg-[#eff6ff]',
  }
  return classMap[props.color]
})

const iconClass = computed(() => {
  const classMap = {
    gray: 'text-[#6e6e80]',
    yellow: 'text-[#a16207]',
    green: 'text-[#0f8b6d]',
    red: 'text-[#b42318]',
    blue: 'text-[#2056cf]',
  }
  return classMap[props.color]
})
</script>
