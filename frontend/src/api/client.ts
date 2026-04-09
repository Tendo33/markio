import axios, { AxiosError } from 'axios'

const envBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim()
const envApiToken = (import.meta.env.VITE_API_TOKEN as string | undefined)?.trim() ?? ''
export const API_TOKEN_STORAGE_KEY = 'markio_api_token'
const TOKEN_CHANGE_EVENT = 'markio:token-change'

function resolveStoredToken(): string {
  if (typeof window === 'undefined') {
    return envApiToken
  }
  const persistedToken = window.localStorage.getItem(API_TOKEN_STORAGE_KEY)?.trim() ?? ''
  return persistedToken || envApiToken
}

export function setApiToken(token: string) {
  if (typeof window === 'undefined') return
  const normalized = token.trim()
  if (normalized) {
    window.localStorage.setItem(API_TOKEN_STORAGE_KEY, normalized)
  } else {
    window.localStorage.removeItem(API_TOKEN_STORAGE_KEY)
  }
  window.dispatchEvent(new Event(TOKEN_CHANGE_EVENT))
}

export function getApiToken(): string {
  return resolveStoredToken()
}

export function hasApiToken(): boolean {
  return resolveStoredToken().length > 0
}

function decodeBase64Url(input: string): string | null {
  if (!input) return null
  const normalized = input.replace(/-/g, '+').replace(/_/g, '/')
  const padded = normalized + '='.repeat((4 - (normalized.length % 4)) % 4)
  try {
    if (typeof window !== 'undefined' && typeof window.atob === 'function') {
      return window.atob(padded)
    }
  } catch {
    return null
  }
  return null
}

export function getApiTokenRole(defaultRole: string = 'user'): string {
  const token = resolveStoredToken()
  if (!token) return defaultRole
  const [, payloadSegment] = token.split('.')
  if (!payloadSegment) return defaultRole
  const payloadRaw = decodeBase64Url(payloadSegment)
  if (!payloadRaw) return defaultRole
  try {
    const payload = JSON.parse(payloadRaw) as { role?: unknown }
    if (typeof payload.role === 'string' && payload.role.trim()) {
      return payload.role.trim().toLowerCase()
    }
  } catch {
    return defaultRole
  }
  return defaultRole
}

export function onApiTokenChange(handler: () => void): () => void {
  if (typeof window === 'undefined') {
    return () => {}
  }
  window.addEventListener(TOKEN_CHANGE_EVENT, handler)
  return () => {
    window.removeEventListener(TOKEN_CHANGE_EVENT, handler)
  }
}

const apiClient = axios.create({
  baseURL: envBaseUrl && envBaseUrl.length > 0 ? envBaseUrl : '',
  timeout: 180000,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const token = resolveStoredToken()
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

type ApiErrorPayload = {
  detail?: string
  error?: {
    message?: string
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorPayload>) => {
    const message =
      error.response?.data?.error?.message ||
      error.response?.data?.detail ||
      error.message
    if (message) {
      return Promise.reject(new Error(message))
    }
    return Promise.reject(error)
  }
)

export default apiClient
