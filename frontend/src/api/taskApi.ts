import apiClient from './client'
import type {
  CancelResponse,
  DashboardPayload,
  RetryResponse,
  SubmitTaskRequest,
  TaskListPage,
  TaskRecord,
  TaskStatus,
} from './types'

const TASK_BASE = '/v1/tasks'

export async function submitTask(request: SubmitTaskRequest): Promise<TaskRecord> {
  const formData = new FormData()
  formData.append('file', request.file)
  formData.append('parse_method', request.parse_method || 'auto')
  formData.append('lang', request.lang || 'ch')
  formData.append('priority', String(request.priority ?? 0))
  formData.append('save_parsed_content', String(request.save_parsed_content ?? false))
  formData.append('save_middle_content', String(request.save_middle_content ?? false))
  formData.append('output_dir', request.output_dir || 'outputs')
  formData.append('start_page', String(request.start_page ?? 0))

  if (request.end_page !== undefined && request.end_page !== null) {
    formData.append('end_page', String(request.end_page))
  }

  const response = await apiClient.post<TaskRecord>(`${TASK_BASE}/submit`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export async function listTasks(
  page: number,
  pageSize: number,
  status?: TaskStatus
): Promise<TaskListPage> {
  const response = await apiClient.get<TaskListPage>(TASK_BASE, {
    params: {
      page,
      page_size: pageSize,
      status: status || undefined,
    },
  })
  return response.data
}

export async function getTaskDetail(taskId: string): Promise<TaskRecord> {
  const response = await apiClient.get<TaskRecord>(`${TASK_BASE}/${taskId}`)
  return response.data
}

export async function getDashboard(recentLimit: number = 8): Promise<DashboardPayload> {
  const response = await apiClient.get<DashboardPayload>(`${TASK_BASE}/dashboard`, {
    params: { recent_limit: recentLimit },
  })
  return response.data
}

export async function cancelTask(taskId: string): Promise<CancelResponse> {
  const response = await apiClient.post<CancelResponse>(`${TASK_BASE}/${taskId}/cancel`)
  return response.data
}

export async function retryTask(taskId: string): Promise<RetryResponse> {
  const response = await apiClient.post<RetryResponse>(`${TASK_BASE}/${taskId}/retry`)
  return response.data
}
