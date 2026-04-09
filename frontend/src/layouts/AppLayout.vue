<template>
  <div class="min-h-screen bg-subtle">
    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-surface focus:px-3 focus:py-2 focus:text-sm focus:text-primary"
    >
      跳转到主要内容
    </a>

    <nav
      class="relative bg-white/90 backdrop-blur-md border-b border-subtle sticky top-0 z-40"
      aria-label="主导航"
    >
      <div class="w-full px-4 sm:px-6 lg:px-8 xl:px-12">
        <div class="flex flex-wrap lg:flex-nowrap justify-between items-center min-h-16 py-2 gap-3">
          <div class="flex items-center min-w-0 flex-1">
            <router-link to="/" class="flex items-center gap-3 group">
              <div class="h-9 w-9 rounded-xl text-white font-semibold text-xs tracking-wide flex items-center justify-center bg-[color:var(--text-primary)]">
                MK
              </div>
              <div>
                <div class="text-lg font-semibold text-primary">Markio Console</div>
                <div class="text-xs text-secondary">OpenAI 风格轻量任务控制台</div>
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
            <button
              class="inline-flex lg:hidden px-2 py-1.5 text-xs rounded-lg border border-default text-tertiary hover:bg-hover"
              type="button"
              @click="showMobileTokenPanel = !showMobileTokenPanel"
              :aria-expanded="showMobileTokenPanel ? 'true' : 'false'"
              aria-controls="mobile-token-panel"
            >
              {{ showMobileTokenPanel ? '收起 Token' : '配置 Token' }}
            </button>
            <div class="hidden lg:flex items-center gap-2">
              <input
                v-model="apiToken"
                type="password"
                class="w-52 px-2 py-1.5 text-xs rounded-lg border border-default bg-surface text-primary"
                placeholder="JWT Token"
                aria-label="API JWT Token"
                @keyup.enter="saveToken"
              />
              <button
                @click="saveToken"
                class="px-2 py-1.5 text-xs rounded-lg border border-default text-tertiary hover:bg-hover"
                aria-label="保存 API Token"
              >
                保存
              </button>
              <button
                @click="clearToken"
                class="px-2 py-1.5 text-xs rounded-lg border border-default text-tertiary hover:bg-hover"
                aria-label="清除 API Token"
              >
                清除
              </button>
            </div>
            <div class="hidden md:flex items-center gap-3 px-3 py-1.5 bg-subtle rounded-lg border border-subtle">
              <div class="flex items-center gap-1.5 text-xs">
                <div
                  class="w-2 h-2 rounded-full bg-[color:var(--status-warning-text)]"
                  :class="stats.processing > 0 ? 'animate-pulse' : ''"
                ></div>
                <span class="text-secondary">处理中</span>
                <span class="font-semibold text-warning">{{ stats.processing }}</span>
              </div>
              <div class="w-px h-3 bg-[color:var(--border-default)]"></div>
              <div class="flex items-center gap-1.5 text-xs">
                <div class="w-2 h-2 rounded-full bg-[color:var(--border-strong)]"></div>
                <span class="text-secondary">等待</span>
                <span class="font-semibold text-tertiary">{{ stats.pending }}</span>
              </div>
            </div>

            <button
              @click="refreshAll"
              :disabled="refreshing || autoRefreshing"
              aria-label="刷新仪表盘和队列状态"
              class="icon-btn text-secondary hover:text-primary-600 hover:bg-hover"
              title="刷新"
            >
              <RefreshCw :class="{ 'animate-spin': refreshing || autoRefreshing }" class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
      <div class="absolute inset-x-0 bottom-0 h-[2px] bg-[color:var(--accent)] opacity-50"></div>
    </nav>

    <section
      id="mobile-token-panel"
      v-if="showMobileTokenPanel"
      class="lg:hidden px-4 sm:px-6 py-3 border-b border-subtle bg-surface"
    >
      <div class="flex items-center gap-2">
        <input
          v-model="apiToken"
          type="password"
          class="flex-1 px-2 py-2 text-xs rounded-lg border border-default bg-surface text-primary"
          placeholder="JWT Token"
          aria-label="移动端 API JWT Token"
          @keyup.enter="saveToken"
        />
        <button
          @click="saveToken"
          class="px-2 py-2 text-xs rounded-lg border border-default text-tertiary hover:bg-hover"
          aria-label="保存移动端 API Token"
        >
          保存
        </button>
        <button
          @click="clearToken"
          class="px-2 py-2 text-xs rounded-lg border border-default text-tertiary hover:bg-hover"
          aria-label="清除移动端 API Token"
        >
          清除
        </button>
      </div>
    </section>

    <section
      v-if="!tokenConfigured"
      class="mx-4 mt-4 rounded-2xl border border-warning bg-warning p-4 text-sm text-warning sm:mx-6 lg:mx-8 xl:mx-12"
      role="status"
      aria-live="polite"
    >
      当前尚未配置 JWT Token，控制台不会主动请求 `/v1/*` 接口。请在顶部保存 Token 后再访问仪表盘、任务或队列能力。
    </section>

    <main id="main-content" class="w-full px-4 sm:px-6 lg:px-8 xl:px-12 py-4 lg:py-6">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute } from 'vue-router'
