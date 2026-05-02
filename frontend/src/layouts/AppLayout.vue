<template>
  <div class="min-h-screen bg-subtle">
    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-surface focus:px-3 focus:py-2 focus:text-sm focus:text-primary"
    >
      跳转到主要内容
    </a>

    <nav
      class="sticky top-0 z-40 border-b border-subtle bg-surface"
      aria-label="主导航"
    >
      <div class="w-full px-4 sm:px-6 lg:px-8 xl:px-12">
        <div class="flex flex-wrap items-center justify-between gap-3 py-3 lg:flex-nowrap">
          <div class="flex items-center min-w-0 flex-1">
            <router-link to="/" class="flex items-center gap-3 group">
              <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[color:var(--text-primary)] text-inverse text-xs font-semibold tracking-wide">
                MK
              </div>
              <div>
                <div class="text-lg font-semibold text-primary">Markio Console</div>
                <div class="text-xs text-secondary">提交、追踪与管理文档解析任务</div>
              </div>
            </router-link>
          </div>

          <div class="order-3 flex w-full flex-wrap items-center gap-2 lg:order-none lg:w-auto lg:flex-1 lg:justify-center">
            <router-link
              v-for="item in navItems"
              :key="item.path"
              :to="item.path"
              :class="isActive(item.path) ? activeClass : inactiveClass"
              class="nav-link"
            >
              <component :is="item.icon" class="h-4 w-4" />
              {{ item.label }}
            </router-link>
          </div>

          <div class="flex items-center gap-2">
            <button
              class="btn btn-secondary text-xs lg:hidden"
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
                class="min-h-[44px] w-56 rounded-xl border border-default bg-surface px-3 py-2.5 text-sm text-primary xl:w-64"
                placeholder="输入 JWT Token"
                aria-label="API JWT Token"
                @keyup.enter="saveToken"
              />
              <button
                @click="saveToken"
                class="btn btn-secondary text-xs"
                aria-label="保存 API Token"
              >
                保存
              </button>
              <button
                @click="clearToken"
                class="btn btn-secondary text-xs"
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
              class="icon-btn text-secondary hover:bg-hover hover:text-primary"
              title="刷新"
            >
              <RefreshCw :class="{ 'animate-spin': refreshing || autoRefreshing }" class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </nav>

    <section
      id="mobile-token-panel"
      v-if="showMobileTokenPanel"
      class="border-b border-subtle bg-surface px-4 py-3 sm:px-6 lg:hidden"
    >
      <div class="grid grid-cols-1 gap-2 sm:grid-cols-[minmax(0,1fr)_auto_auto]">
        <input
          v-model="apiToken"
          type="password"
          class="min-h-[44px] rounded-xl border border-default bg-surface px-3 py-2.5 text-sm text-primary"
          placeholder="输入 JWT Token"
          aria-label="移动端 API JWT Token"
          @keyup.enter="saveToken"
        />
        <button
          @click="saveToken"
          class="btn btn-secondary text-xs"
          aria-label="保存移动端 API Token"
        >
          保存
        </button>
        <button
          @click="clearToken"
          class="btn btn-secondary text-xs"
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
      {{ tokenBannerMessage }}
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
const { configured: tokenConfigured, isAdmin, role, status, token } = storeToRefs(authStore)

const refreshing = ref(false)
const autoRefreshing = ref(false)
const showMobileTokenPanel = ref(false)
const apiToken = ref(token.value)
let timerId: number | null = null
let autoRefreshDelayMs = 5000

const navItems = computed(() => {
  const items = [
    { path: '/', label: '仪表盘', icon: LayoutDashboard },
    { path: '/tasks', label: '任务列表', icon: ListTodo },
    { path: '/tasks/submit', label: '提交任务', icon: Upload },
  ]
  if (isAdmin.value) {
    items.push({ path: '/queue', label: '队列管理', icon: Settings })
  }
  return items
})

const activeClass = 'nav-link-active'
const inactiveClass = 'nav-link-inactive'
const currentRole = computed(() => role.value)
const tokenBannerMessage = computed(() => {
  if (status.value === 'expired') {
    return '当前 JWT Token 已过期。先在顶部更新 Token，再查看任务、提交文件或管理队列。'
  }
  if (status.value === 'invalid') {
    return '当前 JWT Token 无效。先在顶部更新 Token，再查看任务、提交文件或管理队列。'
  }
  return '还没有可用的 JWT Token。先在顶部保存 Token，再查看任务、提交文件或管理队列。'
})

const stats = computed(() => {
  return (
    taskStore.dashboard?.stats ?? {
      pending: 0,
      processing: 0,
      completed: 0,
      failed: 0,
      canceled: 0,
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
    timerId = null
  }
  if (!shouldAutoRefresh()) {
    return
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
    return
  }
  if (timerId) {
    clearTimeout(timerId)
    timerId = null
  }
}

function saveToken() {
  authStore.saveToken(apiToken.value)
  syncTokenContext()
  toast.success('Token 已保存')
  refreshAll().catch(() => {
    // ignore refresh error after token save
  })
  scheduleAutoRefresh()
}

function clearToken() {
  apiToken.value = ''
  authStore.clearToken()
  syncTokenContext()
  taskStore.resetState()
  queueStore.reset()
  if (timerId) {
    clearTimeout(timerId)
    timerId = null
  }
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

watch(
  [tokenConfigured, () => route.name, () => stats.value.pending, () => stats.value.processing],
  () => {
    scheduleAutoRefresh()
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
