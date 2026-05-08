import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute } from 'vue-router'

import { useAuthStore, useTaskStore } from '@/stores'
import { toast } from '@/utils/toast'

export function useTaskDetailPolling() {
  const route = useRoute()
  const authStore = useAuthStore()
  const taskStore = useTaskStore()
  const { configured: tokenConfigured } = storeToRefs(authStore)

  let timerId: number | null = null
  let refreshing = false
  let pollDelayMs = 3000

  const taskId = computed(() => String(route.params.id))
  const task = computed(() => taskStore.currentTask)
  const finalResultLoaded = ref(false)
  const confirmState = ref({
    visible: false,
    title: '',
    message: '',
    type: 'warning' as 'danger' | 'warning' | 'info',
    action: null as null | (() => Promise<void>),
  })

  function stopPolling() {
    if (timerId) {
      clearTimeout(timerId)
      timerId = null
    }
  }

  function shouldPollCurrentTask() {
    if (!tokenConfigured.value || document.visibilityState !== 'visible') {
      return false
    }
    if (!task.value) {
      return false
    }
    return task.value.status === 'pending' || task.value.status === 'processing'
  }

  async function refresh(options: { silent?: boolean } = {}) {
    if (!tokenConfigured.value) {
      taskStore.resetCurrentTask()
      finalResultLoaded.value = false
      return true
    }
    if (refreshing) {
      return true
    }
    refreshing = true
    try {
      const includeResult = task.value?.status === 'completed'
      const latest = await taskStore.loadTask(taskId.value, { includeResult })
      if (latest.status === 'completed') {
        if (!includeResult && !finalResultLoaded.value) {
          finalResultLoaded.value = true
          await taskStore.loadTask(taskId.value, { includeResult: true })
        } else if (includeResult) {
          finalResultLoaded.value = true
        }
      } else {
        finalResultLoaded.value = false
      }
      return true
    } catch (error: any) {
      if (!options.silent) {
        toast.error(error?.message || '加载任务详情失败')
      }
      return false
    } finally {
      refreshing = false
    }
  }

  async function loadCurrentTask() {
    taskStore.resetCurrentTask()
    finalResultLoaded.value = false
    stopPolling()
    await refresh({ silent: true })
    schedulePoll()
  }

  function cancel() {
    confirmState.value = {
      visible: true,
      title: '取消任务',
      message: `确认取消任务 ${taskId.value} 吗？`,
      type: 'warning',
      action: async () => {
        await taskStore.cancel(taskId.value)
        toast.success('任务已取消')
        await refresh()
        schedulePoll()
      },
    }
  }

  function retry() {
    confirmState.value = {
      visible: true,
      title: '重试任务',
      message: `确认重试任务 ${taskId.value} 吗？`,
      type: 'info',
      action: async () => {
        await taskStore.retry(taskId.value)
        toast.success('任务已重新提交')
        await refresh()
        schedulePoll()
      },
    }
  }

  async function executeConfirmedAction() {
    const action = confirmState.value.action
    if (!action) return
    try {
      await action()
    } catch (error: any) {
      toast.error(error?.message || '操作失败')
    } finally {
      confirmState.value.action = null
    }
  }

  function nextPollDelay(hadError: boolean) {
    if (!shouldPollCurrentTask()) {
      pollDelayMs = 15000
      return pollDelayMs
    }
    const baseline = task.value?.status === 'processing' ? 3000 : 5000
    if (hadError) {
      pollDelayMs = Math.min(Math.max(baseline, pollDelayMs * 2), 30000)
    } else {
      pollDelayMs = baseline
    }
    return pollDelayMs
  }

  function schedulePoll(hadError = false) {
    stopPolling()
    if (!shouldPollCurrentTask()) {
      return
    }
    timerId = window.setTimeout(async () => {
      const ok = await refresh({ silent: true })
      schedulePoll(!ok)
    }, nextPollDelay(hadError))
  }

  function handleVisibilityChange() {
    if (document.visibilityState === 'visible') {
      refresh({ silent: true }).catch(() => {
        // ignore visibility-triggered refresh errors
      })
      schedulePoll()
      return
    }
    stopPolling()
  }

  onMounted(() => {
    document.addEventListener('visibilitychange', handleVisibilityChange)
  })

  watch(
    [taskId, tokenConfigured],
    () => {
      loadCurrentTask().catch(() => {
        // errors are already stored in the Pinia store
      })
    },
    { immediate: true }
  )

  onUnmounted(() => {
    document.removeEventListener('visibilitychange', handleVisibilityChange)
    stopPolling()
  })

  return {
    confirmState,
    task,
    taskId,
    taskStore,
    tokenConfigured,
    cancel,
    executeConfirmedAction,
    refresh,
    retry,
  }
}
