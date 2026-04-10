<template>
  <div :aria-busy="taskStore.listLoading ? 'true' : 'false'">
    <div class="mb-6">
      <h1 class="page-title">任务列表</h1>
      <p class="mt-1 page-subtitle">分页查询、状态筛选、重试与取消</p>
    </div>

    <div
      v-if="!tokenConfigured"
      class="card border-warning bg-warning text-sm text-warning break-words"
      dir="auto"
    >
      还没有可用的 JWT Token。先在顶部保存 Token，再筛选、翻页和查看任务详情。
    </div>

    <template v-else>
      <div class="card mb-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label class="field-label" for="task-status-filter">状态</label>
            <select
              id="task-status-filter"
              v-model="status"
              class="w-full px-3 py-2.5"
            >
              <option value="">全部</option>
              <option value="pending">pending</option>
              <option value="processing">processing</option>
              <option value="completed">completed</option>
              <option value="failed">failed</option>
              <option value="canceled">canceled</option>
            </select>
          </div>

          <div>
            <label class="field-label" for="task-page-size-filter">每页数量</label>
            <select
              id="task-page-size-filter"
              v-model.number="pageSize"
              class="w-full px-3 py-2.5"
            >
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
            </select>
          </div>

          <div class="md:col-span-2 flex items-end gap-2">
            <button @click="applyFilters" :disabled="taskStore.listLoading" class="btn btn-secondary">
              应用过滤
            </button>
            <button
              @click="refresh"
              :disabled="taskStore.listLoading"
              class="btn btn-secondary flex items-center"
            >
              <RefreshCw :class="{ 'animate-spin': taskStore.listLoading }" class="w-4 h-4 mr-1" />
              刷新
            </button>
            <router-link to="/tasks/submit" class="btn btn-primary flex items-center">
              <Plus class="w-4 h-4 mr-1" />
              提交任务
            </router-link>
          </div>
        </div>
      </div>

      <div
        v-if="taskStore.listError"
        class="card mb-6 border-danger bg-danger text-sm text-danger break-words"
        dir="auto"
        role="alert"
      >
        {{ taskStore.listError }}
      </div>

      <div class="card">
        <div
          v-if="taskStore.listLoading && taskStore.tasks.length === 0"
          class="text-center py-12"
          role="status"
          aria-live="polite"
          aria-busy="true"
        >
          <LoadingSpinner text="加载中" />
        </div>

        <div v-else-if="taskStore.tasks.length === 0" class="text-center py-12 text-secondary">
          <FileQuestion class="w-16 h-16 mx-auto mb-4 text-tertiary" />
          <p>还没有任务。</p>
          <p class="mt-2 text-sm">提交一个文件后，任务状态会在这里持续更新。</p>
        </div>

        <div v-else>
          <div class="space-y-3 md:hidden">
            <article
              v-for="task in taskStore.tasks"
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
                  @click="cancelTask(task.task_id)"
                  type="button"
                  class="btn btn-secondary text-xs"
                  :aria-label="`取消任务 ${task.task_id}`"
                >
                  <X class="w-4 h-4" />
                  取消任务
                </button>
                <button
                  v-if="task.status === 'failed' || task.status === 'canceled'"
                  @click="retryTask(task.task_id)"
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
                <tr v-for="task in taskStore.tasks" :key="task.task_id" class="hover:bg-muted">
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
                        @click="cancelTask(task.task_id)"
                        type="button"
                        class="icon-btn text-danger hover:text-danger"
                        title="取消"
                        :aria-label="`取消任务 ${task.task_id}`"
                      >
                        <X class="w-4 h-4" />
                      </button>
                      <button
                        v-if="task.status === 'failed' || task.status === 'canceled'"
                        @click="retryTask(task.task_id)"
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

        <div v-if="taskStore.tasks.length > 0" class="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div class="text-sm text-secondary">共 {{ taskStore.total }} 条</div>
          <div class="flex items-center gap-2">
            <button
              @click="prevPage"
              :disabled="taskStore.page <= 1"
              type="button"
              aria-label="上一页"
              class="icon-btn text-secondary hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft class="w-5 h-5" />
            </button>
            <span class="text-sm text-secondary">第 {{ taskStore.page }} / {{ taskStore.maxPage }} 页</span>
            <button
              @click="nextPage"
              :disabled="taskStore.page >= taskStore.maxPage"
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
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'
import {
  ChevronLeft,
  ChevronRight,
  Eye,
  FileQuestion,
  Plus,
  RefreshCw,
  RotateCcw,
  X,
} from 'lucide-vue-next'

import type { TaskStatus } from '@/api/types'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useAuthStore, useTaskStore } from '@/stores'
import { formatRelativeTime } from '@/utils/format'
import { toast } from '@/utils/toast'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const taskStore = useTaskStore()
const { configured: tokenConfigured } = storeToRefs(authStore)

const VALID_PAGE_SIZES = [10, 20, 50]
const VALID_STATUSES: TaskStatus[] = ['pending', 'processing', 'completed', 'failed', 'canceled']

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

async function cancelTask(taskId: string) {
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

async function retryTask(taskId: string) {
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
</script>