import { LayoutDashboard, ListTodo, RefreshCw, Settings, Upload } from 'lucide-vue-next'

import { useAuthStore, useQueueStore, useTaskStore } from '@/stores'
import { toast } from '@/utils/toast'

const route = useRoute()
const authStore = useAuthStore()
const taskStore = useTaskStore()
const queueStore = useQueueStore()
const { configured: tokenConfigured, isAdmin, role, token } = storeToRefs(authStore)

const refreshing = ref(false)
const autoRefreshing = ref(false)
const showMobileTokenPanel = ref(false)
const apiToken = ref(token.value)
let timerId: number | null = null
let autoRefreshDelayMs = 5000

const navItems = [
  { path: '/', label: '仪表盘', icon: LayoutDashboard },
  { path: '/tasks', label: '任务列表', icon: ListTodo },
  { path: '/tasks/submit', label: '提交任务', icon: Upload },
  { path: '/queue', label: '队列管理', icon: Settings },
]

const activeClass = 'bg-accent-soft text-accent-strong'
const inactiveClass = 'text-secondary hover:text-primary hover:bg-hover'
const currentRole = computed(() => role.value)

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
  return tokenConfigured.value && document.visibilityState === 'visible' && route.name !== 'task-detail'
}

function syncTokenContext() {
  authStore.refreshFromStorage()
  apiToken.value = token.value
}

async function refreshAll(options: { silent?: boolean } = {}) {
  const isSilent = options.silent ?? false
  if ((refreshing.value || autoRefreshing.value) || (isSilent && !shouldAutoRefresh())) {
    return true
  }
  if (!tokenConfigured.value) {
    taskStore.resetState()
    queueStore.reset()
    return true
  }
  if (isSilent) {
    autoRefreshing.value = true
  } else {
    refreshing.value = true
  }
  try {
    const operations: Array<Promise<unknown>> = [taskStore.loadDashboard(8)]
    if (isAdmin.value) {
      operations.push(queueStore.fetchHealth())
    } else {
      queueStore.reset()
    }
    await Promise.all(operations)
    return true
  } catch {
    // Errors are stored in Pinia stores and surfaced by pages.
    return false
  } finally {
    if (isSilent) {
      autoRefreshing.value = false
    } else {
      refreshing.value = false
    }
  }
}

function nextAutoRefreshDelay(hadError: boolean) {
  if (!shouldAutoRefresh()) {
    autoRefreshDelayMs = 30000
    return autoRefreshDelayMs
  }
  const activeTasks = Number(stats.value.pending) + Number(stats.value.processing)
  const baseline = activeTasks > 0 ? 5000 : 15000
  if (hadError) {
    autoRefreshDelayMs = Math.min(Math.max(baseline, autoRefreshDelayMs * 2), 60000)
  } else {
    autoRefreshDelayMs = baseline
  }
  return autoRefreshDelayMs
}

function scheduleAutoRefresh(hadError = false) {
  if (timerId) {
    clearTimeout(timerId)
  }
  const delay = nextAutoRefreshDelay(hadError)
  timerId = window.setTimeout(async () => {
    const ok = await refreshAll({ silent: true })
    scheduleAutoRefresh(!ok)
  }, delay)
}

function handleVisibilityChange() {
  if (document.visibilityState === 'visible') {
    refreshAll({ silent: true }).catch(() => {
      // ignore visibility refresh error
    })
    scheduleAutoRefresh()
  }
}

function saveToken() {
  authStore.saveToken(apiToken.value)
  syncTokenContext()
  toast.success('Token 已保存')
  refreshAll().catch(() => {
    // ignore refresh error after token save
  })
}

function clearToken() {
  apiToken.value = ''
  authStore.clearToken()
  syncTokenContext()
  taskStore.resetState()
  queueStore.reset()
  toast.info('Token 已清除')
}

onMounted(async () => {
  syncTokenContext()
  try {
    await refreshAll()
  } catch {
    // ignore initial refresh error
  }
  document.addEventListener('visibilitychange', handleVisibilityChange)
  scheduleAutoRefresh()
})

watch(
  token,
  () => {
    syncTokenContext()
  }
)

onUnmounted(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  if (timerId) {
    clearTimeout(timerId)
    timerId = null
  }
})
</script>
