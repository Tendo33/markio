<template>
  <div>
    <div class="mb-6 lg:mb-10">
      <h1 class="page-title">仪表盘</h1>
      <p class="mt-2 lg:mt-3 page-subtitle">实时监控异步文档任务状态</p>
    </div>

    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6 mb-6 lg:mb-8">
      <StatCard title="等待中" :value="stats.pending" subtitle="待处理任务" :icon="Clock" color="gray" />
      <StatCard title="处理中" :value="stats.processing" subtitle="正在解析" :icon="Loader" color="yellow" />
      <StatCard title="已完成" :value="stats.completed" subtitle="解析成功" :icon="CheckCircle" color="green" />
      <StatCard title="失败" :value="stats.failed" subtitle="需要重试" :icon="XCircle" color="red" />
    </div>

    <div v-if="taskStore.dashboardError" class="card mb-6 border-danger bg-danger text-sm text-danger break-words" dir="auto">
      {{ taskStore.dashboardError }}
    </div>

    <div v-if="sla" class="grid grid-cols-1 md:grid-cols-3 gap-3 sm:gap-4 lg:gap-6 mb-6 lg:mb-8">
      <StatCard title="平均耗时" :value="`${sla.avg_ms} ms`" subtitle="已完成/失败任务" :icon="Clock3" color="blue" />
      <StatCard title="P95 耗时" :value="`${sla.p95_ms} ms`" subtitle="SLA 观测" :icon="Gauge" color="blue" />
      <StatCard title="最大耗时" :value="`${sla.max_ms} ms`" subtitle="高水位" :icon="Timer" color="blue" />
    </div>

    <div class="mb-6 lg:mb-8">
      <div class="card">
        <h2 class="section-title mb-3 lg:mb-4">快捷操作</h2>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 lg:gap-3">
          <router-link to="/tasks/submit" class="btn btn-primary flex items-center justify-center">
            <Upload class="w-4 h-4 mr-2" />
            提交任务
          </router-link>
          <router-link to="/tasks" class="btn btn-secondary flex items-center justify-center">
            <ListTodo class="w-4 h-4 mr-2" />
            任务列表
          </router-link>
          <router-link to="/queue" class="btn btn-secondary flex items-center justify-center">
            <Settings class="w-4 h-4 mr-2" />
            队列管理
          </router-link>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
        <h2 class="section-title">最近任务</h2>
        <button @click="refresh" :disabled="taskStore.dashboardLoading" class="text-sm text-primary-600 hover:text-primary-700 flex items-center">
          <RefreshCw :class="{ 'animate-spin': taskStore.dashboardLoading }" class="w-4 h-4 mr-1" />
          刷新
        </button>
      </div>

      <div
        v-if="taskStore.dashboardLoading && recentTasks.length === 0"
        class="text-center py-8"
        role="status"
        aria-live="polite"
        aria-busy="true"
      >
        <LoadingSpinner text="加载中" />
      </div>

      <div v-else-if="recentTasks.length === 0" class="text-center py-8 text-secondary">
        <FileQuestion class="w-12 h-12 mx-auto mb-2 text-tertiary" />
        <p>暂无任务</p>
      </div>

      <div v-else class="overflow-x-auto -mx-4 sm:-mx-6 lg:-mx-8">
        <div class="inline-block min-w-full align-middle px-4 sm:px-6 lg:px-8">
          <table class="min-w-full divide-y divide-[color:var(--border-subtle)]">
            <thead>
              <tr class="bg-muted">
                <th class="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">文件名</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">状态</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">优先级</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">创建时间</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">操作</th>
              </tr>
            </thead>
            <tbody class="bg-surface divide-y divide-[color:var(--border-subtle)]">
              <tr v-for="task in recentTasks" :key="task.task_id" class="hover:bg-muted">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-primary max-w-xs truncate" :title="task.filename" dir="auto">
                  {{ task.filename }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap"><StatusBadge :status="task.status" /></td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-secondary">{{ task.priority }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-secondary">{{ formatRelativeTime(task.created_at) }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-secondary">
                  <router-link :to="`/tasks/${task.task_id}`" class="text-primary-600 hover:text-primary-700 flex items-center">
                    <Eye class="w-4 h-4 mr-1" />
                    详情
                  </router-link>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  CheckCircle,
  Clock,
  Clock3,
  Eye,
  FileQuestion,
  Gauge,
  ListTodo,
  Loader,
  RefreshCw,
  Settings,
  Timer,
  Upload,
  XCircle,
} from 'lucide-vue-next'

import LoadingSpinner from '@/components/LoadingSpinner.vue'
import StatCard from '@/components/StatCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useTaskStore } from '@/stores'
import { formatRelativeTime } from '@/utils/format'
import { toast } from '@/utils/toast'

const taskStore = useTaskStore()

const stats = computed(() => {
  return (
    taskStore.dashboard?.stats ?? {
      pending: 0,
      processing: 0,
      completed: 0,
      failed: 0,
    }
  )
})

const recentTasks = computed(() => taskStore.dashboard?.recent_tasks ?? [])
const sla = computed(() => taskStore.dashboard?.sla ?? null)

async function refresh() {
  try {
    await taskStore.loadDashboard(10)
  } catch (error: any) {
    toast.error(error?.message || '加载仪表盘失败')
  }
}

</script>
