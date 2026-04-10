<template>
  <div
    :class="containerClass"
    class="flex items-center justify-center"
    role="status"
    aria-live="polite"
    aria-busy="true"
  >
    <div :class="spinnerClass" class="spinner-ring animate-spin rounded-full border-2" aria-hidden="true"></div>
    <p v-if="text" :class="textClass" class="ml-3">{{ text }}</p>
    <span v-else class="sr-only">加载中</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  size?: 'sm' | 'md' | 'lg'
  text?: string
  fullscreen?: boolean
}>(), {
  size: 'md',
  fullscreen: false
})

  const containerClass = computed(() => {
    if (props.fullscreen) {
      return 'fixed inset-0 z-50 bg-[color:rgba(253,253,248,0.82)]'
    }
    return ''
  })

const spinnerClass = computed(() => {
  const sizeMap = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  }
  return sizeMap[props.size]
})

  const textClass = computed(() => {
    const sizeMap = {
      sm: 'text-sm text-secondary',
      md: 'text-base text-tertiary',
      lg: 'text-lg text-primary',
    }
    return sizeMap[props.size]
  })
</script>
