export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'canceled'

export type ParseMethod = 'auto' | 'txt' | 'ocr'
export type TaskLanguage = 'ch' | 'en' | 'japan' | 'korean'

export interface SubmitTaskRequest {
  file: File
  parse_method?: ParseMethod
  lang?: TaskLanguage
  priority?: number
  save_parsed_content?: boolean
  save_middle_content?: boolean
  output_dir?: string
  start_page?: number
  end_page?: number | null
}

export interface TaskRecord {
  task_id: string
  filename: string
  status: TaskStatus
  parse_method: string
  lang: string
  created_at: string
  started_at: string | null
  completed_at: string | null
  result: string | null
  error_message: string | null
  cache_hit: boolean
  priority: number
  retry_count: number
}

export interface TaskListPage {
  items: TaskRecord[]
  total: number
  page: number
  page_size: number
}

export interface TaskStats {
  pending: number
  processing: number
  completed: number
  failed: number
}

export interface QueueHealth {
  queued: number
  processing: number
  workers: number
  paused: boolean
}

export interface DashboardPayload {
  stats: TaskStats
  queue: QueueHealth
  success_rate: number
  recent_tasks: TaskRecord[]
  updated_at: string
}

export interface QueuePauseResumeResponse {
  paused: boolean
}

export interface CancelResponse {
  task_id: string
  canceled: boolean
}

export interface RetryResponse {
  task_id: string
  retried: boolean
}
