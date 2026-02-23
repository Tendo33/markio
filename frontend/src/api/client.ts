import axios, { AxiosError } from 'axios'

const envBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim()

const apiClient = axios.create({
  baseURL: envBaseUrl && envBaseUrl.length > 0 ? envBaseUrl : '',
  timeout: 180000,
  headers: {
    'Content-Type': 'application/json',
  },
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
