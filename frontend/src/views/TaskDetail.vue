<template>
  <div :aria-busy="taskStore.detailLoading ? 'true' : 'false'">
    <div class="mb-4">
      <button @click="$router.back()" class="text-sm text-secondary hover:text-primary flex items-center">
        <ArrowLeft class="w-4 h-4 mr-1" />
        返回
      </button>
    </div>

    <div class="mb-6">
      <h1 class="page-title">任务详情</h1>
      <p class="mt-1 page-subtitle">跟踪任务执行状态与解析输出</p>
    </div>

    <div
      v-if="taskStore.detailLoading && !task"
      class="text-center py-12"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <LoadingSpinner size="lg" text="加载中" />
    </div>

    <div v-else-if="taskStore.detailError" class="card bg-danger border-danger text-danger break-words" dir="auto">
      {{ taskStore.detailError }}
    </div>

    <div v-else-if="task" class="space-y-6">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="section-title">基本信息</h2>
          <StatusBadge :status="task.status" />
        </div>

        <dl class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <dt class="text-secondary">任务ID</dt>
            <dd class="mt-1 text-primary font-mono break-all">{{ task.task_id }}</dd>
          </div>
          <div>
            <dt class="text-secondary">文件名</dt>
            <dd class="mt-1 text-primary break-words" dir="auto">{{ task.filename }}</dd>
          </div>
          <div>
            <dt class="text-secondary">parse_method</dt>
            <dd class="mt-1 text-primary">{{ task.parse_method }}</dd>
          </div>
          <div>
            <dt class="text-secondary">lang</dt>
            <dd class="mt-1 text-primary">{{ task.lang }}</dd>
          </div>
          <div>
            <dt class="text-secondary">优先级</dt>
            <dd class="mt-1 text-primary">{{ task.priority }}</dd>
          </div>
          <div>
            <dt class="text-secondary">重试次数</dt>
            <dd class="mt-1 text-primary">{{ task.retry_count }}</dd>
          </div>
          <div>
            <dt class="text-secondary">创建时间</dt>
            <dd class="mt-1 text-primary">{{ formatDateTime(task.created_at) }}</dd>
          </div>
          <div>
            <dt class="text-secondary">开始时间</dt>
            <dd class="mt-1 text-primary">{{ formatDateTime(task.started_at) }}</dd>
          </div>
          <div>
            <dt class="text-secondary">完成时间</dt>
            <dd class="mt-1 text-primary">{{ formatDateTime(task.completed_at) }}</dd>
          </div>
          <div>
            <dt class="text-secondary">处理时长</dt>
            <dd class="mt-1 text-primary">
              {{ task.processing_duration_ms !== null && task.processing_duration_ms !== undefined
                ? `${task.processing_duration_ms} ms`
                : formatDuration(task.started_at, task.completed_at) }}
            </dd>
          </div>
        </dl>

        <div v-if="task.error_message" class="mt-4 rounded-lg border border-danger bg-danger p-3 text-sm text-danger break-words" dir="auto">
          {{ task.error_message }}
        </div>

        <div class="mt-5 flex gap-3">
          <button
            v-if="task.status === 'pending'"
            @click="cancel"
            class="btn btn-secondary flex items-center"
          >
            <X class="w-4 h-4 mr-2" />
            取消任务
          </button>
          <button
            v-if="task.status === 'failed' || task.status === 'canceled'"
            @click="retry"
            class="btn btn-secondary flex items-center"
          >
            <RotateCcw class="w-4 h-4 mr-2" />
            重试任务
          </button>
          <button @click="refresh" class="btn btn-primary flex items-center">
            <RefreshCw class="w-4 h-4 mr-2" />
            刷新
          </button>
        </div>
      </div>

      <div class="card">
        <h2 class="section-title mb-3">解析结果</h2>
        <div v-if="task.result" class="bg-code text-code text-xs rounded-lg p-4 overflow-auto max-h-[480px]" dir="auto">
          <pre class="whitespace-pre-wrap break-words">{{ task.result }}</pre>
        </div>
        <div v-else class="text-sm text-secondary">暂无结果输出</div>
      </div>
    </div>

    <ConfirmDialog
      v-model="confirmState.visible"
      :title="confirmState.title"
      :message="confirmState.message"
      :type="confirmState.type"
      @confirm="executeConfirmedAction"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, RefreshCw, RotateCcw, X } from 'lucide-vue-next'

import ConfirmDialog from '@/components/ConfirmDialog.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useTaskStore } from '@/stores'
import { formatDateTime, formatDuration } from '@/utils/format'
import { toast } from '@/utils/toast'

const route = useRoute()
const taskStore = useTaskStore()

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

function shouldPollCurrentTask() {
  if (document.visibilityState !== 'visible') {
    return false
  }
  if (!task.value) {
    return false
  }
  return task.value.status === 'pending' || task.value.status === 'processing'
}

async function refresh(options: { silent?: boolean } = {}) {
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

async function cancel() {
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

async function retry() {
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
  if (timerId) {
    clearTimeout(timerId)
  }
  if (!shouldPollCurrentTask()) {
    timerId = null
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
  if (timerId) {
    clearTimeout(timerId)
    timerId = null
  }
}

onMounted(async () => {
  await refresh()
  document.addEventListener('visibilitychange', handleVisibilityChange)
  if (shouldPollCurrentTask()) {
    schedulePoll()
  }
})

onUnmounted(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  if (timerId) {
    clearTimeout(timerId)
    timerId = null
  }
})
</script>
