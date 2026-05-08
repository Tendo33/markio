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
      <TaskListFilters
        :loading="taskStore.listLoading"
        :page-size="pageSize"
        :status="status"
        @update:page-size="pageSize = $event"
        @update:status="status = $event"
        @apply="applyFilters"
        @refresh="refresh"
      />

      <div
        v-if="taskStore.listError"
        class="card mb-6 border-danger bg-danger text-sm text-danger break-words"
        dir="auto"
        role="alert"
      >
        {{ taskStore.listError }}
      </div>

      <TaskListResults
        :loading="taskStore.listLoading"
        :max-page="taskStore.maxPage"
        :page="taskStore.page"
        :tasks="taskStore.tasks"
        :total="taskStore.total"
        @cancel="cancelTask"
        @retry="retryTask"
        @prev-page="prevPage"
        @next-page="nextPage"
      />
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
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import TaskListFilters from '@/components/task-list/TaskListFilters.vue'
import TaskListResults from '@/components/task-list/TaskListResults.vue'
import { useTaskListPage } from '@/composables/useTaskListPage'

const {
  applyFilters,
  cancelTask,
  confirmState,
  executeConfirmedAction,
  nextPage,
  pageSize,
  prevPage,
  refresh,
  retryTask,
  status,
  taskStore,
  tokenConfigured,
} = useTaskListPage()
</script>
