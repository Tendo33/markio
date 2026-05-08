import axios, { AxiosError } from 'axios'

const envBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim()
const envApiToken = (import.meta.env.VITE_API_TOKEN as string | undefined)?.trim() ?? ''
export const API_TOKEN_STORAGE_KEY = 'markio_api_token'
const TOKEN_CHANGE_EVENT = 'markio:token-change'

// Keep browser token storage access centralized in this module so the
// console's credential surface stays narrow and auditable.

export type ApiTokenStatus = 'missing' | 'invalid' | 'expired' | 'valid'

function readStoredToken(): string {
  if (typeof window === 'undefined') {
    return envApiToken
  }
  const persistedToken = window.localStorage.getItem(API_TOKEN_STORAGE_KEY)?.trim() ?? ''
  return persistedToken || envApiToken
}

type JwtPayload = {
  exp?: unknown
  role?: unknown
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
  return readStoredToken()
}

function hasJwtShape(token: string): boolean {
  const segments = token.split('.')
  return segments.length === 3 && segments.every((segment) => segment.length > 0)
}

function decodeBase64Url(input: string): string | null {
  if (!input) return null
  const normalized = input.replace(/-/g, '+').replace(/_/g, '/')
  const padded = normalized + '='.repeat((4 - (normalized.length % 4)) % 4)
  try {
    const atobFn =
      typeof window !== 'undefined' && typeof window.atob === 'function'
        ? window.atob.bind(window)
        : typeof atob === 'function'
          ? atob
          : null
    if (!atobFn) {
      return null
    }
    const binary = atobFn(padded)
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0))
    return new TextDecoder().decode(bytes)
  } catch {
    return null
  }
}

function parseTokenPayload(token: string): JwtPayload | null {
  if (!hasJwtShape(token)) return null
  const [, payloadSegment] = token.split('.')
  if (!payloadSegment) return null
  const payloadRaw = decodeBase64Url(payloadSegment)
  if (!payloadRaw) return null
  try {
    return JSON.parse(payloadRaw) as JwtPayload
  } catch {
    return null
  }
}

function classifyToken(token: string): ApiTokenStatus {
  if (!token) return 'missing'
  if (!hasJwtShape(token)) return 'invalid'
  const payload = parseTokenPayload(token)
  if (!payload) return 'invalid'
  if (typeof payload.exp !== 'number' || !Number.isFinite(payload.exp)) {
    return 'invalid'
  }
  if (Date.now() >= payload.exp * 1000) {
    return 'expired'
  }
  return 'valid'
}

function resolveUsableToken(): string {
  const storedToken = readStoredToken()
  return classifyToken(storedToken) === 'valid' ? storedToken : ''
}

export function getApiTokenStatus(): ApiTokenStatus {
  return classifyToken(readStoredToken())
}

export function hasApiToken(): boolean {
  return resolveUsableToken().length > 0
}

export function getApiTokenRole(defaultRole: string = 'user'): string {
  const token = resolveUsableToken()
  if (!token) return defaultRole
  const payload = parseTokenPayload(token)
  if (payload && typeof payload.role === 'string' && payload.role.trim()) {
    return payload.role.trim().toLowerCase() === 'admin' ? 'admin' : defaultRole
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
  const token = resolveUsableToken()
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
