<template>
  <div
    :class="containerClass"
    class="flex items-center justify-center"
    role="status"
    aria-live="polite"
    aria-busy="true"
  >
    <div :class="spinnerClass" class="animate-spin rounded-full border-t-2 border-b-2" aria-hidden="true"></div>
    <p v-if="text" :class="textClass" class="ml-3">{{ text }}</p>
    <span v-else class="sr-only">Loading</span>
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
      return 'fixed inset-0 bg-surface bg-opacity-75 z-50'
    }
    return ''
  })

const spinnerClass = computed(() => {
  const sizeMap = {
    sm: 'h-4 w-4 border-primary-500',
    md: 'h-8 w-8 border-primary-600',
    lg: 'h-12 w-12 border-primary-600',
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
