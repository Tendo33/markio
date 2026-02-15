import axios, { AxiosError } from 'axios'

const apiClient = axios.create({
  baseURL: '',
  timeout: 180000,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    if (error.response?.data?.detail) {
      return Promise.reject(new Error(error.response.data.detail))
    }
    return Promise.reject(error)
  }
)

export default apiClient
