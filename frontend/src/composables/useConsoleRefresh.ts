import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute } from 'vue-router'

import { useAuthStore, useQueueStore, useTaskStore } from '@/stores'
import { toast } from '@/utils/toast'

export function useConsoleRefresh() {
  const route = useRoute()
  const authStore = useAuthStore()
  const taskStore = useTaskStore()
  const queueStore = useQueueStore()
  const { configured: tokenConfigured, isAdmin, role, status, token } = storeToRefs(authStore)

  const refreshing = ref(false)
  const autoRefreshing = ref(false)
  const apiToken = ref(token.value)
  let timerId: number | null = null
  let autoRefreshDelayMs = 5000

  const currentRole = computed(() => role.value)
  const tokenBannerMessage = computed(() => {
    if (status.value === 'expired') {
      return '当前 JWT Token 已过期。先在顶部更新 Token，再查看任务、提交文件或管理队列。'
    }
    if (status.value === 'invalid') {
      return '当前 JWT Token 无效。先在顶部更新 Token，再查看任务、提交文件或管理队列。'
    }
    return '还没有可用的 JWT Token。先在顶部保存 Token，再查看任务、提交文件或管理队列。'
  })

  const stats = computed(() => {
    return (
      taskStore.dashboard?.stats ?? {
        pending: 0,
        processing: 0,
        completed: 0,
        failed: 0,
        canceled: 0,
      }
    )
  })

  function shouldAutoRefresh() {
    return tokenConfigured.value && document.visibilityState === 'visible' && route.name !== 'task-detail'
  }

  function syncTokenContext() {
    authStore.refreshFromStorage()
    apiToken.value = token.value
  }

  async function refreshAll(options: { silent?: boolean } = {}) {
    const isSilent = options.silent ?? false
    if ((refreshing.value || autoRefreshing.value) || (isSilent && !shouldAutoRefresh())) {
      return true
    }
    if (!tokenConfigured.value) {
      taskStore.resetState()
      queueStore.reset()
      return true
    }
    if (isSilent) {
      autoRefreshing.value = true
    } else {
      refreshing.value = true
    }
    try {
      const operations: Array<Promise<unknown>> = [taskStore.loadDashboard(8)]
      if (isAdmin.value) {
        operations.push(queueStore.fetchHealth())
      } else {
        queueStore.reset()
      }
      await Promise.all(operations)
      return true
    } catch {
      return false
    } finally {
      if (isSilent) {
        autoRefreshing.value = false
      } else {
        refreshing.value = false
      }
    }
  }

  function nextAutoRefreshDelay(hadError: boolean) {
    if (!shouldAutoRefresh()) {
      autoRefreshDelayMs = 30000
      return autoRefreshDelayMs
    }
    const activeTasks = Number(stats.value.pending) + Number(stats.value.processing)
    const baseline = activeTasks > 0 ? 5000 : 15000
    if (hadError) {
      autoRefreshDelayMs = Math.min(Math.max(baseline, autoRefreshDelayMs * 2), 60000)
    } else {
      autoRefreshDelayMs = baseline
    }
    return autoRefreshDelayMs
  }

  function stopAutoRefresh() {
    if (timerId) {
      clearTimeout(timerId)
      timerId = null
    }
  }

  function scheduleAutoRefresh(hadError = false) {
    stopAutoRefresh()
    if (!shouldAutoRefresh()) {
      return
    }
    const delay = nextAutoRefreshDelay(hadError)
    timerId = window.setTimeout(async () => {
      const ok = await refreshAll({ silent: true })
      scheduleAutoRefresh(!ok)
    }, delay)
  }

  function handleVisibilityChange() {
    if (document.visibilityState === 'visible') {
      refreshAll({ silent: true }).catch(() => {
        // ignore visibility refresh error
      })
      scheduleAutoRefresh()
      return
    }
    stopAutoRefresh()
  }

  function saveToken() {
    authStore.saveToken(apiToken.value)
    syncTokenContext()
    toast.success('Token 已保存')
    refreshAll().catch(() => {
      // ignore refresh error after token save
    })
    scheduleAutoRefresh()
  }

  function clearToken() {
    apiToken.value = ''
    authStore.clearToken()
    syncTokenContext()
    taskStore.resetState()
    queueStore.reset()
    stopAutoRefresh()
    toast.info('Token 已清除')
  }

  onMounted(async () => {
    syncTokenContext()
    try {
      await refreshAll()
    } catch {
      // ignore initial refresh error
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)
    scheduleAutoRefresh()
  })

  watch(token, () => {
    syncTokenContext()
  })

  watch(
    [tokenConfigured, () => route.name, () => stats.value.pending, () => stats.value.processing],
    () => {
      scheduleAutoRefresh()
    }
  )

  onUnmounted(() => {
    document.removeEventListener('visibilitychange', handleVisibilityChange)
    stopAutoRefresh()
  })

  return {
    apiToken,
    autoRefreshing,
    currentRole,
    isAdmin,
    refreshing,
    role,
    stats,
    status,
    token,
    tokenBannerMessage,
    tokenConfigured,
    clearToken,
    refreshAll,
    saveToken,
  }
}
