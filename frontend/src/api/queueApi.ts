import apiClient from './client'
import type { QueueHealth, QueuePauseResumeResponse } from './types'

const TASK_BASE = '/v1/tasks'

export async function getQueueHealth(): Promise<QueueHealth> {
  const response = await apiClient.get<QueueHealth>(`${TASK_BASE}/queue`)
  return response.data
}

export async function pauseQueue(): Promise<QueuePauseResumeResponse> {
  const response = await apiClient.post<QueuePauseResumeResponse>(`${TASK_BASE}/queue/pause`)
  return response.data
}

export async function resumeQueue(): Promise<QueuePauseResumeResponse> {
  const response = await apiClient.post<QueuePauseResumeResponse>(`${TASK_BASE}/queue/resume`)
  return response.data
}
