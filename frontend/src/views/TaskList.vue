<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">任务列表</h1>
      <p class="mt-1 text-sm text-gray-600">分页查询、状态筛选、重试与取消</p>
    </div>

    <div class="card mb-6">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">状态</label>
          <select v-model="status" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
            <option value="">全部</option>
            <option value="pending">pending</option>
            <option value="processing">processing</option>
            <option value="completed">completed</option>
            <option value="failed">failed</option>
            <option value="canceled">canceled</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">每页数量</label>
          <select v-model.number="pageSize" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="50">50</option>
          </select>
        </div>

        <div class="md:col-span-2 flex items-end gap-2">
          <button @click="applyFilters" :disabled="taskStore.loading" class="btn btn-secondary">应用过滤</button>
          <button @click="refresh" :disabled="taskStore.loading" class="btn btn-secondary flex items-center">
            <RefreshCw :class="{ 'animate-spin': taskStore.loading }" class="w-4 h-4 mr-1" />
            刷新
          </button>
          <router-link to="/tasks/submit" class="btn btn-primary flex items-center">
            <Plus class="w-4 h-4 mr-1" />
            提交任务
          </router-link>
        </div>
      </div>
    </div>

    <div v-if="taskStore.listError" class="card mb-6 border-red-200 bg-red-50 text-sm text-red-700">
      {{ taskStore.listError }}
    </div>

    <div class="card">
      <div v-if="taskStore.loading && taskStore.tasks.length === 0" class="text-center py-12">
        <LoadingSpinner text="加载中" />
      </div>

      <div v-else-if="taskStore.tasks.length === 0" class="text-center py-12 text-gray-500">
        <FileQuestion class="w-16 h-16 mx-auto mb-4 text-gray-400" />
        <p>暂无任务</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">任务ID</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">文件名</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">优先级</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">重试</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">创建时间</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="task in taskStore.tasks" :key="task.task_id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap text-xs text-gray-600 font-mono">{{ task.task_id }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 max-w-xs truncate">{{ task.filename }}</td>
              <td class="px-6 py-4 whitespace-nowrap"><StatusBadge :status="task.status" /></td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ task.priority }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ task.retry_count }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ formatRelativeTime(task.created_at) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <div class="flex items-center gap-2">
                  <router-link
                    :to="`/tasks/${task.task_id}`"
                    class="text-primary-600 hover:text-primary-700"
                    title="详情"
                    :aria-label="`查看任务 ${task.task_id} 详情`"
                  >
                    <Eye class="w-4 h-4" />
                  </router-link>
                  <button
                    v-if="task.status === 'pending'"
                    @click="cancelTask(task.task_id)"
                    type="button"
                    class="text-red-600 hover:text-red-700"
                    title="取消"
                    :aria-label="`取消任务 ${task.task_id}`"
                  >
                    <X class="w-4 h-4" />
                  </button>
                  <button
                    v-if="task.status === 'failed' || task.status === 'canceled'"
                    @click="retryTask(task.task_id)"
                    type="button"
                    class="text-amber-600 hover:text-amber-700"
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

      <div v-if="taskStore.tasks.length > 0" class="mt-4 flex items-center justify-between">
        <div class="text-sm text-gray-600">共 {{ taskStore.total }} 条</div>
        <div class="flex items-center gap-2">
          <button
            @click="prevPage"
            :disabled="taskStore.page <= 1"
            type="button"
            aria-label="上一页"
            class="p-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft class="w-5 h-5" />
          </button>
          <span class="text-sm text-gray-600">第 {{ taskStore.page }} / {{ taskStore.maxPage }} 页</span>
          <button
            @click="nextPage"
            :disabled="taskStore.page >= taskStore.maxPage"
            type="button"
            aria-label="下一页"
            class="p-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronRight class="w-5 h-5" />
          </button>
        </div>
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
import { onMounted, ref } from 'vue'
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

import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import type { TaskStatus } from '@/api/types'
import { useTaskStore } from '@/stores'
import { formatRelativeTime } from '@/utils/format'
import { toast } from '@/utils/toast'

const taskStore = useTaskStore()

const status = ref(taskStore.statusFilter)
const pageSize = ref(taskStore.pageSize)
const confirmState = ref({
  visible: false,
  title: '',
  message: '',
  type: 'warning' as 'danger' | 'warning' | 'info',
  action: null as null | (() => Promise<void>),
})

async function applyFilters() {
  await runWithErrorToast(
    () => taskStore.setFilters(status.value as TaskStatus | '', pageSize.value),
    '应用过滤失败',
  )
}

async function refresh() {
  await runWithErrorToast(() => taskStore.loadTasks(taskStore.page), '刷新任务列表失败')
}

async function prevPage() {
  if (taskStore.page <= 1) return
  await runWithErrorToast(() => taskStore.loadTasks(taskStore.page - 1), '翻页失败')
}

async function nextPage() {
  if (taskStore.page >= taskStore.maxPage) return
  await runWithErrorToast(() => taskStore.loadTasks(taskStore.page + 1), '翻页失败')
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

async function runWithErrorToast(
  action: () => Promise<unknown>,
  fallbackMessage: string,
) {
  try {
    await action()
  } catch (error: any) {
    toast.error(error?.message || fallbackMessage)
  }
}

onMounted(async () => {
  await runWithErrorToast(() => taskStore.loadTasks(1), '加载任务列表失败')
})
</script>
