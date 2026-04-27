import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import {
  API_TOKEN_STORAGE_KEY,
  getApiToken,
  getApiTokenRole,
  getApiTokenStatus,
  hasApiToken,
  onApiTokenChange,
  setApiToken,
} from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(getApiToken())
  const role = ref(getApiTokenRole('user'))
  const status = ref(getApiTokenStatus())
  const configured = ref(hasApiToken())
  let stopTokenListener: (() => void) | null = null
  let storageListenerBound = false

  function refreshFromStorage() {
    token.value = getApiToken()
    role.value = getApiTokenRole('user')
    status.value = getApiTokenStatus()
    configured.value = hasApiToken()
  }

  function saveToken(nextToken: string) {
    setApiToken(nextToken)
    refreshFromStorage()
  }

  function clearToken() {
    saveToken('')
  }

  function bindListeners() {
    if (typeof window === 'undefined') {
      return
    }
    if (!stopTokenListener) {
      stopTokenListener = onApiTokenChange(refreshFromStorage)
    }
    if (!storageListenerBound) {
      window.addEventListener('storage', (event: StorageEvent) => {
        if (event.key === null || event.key === API_TOKEN_STORAGE_KEY) {
          refreshFromStorage()
        }
      })
      storageListenerBound = true
    }
  }

  bindListeners()

  return {
    token,
    role,
    status,
    configured,
    isAdmin: computed(() => role.value === 'admin'),
    refreshFromStorage,
    saveToken,
    clearToken,
  }
})
