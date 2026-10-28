import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'

import { downloadTaskResult } from '@/api/taskApi'

import { useAuthStore, useTaskStore } from '@/stores'
import { toast } from '@/utils/toast'

export function useTaskDetailPolling() {
  const route = useRoute()
  const router = useRouter()
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

  function remove() {
    confirmState.value = {
      visible: true,
      title: '删除任务',
      message: `确认删除任务 ${taskId.value} 吗？删除后无法恢复。`,
      type: 'danger',
      action: async () => {
        stopPolling()
        await taskStore.remove(taskId.value)
        toast.success('任务已删除')
        await router.replace({ name: 'task-list' })
      },
    }
  }

  function goBack() {
    // A direct link has no in-app history entry; fall back to the task list
    if (window.history.state?.back) {
      router.back()
    } else {
      router.push({ name: 'task-list' })
    }
  }

  async function copyResult() {
    const text = task.value?.result
    if (!text) return
    try {
      await navigator.clipboard.writeText(text)
      toast.success('已复制 Markdown')
    } catch {
      toast.error('复制失败，请手动选择文本复制')
    }
  }

  async function downloadResult() {
    try {
      const { blob, filename } = await downloadTaskResult(taskId.value)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (error: any) {
      toast.error(error?.message || '下载失败')
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
    copyResult,
    downloadResult,
    executeConfirmedAction,
    goBack,
    remove,
    refresh,
    retry,
  }
}
