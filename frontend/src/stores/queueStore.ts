import { defineStore } from 'pinia'
import { ref } from 'vue'

import { queueApi } from '@/api'
import type { QueueHealth } from '@/api/types'

const DEFAULT_HEALTH: QueueHealth = {
  queued: 0,
  processing: 0,
  workers: 0,
  paused: false,
}

export const useQueueStore = defineStore('queue', () => {
  const health = ref<QueueHealth>({ ...DEFAULT_HEALTH })
  const loading = ref(false)

  async function fetchHealth() {
    loading.value = true
    try {
      health.value = await queueApi.getQueueHealth()
      return health.value
    } catch (err: any) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function pause() {
    const result = await queueApi.pauseQueue()
    health.value.paused = result.paused
    return result
  }

  async function resume() {
    const result = await queueApi.resumeQueue()
    health.value.paused = result.paused
    return result
  }

  function reset() {
    health.value = { ...DEFAULT_HEALTH }
  }

  return {
    health,
    loading,
    fetchHealth,
    pause,
    resume,
    reset,
  }
})
