<template>
  <div class="card mb-6">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div>
        <label class="field-label" for="task-status-filter">状态</label>
        <select
          id="task-status-filter"
          :value="status"
          class="w-full px-3 py-2.5"
          @change="emit('update:status', ($event.target as HTMLSelectElement).value)"
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
          :value="String(pageSize)"
          class="w-full px-3 py-2.5"
          @change="emit('update:pageSize', Number(($event.target as HTMLSelectElement).value))"
        >
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
        </select>
      </div>

      <div class="md:col-span-2 flex items-end gap-2">
        <button @click="emit('apply')" :disabled="loading" class="btn btn-secondary">
          应用过滤
        </button>
        <button
          @click="emit('refresh')"
          :disabled="loading"
          class="btn btn-secondary flex items-center"
        >
          <RefreshCw :class="{ 'animate-spin': loading }" class="w-4 h-4 mr-1" />
          刷新
        </button>
        <router-link to="/tasks/submit" class="btn btn-primary flex items-center">
          <Plus class="w-4 h-4 mr-1" />
          提交任务
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Plus, RefreshCw } from 'lucide-vue-next'

defineProps<{
  loading: boolean
  pageSize: number
  status: string
}>()

const emit = defineEmits<{
  (event: 'apply'): void
  (event: 'refresh'): void
  (event: 'update:pageSize', value: number): void
  (event: 'update:status', value: string): void
}>()
</script>
