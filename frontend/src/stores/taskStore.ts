import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { taskApi } from '@/api'
import type { DashboardPayload, SubmitTaskRequest, TaskRecord, TaskStatus } from '@/api/types'

export const useTaskStore = defineStore('task', () => {
  type RequestScope = 'dashboard' | 'list' | 'detail' | 'submit'

  const tasks = ref<TaskRecord[]>([])
  const currentTaskSummary = ref<TaskRecord | null>(null)
  const currentTaskResult = ref<string | null>(null)
  const dashboard = ref<DashboardPayload | null>(null)

  const page = ref(1)
  const pageSize = ref(20)
  const total = ref(0)
  const statusFilter = ref<TaskStatus | ''>('')

  const requestState = ref<Record<RequestScope, { loading: boolean; error: string }>>({
    dashboard: { loading: false, error: '' },
    list: { loading: false, error: '' },
    detail: { loading: false, error: '' },
    submit: { loading: false, error: '' },
  })
  const dashboardLoading = computed(() => requestState.value.dashboard.loading)
  const listLoading = computed(() => requestState.value.list.loading)
  const detailLoading = computed(() => requestState.value.detail.loading)
  const submitting = computed(() => requestState.value.submit.loading)
  const dashboardError = computed(() => requestState.value.dashboard.error)
  const listError = computed(() => requestState.value.list.error)
  const detailError = computed(() => requestState.value.detail.error)
  const submitError = computed(() => requestState.value.submit.error)
  const currentTask = computed<TaskRecord | null>(() => {
    if (!currentTaskSummary.value) {
      return null
    }
    return {
      ...currentTaskSummary.value,
      result: currentTaskResult.value,
    }
  })

  const maxPage = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

  function toTaskSummary(record: TaskRecord): TaskRecord {
    return {
      ...record,
      result: null,
    }
  }

  function beginRequest(scope: RequestScope) {
    requestState.value[scope].loading = true
    requestState.value[scope].error = ''
  }

  function failRequest(scope: RequestScope, message: string) {
    requestState.value[scope].error = message
  }

  function finishRequest(scope: RequestScope) {
    requestState.value[scope].loading = false
  }

  async function loadDashboard(recentLimit: number = 8) {
    beginRequest('dashboard')
    try {
      dashboard.value = await taskApi.getDashboard(recentLimit)
      return dashboard.value
    } catch (err: any) {
      failRequest('dashboard', err?.message || '加载仪表盘失败')
      throw err
    } finally {
      finishRequest('dashboard')
    }
  }

  async function loadTasks(nextPage: number = page.value) {
    beginRequest('list')

    try {
      const response = await taskApi.listTasks(
        nextPage,
        pageSize.value,
        statusFilter.value || undefined
      )
      tasks.value = response.items.map((item) => toTaskSummary(item))
      total.value = response.total
      page.value = response.page
      return response
    } catch (err: any) {
      failRequest('list', err?.message || '加载任务列表失败')
      throw err
    } finally {
      finishRequest('list')
    }
  }

  async function setFilters(nextStatus: TaskStatus | '', nextPageSize: number) {
    statusFilter.value = nextStatus
    pageSize.value = nextPageSize
    page.value = 1
    await loadTasks(1)
  }

  async function loadTask(
    taskId: string,
    options: { includeResult?: boolean; maxResultChars?: number } = {}
  ) {
    beginRequest('detail')

    try {
      const detail = await taskApi.getTaskDetail(taskId, {
        includeResult: options.includeResult,
        maxResultChars: options.maxResultChars,
      })
      const summary = toTaskSummary(detail)
      const previousTaskId = currentTaskSummary.value?.task_id
      currentTaskSummary.value = summary
      if (options.includeResult) {
        currentTaskResult.value =
          detail.result === null || detail.result === undefined ? null : detail.result
      } else if (previousTaskId !== detail.task_id || detail.status !== 'completed') {
        currentTaskResult.value = null
      }
      const index = tasks.value.findIndex((item) => item.task_id === taskId)
      if (index >= 0) {
        tasks.value[index] = summary
      }
      return {
        ...summary,
        result: currentTaskResult.value,
      }
    } catch (err: any) {
      failRequest('detail', err?.message || '加载任务详情失败')
      throw err
    } finally {
      finishRequest('detail')
    }
  }

  async function submit(request: SubmitTaskRequest) {
    beginRequest('submit')

    try {
      const result = await taskApi.submitTask(request)
      tasks.value.unshift(toTaskSummary(result))
      total.value += 1
      return result
    } catch (err: any) {
      failRequest('submit', err?.message || '提交任务失败')
      throw err
    } finally {
      finishRequest('submit')
    }
  }

  async function cancel(taskId: string) {
    const response = await taskApi.cancelTask(taskId)
    if (!response.canceled) {
      throw new Error('任务当前不可取消')
    }
    await Promise.all([loadTasks(page.value), loadDashboard(8)])
  }

  async function retry(taskId: string) {
    const response = await taskApi.retryTask(taskId)
    if (!response.retried) {
      throw new Error('任务当前不可重试')
    }
    await Promise.all([loadTasks(page.value), loadDashboard(8)])
  }

  function resetState() {
    tasks.value = []
    currentTaskSummary.value = null
    currentTaskResult.value = null
    dashboard.value = null
    page.value = 1
    pageSize.value = 20
    total.value = 0
    statusFilter.value = ''
    clearError()
  }

  function resetCurrentTask() {
    currentTaskSummary.value = null
    currentTaskResult.value = null
    clearError('detail')
  }

  function clearError(scope: 'dashboard' | 'list' | 'detail' | 'submit' | 'all' = 'all') {
    if (scope === 'all') {
      for (const key of Object.keys(requestState.value) as RequestScope[]) {
        requestState.value[key].error = ''
      }
      return
    }
    requestState.value[scope].error = ''
  }

  return {
    tasks,
    currentTask,
    dashboard,
    requestState,
    page,
    pageSize,
    total,
    maxPage,
    statusFilter,
    dashboardLoading,
    listLoading,
    detailLoading,
    submitting,
    dashboardError,
    listError,
    detailError,
    submitError,
    loadDashboard,
    loadTasks,
    setFilters,
    loadTask,
    submit,
    cancel,
    retry,
    resetState,
    resetCurrentTask,
    clearError,
  }
})
