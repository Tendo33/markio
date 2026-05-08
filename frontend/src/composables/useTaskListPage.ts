import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'

import type { TaskStatus } from '@/api/types'
import { useAuthStore, useTaskStore } from '@/stores'
import { toast } from '@/utils/toast'

const VALID_PAGE_SIZES = [10, 20, 50]
const VALID_STATUSES: TaskStatus[] = ['pending', 'processing', 'completed', 'failed', 'canceled']

export function useTaskListPage() {
  const route = useRoute()
  const router = useRouter()
  const authStore = useAuthStore()
  const taskStore = useTaskStore()
  const { configured: tokenConfigured } = storeToRefs(authStore)

  const status = ref<TaskStatus | ''>(taskStore.statusFilter)
  const pageSize = ref(taskStore.pageSize)
  const hasActiveTasks = computed(() =>
    taskStore.tasks.some((task) => task.status === 'pending' || task.status === 'processing')
  )
  const confirmState = ref({
    visible: false,
    title: '',
    message: '',
    type: 'warning' as 'danger' | 'warning' | 'info',
    action: null as null | (() => Promise<void>),
  })
  let pollTimerId: number | null = null
  let pollDelayMs = 5000

  function stopPolling() {
    if (pollTimerId) {
      clearTimeout(pollTimerId)
      pollTimerId = null
    }
  }

  function normalizePage(value: unknown): number {
    const raw = Array.isArray(value) ? value[0] : value
    const parsed = Number.parseInt(String(raw ?? ''), 10)
    return Number.isFinite(parsed) && parsed > 0 ? parsed : 1
  }

  function normalizePageSize(value: unknown): number {
    const raw = Array.isArray(value) ? value[0] : value
    const parsed = Number.parseInt(String(raw ?? ''), 10)
    return VALID_PAGE_SIZES.includes(parsed) ? parsed : 20
  }

  function normalizeStatus(value: unknown): TaskStatus | '' {
    const raw = Array.isArray(value) ? value[0] : value
    return VALID_STATUSES.includes(raw as TaskStatus) ? (raw as TaskStatus) : ''
  }

  async function syncStateFromRoute() {
    status.value = normalizeStatus(route.query.status)
    pageSize.value = normalizePageSize(route.query.page_size)
    taskStore.statusFilter = status.value
    taskStore.pageSize = pageSize.value
    taskStore.page = normalizePage(route.query.page)

    if (!tokenConfigured.value) {
      taskStore.tasks = []
      taskStore.total = 0
      taskStore.clearError('list')
      stopPolling()
      return
    }

    await refresh({ silent: true, page: taskStore.page })
    schedulePoll()
  }

  async function updateRouteQuery(next: {
    page?: number
    pageSize?: number
    status?: TaskStatus | ''
  }) {
    const nextStatus = next.status ?? status.value
    await router.push({
      query: {
        ...route.query,
        page: String(next.page ?? taskStore.page),
        page_size: String(next.pageSize ?? pageSize.value),
        status: nextStatus || undefined,
      },
    })
  }

  function shouldPollTaskList() {
    return tokenConfigured.value && document.visibilityState === 'visible' && hasActiveTasks.value
  }

  function nextPollDelay(hadError: boolean) {
    if (!shouldPollTaskList()) {
      pollDelayMs = 5000
      return pollDelayMs
    }
    const baseline = 5000
    if (hadError) {
      pollDelayMs = Math.min(Math.max(baseline, pollDelayMs * 2), 30000)
    } else {
      pollDelayMs = baseline
    }
    return pollDelayMs
  }

  function schedulePoll(hadError = false) {
    stopPolling()
    if (!shouldPollTaskList()) {
      return
    }
    pollTimerId = window.setTimeout(async () => {
      const ok = await refresh({ silent: true })
      schedulePoll(!ok)
    }, nextPollDelay(hadError))
  }

  async function applyFilters() {
    await runWithErrorToast(
      () =>
        updateRouteQuery({
          page: 1,
          pageSize: pageSize.value,
          status: status.value,
        }),
      '应用过滤失败'
    )
  }

  async function refresh(options: { silent?: boolean; page?: number } = {}) {
    const silent = options.silent ?? false
    if (!tokenConfigured.value) {
      return true
    }
    try {
      await taskStore.loadTasks(options.page ?? taskStore.page)
      return true
    } catch (error: any) {
      if (!silent) {
        toast.error(error?.message || '刷新任务列表失败')
      }
      return false
    }
  }

  async function prevPage() {
    if (taskStore.page <= 1) return
    await runWithErrorToast(() => updateRouteQuery({ page: taskStore.page - 1 }), '翻页失败')
  }

  async function nextPage() {
    if (taskStore.page >= taskStore.maxPage) return
    await runWithErrorToast(() => updateRouteQuery({ page: taskStore.page + 1 }), '翻页失败')
  }

  function cancelTask(taskId: string) {
    confirmState.value = {
      visible: true,
      title: '取消任务',
      message: `确认取消任务 ${taskId} 吗？`,
      type: 'warning',
      action: async () => {
        await taskStore.cancel(taskId)
        toast.success('任务已取消')
        schedulePoll()
      },
    }
  }

  function retryTask(taskId: string) {
    confirmState.value = {
      visible: true,
      title: '重试任务',
      message: `确认重试任务 ${taskId} 吗？`,
      type: 'info',
      action: async () => {
        await taskStore.retry(taskId)
        toast.success('任务已重新提交')
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

  async function runWithErrorToast(action: () => Promise<unknown>, fallbackMessage: string) {
    try {
      await action()
    } catch (error: any) {
      toast.error(error?.message || fallbackMessage)
    }
  }

  function handleVisibilityChange() {
    if (document.visibilityState === 'visible') {
      refresh({ silent: true }).catch(() => {
        // ignore visibility refresh error
      })
      schedulePoll()
      return
    }
    stopPolling()
  }

  onMounted(async () => {
    document.addEventListener('visibilitychange', handleVisibilityChange)
    await syncStateFromRoute()
  })

  watch(tokenConfigured, () => {
    syncStateFromRoute().catch(() => {
      // errors are already stored in the Pinia store
    })
  })

  watch(
    () => route.query,
    () => {
      syncStateFromRoute().catch(() => {
        // errors are already stored in the Pinia store
      })
    }
  )

  watch(hasActiveTasks, () => {
    schedulePoll()
  })

  onUnmounted(() => {
    document.removeEventListener('visibilitychange', handleVisibilityChange)
    stopPolling()
  })

  return {
    confirmState,
    pageSize,
    status,
    taskStore,
    tokenConfigured,
    applyFilters,
    cancelTask,
    executeConfirmedAction,
    nextPage,
    prevPage,
    refresh,
    retryTask,
  }
}
