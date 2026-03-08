<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">队列管理</h1>
      <p class="mt-1 text-sm text-gray-600">暂停/恢复队列，并监控 worker 运行状态</p>
    </div>

    <div class="space-y-6">
      <div>
        <h2 class="text-lg font-semibold text-gray-900 mb-4">队列状态</h2>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard title="队列长度" :value="queueStore.health.queued" subtitle="等待执行任务" :icon="Clock" color="gray" />
          <StatCard title="处理中" :value="queueStore.health.processing" subtitle="正在运行任务" :icon="Loader" color="yellow" />
          <StatCard title="Worker" :value="queueStore.health.workers" subtitle="工作线程数" :icon="Cpu" color="blue" />
          <StatCard title="暂停状态" :value="queueStore.health.paused ? '是' : '否'" subtitle="队列是否暂停" :icon="PauseCircle" :color="queueStore.health.paused ? 'red' : 'green'" />
        </div>
      </div>

      <div class="card">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">管理操作</h2>
        <div class="flex flex-wrap gap-3">
          <button @click="pause" :disabled="actionLocked" class="btn btn-secondary flex items-center">
            <Pause class="w-4 h-4 mr-2" />
            暂停队列
          </button>
          <button @click="resume" :disabled="actionLocked" class="btn btn-primary flex items-center">
            <Play class="w-4 h-4 mr-2" />
            恢复队列
          </button>
          <button @click="refresh" :disabled="actionLocked" class="btn btn-secondary flex items-center">
            <RefreshCw :class="{ 'animate-spin': queueStore.loading }" class="w-4 h-4 mr-2" />
            刷新状态
          </button>
        </div>
      </div>

      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">操作日志</h2>
          <button @click="logs = []" class="text-sm text-gray-600 hover:text-gray-900">清空</button>
        </div>
        <div v-if="logs.length === 0" class="text-sm text-gray-500">暂无日志</div>
        <div v-else class="space-y-2">
          <div
            v-for="(log, index) in logs"
            :key="index"
            class="p-3 rounded-lg text-sm"
            :class="log.type === 'error' ? 'bg-red-50 text-red-700' : 'bg-gray-50 text-gray-700'"
          >
            {{ formatDateTime(log.time) }} | {{ log.message }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  Clock,
  Cpu,
  Loader,
  Pause,
  PauseCircle,
  Play,
  RefreshCw,
} from 'lucide-vue-next'

import StatCard from '@/components/StatCard.vue'
import { useQueueStore } from '@/stores'
import { formatDateTime } from '@/utils/format'
import { toast } from '@/utils/toast'

const queueStore = useQueueStore()

const logs = ref<Array<{ time: string; message: string; type: 'info' | 'error' }>>([])
const actionLocked = ref(false)

function addLog(message: string, type: 'info' | 'error' = 'info') {
  logs.value.unshift({
    message,
    type,
    time: new Date().toISOString(),
  })
  if (logs.value.length > 20) {
    logs.value = logs.value.slice(0, 20)
  }
}

async function refresh() {
  if (actionLocked.value) return
  actionLocked.value = true
  try {
    await queueStore.fetchHealth()
    addLog('刷新队列状态')
  } catch (error: any) {
    const message = error?.message || '刷新队列状态失败'
    addLog(message, 'error')
    toast.error(message)
  } finally {
    actionLocked.value = false
  }
}

async function pause() {
  if (actionLocked.value) return
  actionLocked.value = true
  try {
    await queueStore.pause()
    await queueStore.fetchHealth()
    addLog('队列已暂停')
    toast.success('队列已暂停')
  } catch (error: any) {
    const message = error?.message || '暂停失败'
    addLog(message, 'error')
    toast.error(message)
  } finally {
    actionLocked.value = false
  }
}

async function resume() {
  if (actionLocked.value) return
  actionLocked.value = true
  try {
    await queueStore.resume()
    await queueStore.fetchHealth()
    addLog('队列已恢复')
    toast.success('队列已恢复')
  } catch (error: any) {
    const message = error?.message || '恢复失败'
    addLog(message, 'error')
    toast.error(message)
  } finally {
    actionLocked.value = false
  }
}

onMounted(async () => {
  await refresh()
})
</script>
