<template>
  <div>
    <div class="mb-4">
      <button @click="$router.back()" class="text-sm text-gray-600 hover:text-gray-900 flex items-center">
        <ArrowLeft class="w-4 h-4 mr-1" />
        返回
      </button>
    </div>

    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">任务详情</h1>
      <p class="mt-1 text-sm text-gray-600">跟踪任务执行状态与解析输出</p>
    </div>

    <div v-if="taskStore.loading && !task" class="text-center py-12">
      <LoadingSpinner size="lg" text="加载中" />
    </div>

    <div v-else-if="taskStore.error" class="card bg-red-50 border-red-200 text-red-700">
      {{ taskStore.error }}
    </div>

    <div v-else-if="task" class="space-y-6">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">基本信息</h2>
          <StatusBadge :status="task.status" />
        </div>

        <dl class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <dt class="text-gray-500">任务ID</dt>
            <dd class="mt-1 text-gray-900 font-mono break-all">{{ task.task_id }}</dd>
          </div>
          <div>
            <dt class="text-gray-500">文件名</dt>
            <dd class="mt-1 text-gray-900">{{ task.filename }}</dd>
          </div>
          <div>
            <dt class="text-gray-500">parse_method</dt>
            <dd class="mt-1 text-gray-900">{{ task.parse_method }}</dd>
          </div>
          <div>
            <dt class="text-gray-500">lang</dt>
            <dd class="mt-1 text-gray-900">{{ task.lang }}</dd>
          </div>
          <div>
            <dt class="text-gray-500">优先级</dt>
            <dd class="mt-1 text-gray-900">{{ task.priority }}</dd>
          </div>
          <div>
            <dt class="text-gray-500">重试次数</dt>
            <dd class="mt-1 text-gray-900">{{ task.retry_count }}</dd>
          </div>
          <div>
            <dt class="text-gray-500">创建时间</dt>
            <dd class="mt-1 text-gray-900">{{ formatDateTime(task.created_at) }}</dd>
          </div>
          <div>
            <dt class="text-gray-500">开始时间</dt>
            <dd class="mt-1 text-gray-900">{{ formatDateTime(task.started_at) }}</dd>
          </div>
          <div>
            <dt class="text-gray-500">完成时间</dt>
            <dd class="mt-1 text-gray-900">{{ formatDateTime(task.completed_at) }}</dd>
          </div>
          <div>
            <dt class="text-gray-500">处理时长</dt>
            <dd class="mt-1 text-gray-900">{{ formatDuration(task.started_at, task.completed_at) }}</dd>
          </div>
        </dl>

        <div v-if="task.error_message" class="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
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
        <h2 class="text-lg font-semibold text-gray-900 mb-3">解析结果</h2>
        <div v-if="task.result" class="bg-gray-900 text-gray-100 text-xs rounded-lg p-4 overflow-auto max-h-[480px]">
          <pre class="whitespace-pre-wrap">{{ task.result }}</pre>
        </div>
        <div v-else class="text-sm text-gray-500">暂无结果输出</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, RefreshCw, RotateCcw, X } from 'lucide-vue-next'

import LoadingSpinner from '@/components/LoadingSpinner.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useTaskStore } from '@/stores'
import { formatDateTime, formatDuration } from '@/utils/format'

const route = useRoute()
const taskStore = useTaskStore()

let timerId: number | null = null

const taskId = computed(() => String(route.params.id))
const task = computed(() => taskStore.currentTask)

async function refresh() {
  await taskStore.loadTask(taskId.value)
}

async function cancel() {
  await taskStore.cancel(taskId.value)
  await refresh()
}

async function retry() {
  await taskStore.retry(taskId.value)
  await refresh()
}

onMounted(async () => {
  await refresh()
  timerId = window.setInterval(async () => {
    if (!task.value) return
    if (task.value.status === 'pending' || task.value.status === 'processing') {
      await refresh()
    }
  }, 5000)
})

onUnmounted(() => {
  if (timerId) {
    clearInterval(timerId)
    timerId = null
  }
})
</script>
