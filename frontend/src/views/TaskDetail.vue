<template>
  <div :aria-busy="taskStore.detailLoading ? 'true' : 'false'">
    <div class="mb-4">
      <button @click="$router.back()" class="text-link flex items-center text-sm">
        <ArrowLeft class="w-4 h-4 mr-1" />
        返回
      </button>
    </div>

    <div class="mb-6">
      <h1 class="page-title">任务详情</h1>
      <p class="mt-1 page-subtitle">查看任务状态、参数和最终解析结果。</p>
    </div>

      <div
        v-if="!tokenConfigured"
        class="card border-warning bg-warning text-sm text-warning break-words"
        dir="auto"
      >
        还没有可用的 JWT Token。先在顶部保存 Token，再查看任务详情和解析结果。
      </div>

    <template v-else>
      <div
        v-if="taskStore.detailLoading && !task"
        class="text-center py-12"
        role="status"
        aria-live="polite"
        aria-busy="true"
      >
        <LoadingSpinner size="lg" text="加载中" />
      </div>

      <div
        v-else-if="taskStore.detailError"
        class="card bg-danger border-danger text-danger break-words"
        dir="auto"
      >
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
              <dt class="text-secondary">解析方式</dt>
              <dd class="mt-1 text-primary">{{ task.parse_method }}</dd>
            </div>
            <div>
              <dt class="text-secondary">文档语言</dt>
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
                {{
                  task.processing_duration_ms !== null && task.processing_duration_ms !== undefined
                    ? `${task.processing_duration_ms} ms`
                    : formatDuration(task.started_at, task.completed_at)
                }}
              </dd>
            </div>
          </dl>

          <div
            v-if="task.error_message"
            class="mt-4 rounded-lg border border-danger bg-danger p-3 text-sm text-danger break-words"
            dir="auto"
          >
            {{ task.error_message }}
          </div>

          <div class="mt-5 flex flex-wrap gap-3">
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
          <div
            v-if="task.result !== null"
            class="bg-code text-code text-xs rounded-lg p-4 overflow-auto max-h-[480px]"
            dir="auto"
          >
            <pre class="whitespace-pre-wrap break-words">{{ task.result }}</pre>
          </div>
          <div v-else class="text-sm text-secondary">
            {{
              task.status === 'completed'
                ? '解析已完成，但结果为空。'
                : '结果还没生成。任务完成后会显示在这里。'
            }}
          </div>
        </div>
      </div>
    </template>

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
import { ArrowLeft, RefreshCw, RotateCcw, X } from 'lucide-vue-next'

import ConfirmDialog from '@/components/ConfirmDialog.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useTaskDetailPolling } from '@/composables/useTaskDetailPolling'
import { formatDateTime, formatDuration } from '@/utils/format'

const {
  cancel,
  confirmState,
  executeConfirmedAction,
  refresh,
  retry,
  task,
  taskStore,
  tokenConfigured,
} = useTaskDetailPolling()
</script>
