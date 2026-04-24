<template>
  <div :aria-busy="queueStore.loading ? 'true' : 'false'">
    <div class="mb-6">
      <h1 class="page-title">队列管理</h1>
      <p class="mt-1 page-subtitle">在管理员视角下暂停、恢复并观察任务吞吐。</p>
    </div>

    <div v-if="!tokenConfigured" class="card border-warning bg-warning text-sm text-warning break-words" dir="auto">
      还没有可用的 JWT Token。先在顶部保存 Token，管理员才能查看和管理队列。
    </div>

    <div v-else-if="!canManageQueue" class="space-y-6">
      <div class="card border-warning bg-warning text-sm text-warning break-words" dir="auto">
        当前 JWT 角色是 <code>{{ currentRole }}</code>，没有全局队列管理权限。普通用户可以回到仪表盘查看自己的任务概览。
      </div>

      <div class="card">
        <h2 class="section-title mb-4">操作日志</h2>
        <div class="text-sm text-secondary">仅 admin 角色可查看全局队列健康度、暂停或恢复队列。</div>
      </div>
    </div>

    <div v-else class="space-y-6">
      <div>
        <h2 class="section-title mb-4">队列状态</h2>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard title="队列长度" :value="queueStore.health.queued" subtitle="等待执行任务" :icon="Clock" color="gray" />
          <StatCard title="处理中" :value="queueStore.health.processing" subtitle="正在运行任务" :icon="Loader" color="yellow" />
          <StatCard title="Worker" :value="queueStore.health.workers" subtitle="工作线程数" :icon="Cpu" color="blue" />
          <StatCard
            title="暂停状态"
            :value="queueStore.health.paused ? '是' : '否'"
            subtitle="队列是否暂停"
            :icon="PauseCircle"
            :color="queueStore.health.paused ? 'red' : 'green'"
          />
        </div>
      </div>

      <div class="card">
        <h2 class="section-title mb-4">管理操作</h2>
        <div class="mb-3 text-sm text-secondary">
          当前角色：<span class="font-medium text-primary">{{ currentRole }}</span>
        </div>
        <div class="flex flex-wrap gap-3">
          <button
            @click="pause"
            :disabled="actionLocked"
            class="btn btn-secondary flex items-center"
          >
            <Pause class="w-4 h-4 mr-2" />
            暂停队列
          </button>
          <button
            @click="resume"
            :disabled="actionLocked"
            class="btn btn-primary flex items-center"
          >
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
          <h2 class="section-title">操作日志</h2>
          <button @click="logs = []" class="text-link text-sm">清空</button>
        </div>
        <div v-if="logs.length === 0" class="text-sm text-secondary">还没有操作记录。</div>
        <div v-else class="space-y-2">
          <div
            v-for="(log, index) in logs"
            :key="index"
            class="p-3 rounded-lg text-sm break-words"
            :class="log.type === 'error' ? 'bg-danger text-danger' : 'bg-muted text-tertiary'"
            dir="auto"
          >
            {{ formatDateTime(log.time) }} | {{ log.message }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { Clock, Cpu, Loader, Pause, PauseCircle, Play, RefreshCw } from 'lucide-vue-next'

import StatCard from '@/components/StatCard.vue'
import { useAuthStore, useQueueStore } from '@/stores'
import { formatDateTime } from '@/utils/format'
import { toast } from '@/utils/toast'

const authStore = useAuthStore()
const queueStore = useQueueStore()
const { configured: tokenConfigured, role: currentRole } = storeToRefs(authStore)

const logs = ref<Array<{ time: string; message: string; type: 'info' | 'error' }>>([])
const actionLocked = ref(false)
const canManageQueue = computed(() => tokenConfigured.value && currentRole.value === 'admin')

function syncRole() {
  authStore.refreshFromStorage()
  if (!canManageQueue.value) {
    queueStore.reset()
  }
}

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
  if (!canManageQueue.value || actionLocked.value) return
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
  if (!canManageQueue.value) {
    return
  }
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
  if (!canManageQueue.value) {
    return
  }
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
  syncRole()
  if (canManageQueue.value) {
    await refresh()
  }
})

watch([tokenConfigured, currentRole], async () => {
  syncRole()
  if (canManageQueue.value) {
    await refresh()
  }
})
</script>
