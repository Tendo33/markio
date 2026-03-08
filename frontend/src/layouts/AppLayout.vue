<template>
  <div class="min-h-screen bg-[#f7f7f8]">
    <nav class="bg-white/90 backdrop-blur-md border-b border-[#ececf1] sticky top-0 z-40">
      <div class="w-full px-4 sm:px-6 lg:px-8 xl:px-12">
        <div class="flex flex-wrap lg:flex-nowrap justify-between items-center min-h-16 py-2 gap-3">
          <div class="flex items-center min-w-0 flex-1">
            <router-link to="/" class="flex items-center gap-3 group">
              <div class="h-9 w-9 rounded-xl bg-[#202123] text-white font-semibold text-xs tracking-wide flex items-center justify-center">
                MK
              </div>
              <div>
                <div class="text-lg font-semibold text-[#202123]">Markio Console</div>
                <div class="text-xs text-[#6e6e80]">OpenAI 风格轻量任务控制台</div>
              </div>
            </router-link>
          </div>

          <div class="flex items-center gap-1 overflow-x-auto">
            <router-link
              v-for="item in navItems"
              :key="item.path"
              :to="item.path"
              :class="isActive(item.path) ? activeClass : inactiveClass"
              class="inline-flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-all duration-200 whitespace-nowrap"
            >
              <component :is="item.icon" class="w-4 h-4 mr-1.5" />
              {{ item.label }}
            </router-link>
          </div>

          <div class="flex items-center gap-2">
            <div class="hidden lg:flex items-center gap-2">
              <input
                v-model="apiToken"
                type="password"
                class="w-52 px-2 py-1.5 text-xs rounded-lg border border-[#d9d9e3] bg-white text-[#202123]"
                placeholder="JWT Token"
                aria-label="API JWT Token"
                @keyup.enter="saveToken"
              />
              <button
                @click="saveToken"
                class="px-2 py-1.5 text-xs rounded-lg border border-[#d9d9e3] text-[#4a4a62] hover:bg-[#f4f4f5]"
                aria-label="保存 API Token"
              >
                保存
              </button>
              <button
                @click="clearToken"
                class="px-2 py-1.5 text-xs rounded-lg border border-[#d9d9e3] text-[#4a4a62] hover:bg-[#f4f4f5]"
                aria-label="清除 API Token"
              >
                清除
              </button>
            </div>
            <div class="hidden md:flex items-center gap-3 px-3 py-1.5 bg-[#f7f7f8] rounded-lg border border-[#ececf1]">
              <div class="flex items-center gap-1.5 text-xs">
                <div class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></div>
                <span class="text-[#6e6e80]">处理中</span>
                <span class="font-semibold text-amber-700">{{ stats.processing }}</span>
              </div>
              <div class="w-px h-3 bg-[#d9d9e3]"></div>
              <div class="flex items-center gap-1.5 text-xs">
                <div class="w-2 h-2 rounded-full bg-slate-400"></div>
                <span class="text-[#6e6e80]">等待</span>
                <span class="font-semibold text-[#4a4a62]">{{ stats.pending }}</span>
              </div>
            </div>

            <button
              @click="refreshAll"
              :disabled="refreshing || autoRefreshing"
              aria-label="刷新仪表盘和队列状态"
              class="p-2 text-[#6e6e80] hover:text-primary-600 hover:bg-[#f4f4f5] rounded-lg transition-all duration-200"
              title="刷新"
            >
              <RefreshCw :class="{ 'animate-spin': refreshing || autoRefreshing }" class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </nav>

    <main class="w-full px-4 sm:px-6 lg:px-8 xl:px-12 py-4 lg:py-6">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { LayoutDashboard, ListTodo, RefreshCw, Settings, Upload } from 'lucide-vue-next'

import { getApiToken, setApiToken } from '@/api/client'
import { useQueueStore, useTaskStore } from '@/stores'
import { toast } from '@/utils/toast'

const route = useRoute()
const taskStore = useTaskStore()
const queueStore = useQueueStore()

const refreshing = ref(false)
const autoRefreshing = ref(false)
const apiToken = ref(getApiToken())
let timerId: number | null = null

const navItems = [
  { path: '/', label: '仪表盘', icon: LayoutDashboard },
  { path: '/tasks', label: '任务列表', icon: ListTodo },
  { path: '/tasks/submit', label: '提交任务', icon: Upload },
  { path: '/queue', label: '队列管理', icon: Settings },
]

const activeClass = 'bg-[#ececf1] text-[#202123]'
const inactiveClass = 'text-[#6e6e80] hover:text-[#202123] hover:bg-[#f4f4f5]'

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

function isActive(path: string) {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}

function shouldAutoRefresh() {
  return document.visibilityState === 'visible' && route.name !== 'task-detail'
}

async function refreshAll(options: { silent?: boolean } = {}) {
  const isSilent = options.silent ?? false
  if ((refreshing.value || autoRefreshing.value) || (isSilent && !shouldAutoRefresh())) {
    return
  }
  if (isSilent) {
    autoRefreshing.value = true
  } else {
    refreshing.value = true
  }
  try {
    await Promise.all([taskStore.loadDashboard(8), queueStore.fetchHealth()])
  } catch {
    // Errors are stored in Pinia stores and surfaced by pages.
  } finally {
    if (isSilent) {
      autoRefreshing.value = false
    } else {
      refreshing.value = false
    }
  }
}

function handleVisibilityChange() {
  if (document.visibilityState === 'visible') {
    refreshAll({ silent: true }).catch(() => {
      // ignore visibility refresh error
    })
  }
}

function saveToken() {
  setApiToken(apiToken.value)
  toast.success('Token 已保存')
  refreshAll().catch(() => {
    // ignore refresh error after token save
  })
}

function clearToken() {
  apiToken.value = ''
  setApiToken('')
  toast.info('Token 已清除')
}

onMounted(async () => {
  try {
    await refreshAll()
  } catch {
    // ignore initial refresh error
  }
  document.addEventListener('visibilitychange', handleVisibilityChange)
  timerId = window.setInterval(() => {
    refreshAll({ silent: true }).catch(() => {
      // ignore auto refresh error
    })
  }, 10000)
})

onUnmounted(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  if (timerId) {
    clearInterval(timerId)
    timerId = null
  }
})
</script>
