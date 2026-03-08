import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { taskApi } from '@/api'
import type { DashboardPayload, SubmitTaskRequest, TaskRecord, TaskStatus } from '@/api/types'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<TaskRecord[]>([])
  const currentTask = ref<TaskRecord | null>(null)
  const dashboard = ref<DashboardPayload | null>(null)

  const page = ref(1)
  const pageSize = ref(20)
  const total = ref(0)
  const statusFilter = ref<TaskStatus | ''>('')

  const loading = ref(false)
  const submitting = ref(false)
  const dashboardError = ref('')
  const listError = ref('')
  const detailError = ref('')
  const submitError = ref('')
  const error = computed(() =>
    detailError.value || listError.value || dashboardError.value || submitError.value
  )

  const maxPage = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

  async function loadDashboard(recentLimit: number = 8) {
    dashboardError.value = ''
    try {
      dashboard.value = await taskApi.getDashboard(recentLimit)
      return dashboard.value
    } catch (err: any) {
      dashboardError.value = err?.message || '加载仪表盘失败'
      throw err
    }
  }

  async function loadTasks(nextPage: number = page.value) {
    loading.value = true
    listError.value = ''

    try {
      const response = await taskApi.listTasks(
        nextPage,
        pageSize.value,
        statusFilter.value || undefined
      )
      tasks.value = response.items
      total.value = response.total
      page.value = response.page
      return response
    } catch (err: any) {
      listError.value = err?.message || '加载任务列表失败'
      throw err
    } finally {
      loading.value = false
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
    loading.value = true
    detailError.value = ''

    try {
      currentTask.value = await taskApi.getTaskDetail(taskId, {
        includeResult: options.includeResult,
        maxResultChars: options.maxResultChars,
      })
      const index = tasks.value.findIndex((item) => item.task_id === taskId)
      if (index >= 0) {
        tasks.value[index] = currentTask.value
      }
      return currentTask.value
    } catch (err: any) {
      detailError.value = err?.message || '加载任务详情失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function submit(request: SubmitTaskRequest) {
    submitting.value = true
    submitError.value = ''

    try {
      const result = await taskApi.submitTask(request)
      tasks.value.unshift(result)
      total.value += 1
      return result
    } catch (err: any) {
      submitError.value = err?.message || '提交任务失败'
      throw err
    } finally {
      submitting.value = false
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

  function clearError(scope: 'dashboard' | 'list' | 'detail' | 'submit' | 'all' = 'all') {
    if (scope === 'dashboard' || scope === 'all') dashboardError.value = ''
    if (scope === 'list' || scope === 'all') listError.value = ''
    if (scope === 'detail' || scope === 'all') detailError.value = ''
    if (scope === 'submit' || scope === 'all') submitError.value = ''
  }

  return {
    tasks,
    currentTask,
    dashboard,
    page,
    pageSize,
    total,
    maxPage,
    statusFilter,
    loading,
    submitting,
    dashboardError,
    listError,
    detailError,
    submitError,
    error,
    loadDashboard,
    loadTasks,
    setFilters,
    loadTask,
    submit,
    cancel,
    retry,
    clearError,
  }
})
