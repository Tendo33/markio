<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="modelValue" class="fixed inset-0 z-50 overflow-y-auto">
        <!-- 遮罩层 -->
        <div class="fixed inset-0 bg-black bg-opacity-50 transition-opacity" @click="onCancel"></div>

        <!-- 对话框 -->
        <div class="flex min-h-screen items-center justify-center p-4">
          <div
            ref="dialogRef"
            class="relative bg-surface rounded-lg shadow-xl max-w-md w-full p-6 transform transition-all"
            role="dialog"
            aria-modal="true"
            :aria-labelledby="titleId"
            :aria-describedby="messageId"
            tabindex="-1"
          >
            <!-- 标题 -->
            <h3 :id="titleId" class="text-lg font-semibold text-primary mb-4">{{ resolvedTitle }}</h3>

            <!-- 内容 -->
            <p :id="messageId" class="text-sm text-secondary mb-6 break-words" dir="auto">{{ resolvedMessage }}</p>

            <!-- 按钮 -->
            <div class="flex justify-end gap-3">
              <button
                ref="cancelButtonRef"
                @click="onCancel"
                type="button"
                class="px-4 py-2 text-sm font-medium text-tertiary bg-surface border border-default rounded-lg hover:bg-muted"
              >
                {{ cancelText }}
              </button>
              <button
                ref="confirmButtonRef"
                @click="onConfirm"
                type="button"
                :class="confirmButtonClass"
                class="px-4 py-2 text-sm font-medium text-white rounded-lg"
              >
                {{ confirmText }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'

const props = withDefaults(defineProps<{
  modelValue: boolean
  title?: string
  message?: string
  confirmText?: string
  cancelText?: string
  type?: 'danger' | 'warning' | 'info'
}>(), {
  title: '',
  message: '',
  confirmText: '确认',
  cancelText: '取消',
  type: 'danger'
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'confirm': []
  'cancel': []
}>()
const dialogRef = ref<HTMLDivElement | null>(null)
const cancelButtonRef = ref<HTMLButtonElement | null>(null)
const confirmButtonRef = ref<HTMLButtonElement | null>(null)
const titleId = `confirm-dialog-title-${Math.random().toString(36).slice(2)}`
const messageId = `confirm-dialog-message-${Math.random().toString(36).slice(2)}`
let previousFocusedElement: HTMLElement | null = null

  const confirmButtonClass = computed(() => {
    const classMap = {
    danger: 'bg-[color:var(--status-danger-text)] hover:bg-[color:var(--status-danger-text)]',
    warning: 'bg-[color:var(--status-warning-text)] hover:bg-[color:var(--status-warning-text)]',
    info: 'bg-[color:var(--status-info-text)] hover:bg-[color:var(--status-info-text)]',
    }
    return classMap[props.type]
  })

const resolvedTitle = computed(() => props.title || '确认操作')
const resolvedMessage = computed(() => props.message || '你确定要继续吗？')

function onConfirm() {
  emit('confirm')
  emit('update:modelValue', false)
}

function onCancel() {
  emit('cancel')
  emit('update:modelValue', false)
}

function getFocusableElements(): HTMLElement[] {
  if (!dialogRef.value) {
    return []
  }
  return Array.from(
    dialogRef.value.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    ),
  ).filter((element) => !element.hasAttribute('disabled'))
}

function onKeydown(event: KeyboardEvent) {
  if (!props.modelValue) {
    return
  }

  if (event.key === 'Escape') {
    event.preventDefault()
    onCancel()
    return
  }

  if (event.key === 'Tab') {
    const focusable = getFocusableElements()
    if (focusable.length === 0) {
      event.preventDefault()
      return
    }
    const active = document.activeElement as HTMLElement | null
    const currentIndex = focusable.indexOf(active || focusable[0])
    const direction = event.shiftKey ? -1 : 1
    const nextIndex = (currentIndex + direction + focusable.length) % focusable.length
    event.preventDefault()
    focusable[nextIndex].focus()
  }
}

watch(
  () => props.modelValue,
  async (visible) => {
    if (visible) {
      previousFocusedElement = document.activeElement as HTMLElement | null
      document.addEventListener('keydown', onKeydown)
      await nextTick()
      cancelButtonRef.value?.focus()
      return
    }
    document.removeEventListener('keydown', onKeydown)
    previousFocusedElement?.focus?.()
    previousFocusedElement = null
  },
)

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
