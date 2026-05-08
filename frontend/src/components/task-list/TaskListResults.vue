<template>
  <div class="card">
    <div
      v-if="loading && tasks.length === 0"
      class="text-center py-12"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <LoadingSpinner text="加载中" />
    </div>

    <div v-else-if="tasks.length === 0" class="text-center py-12 text-secondary">
      <FileQuestion class="w-16 h-16 mx-auto mb-4 text-tertiary" />
      <p>还没有任务。</p>
      <p class="mt-2 text-sm">提交一个文件后，任务状态会在这里持续更新。</p>
    </div>

    <div v-else>
      <div class="space-y-3 md:hidden">
        <article
          v-for="task in tasks"
          :key="task.task_id"
          class="stack-card"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0 flex-1">
              <p class="break-all text-xs text-secondary">任务 {{ task.task_id }}</p>
              <h2 class="mt-1 truncate text-sm font-semibold text-primary" :title="task.filename" dir="auto">
                {{ task.filename }}
              </h2>
            </div>
            <StatusBadge :status="task.status" />
          </div>

          <dl class="mt-4 grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt class="text-secondary">优先级</dt>
              <dd class="mt-1 text-primary">{{ task.priority }}</dd>
            </div>
            <div>
              <dt class="text-secondary">重试次数</dt>
              <dd class="mt-1 text-primary">{{ task.retry_count }}</dd>
            </div>
            <div class="col-span-2">
              <dt class="text-secondary">创建时间</dt>
              <dd class="mt-1 text-primary">{{ formatRelativeTime(task.created_at) }}</dd>
            </div>
          </dl>

          <div class="mt-4 flex flex-wrap gap-2">
            <router-link
              :to="`/tasks/${task.task_id}`"
              class="btn btn-secondary text-xs"
              :aria-label="`查看任务 ${task.task_id} 详情`"
            >
              <Eye class="w-4 h-4" />
              查看详情
            </router-link>
            <button
              v-if="task.status === 'pending'"
              @click="emit('cancel', task.task_id)"
              type="button"
              class="btn btn-secondary text-xs"
              :aria-label="`取消任务 ${task.task_id}`"
            >
              <X class="w-4 h-4" />
              取消任务
            </button>
            <button
              v-if="task.status === 'failed' || task.status === 'canceled'"
              @click="emit('retry', task.task_id)"
              type="button"
              class="btn btn-secondary text-xs"
              :aria-label="`重试任务 ${task.task_id}`"
            >
              <RotateCcw class="w-4 h-4" />
              重新提交
            </button>
          </div>
        </article>
      </div>

      <div class="hidden overflow-x-auto md:block">
        <table class="min-w-full divide-y divide-[color:var(--border-subtle)]">
          <thead class="bg-muted">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                任务ID
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                文件名
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                状态
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                优先级
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                重试
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                创建时间
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                操作
              </th>
            </tr>
          </thead>
          <tbody class="bg-surface divide-y divide-[color:var(--border-subtle)]">
            <tr v-for="task in tasks" :key="task.task_id" class="hover:bg-muted">
              <td
                class="px-6 py-4 whitespace-nowrap text-xs text-secondary font-mono"
                :title="task.task_id"
                dir="auto"
              >
                {{ task.task_id }}
              </td>
              <td
                class="px-6 py-4 whitespace-nowrap text-sm text-primary max-w-xs truncate"
                :title="task.filename"
                dir="auto"
              >
                {{ task.filename }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap"><StatusBadge :status="task.status" /></td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-secondary">{{ task.priority }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-secondary">{{ task.retry_count }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-secondary">
                {{ formatRelativeTime(task.created_at) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <div class="flex items-center gap-2">
                  <router-link
                    :to="`/tasks/${task.task_id}`"
                    class="icon-btn text-secondary hover:text-primary"
                    title="详情"
                    :aria-label="`查看任务 ${task.task_id} 详情`"
                  >
                    <Eye class="w-4 h-4" />
                  </router-link>
                  <button
                    v-if="task.status === 'pending'"
                    @click="emit('cancel', task.task_id)"
                    type="button"
                    class="icon-btn text-danger hover:text-danger"
                    title="取消"
                    :aria-label="`取消任务 ${task.task_id}`"
                  >
                    <X class="w-4 h-4" />
                  </button>
                  <button
                    v-if="task.status === 'failed' || task.status === 'canceled'"
                    @click="emit('retry', task.task_id)"
                    type="button"
                    class="icon-btn text-warning hover:text-warning"
                    title="重试"
                    :aria-label="`重试任务 ${task.task_id}`"
                  >
                    <RotateCcw class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="tasks.length > 0" class="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div class="text-sm text-secondary">共 {{ total }} 条</div>
      <div class="flex items-center gap-2">
        <button
          @click="emit('prevPage')"
          :disabled="page <= 1"
          type="button"
          aria-label="上一页"
          class="icon-btn text-secondary hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronLeft class="w-5 h-5" />
        </button>
        <span class="text-sm text-secondary">第 {{ page }} / {{ maxPage }} 页</span>
        <button
          @click="emit('nextPage')"
          :disabled="page >= maxPage"
          type="button"
          aria-label="下一页"
          class="icon-btn text-secondary hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronRight class="w-5 h-5" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ChevronLeft, ChevronRight, Eye, FileQuestion, RotateCcw, X } from 'lucide-vue-next'

import type { TaskRecord } from '@/api/types'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { formatRelativeTime } from '@/utils/format'

defineProps<{
  loading: boolean
  maxPage: number
  page: number
  tasks: TaskRecord[]
  total: number
}>()

const emit = defineEmits<{
  (event: 'cancel', taskId: string): void
  (event: 'nextPage'): void
  (event: 'prevPage'): void
  (event: 'retry', taskId: string): void
}>()
</script>
