import axios from 'axios'

// Для разработки используйте полный URL бэкенда
const API_BASE_URL = import.meta.env.DEV 
  ? 'http://localhost:8000'  // Прямой URL для разработки
  : '/api'  // Через прокси для production

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json'
    },
    timeout: 30000  // Добавьте таймаут
})

// Добавьте интерцептор для обработки ошибок
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.code === 'ECONNREFUSED') {
      console.error('❌ Cannot connect to backend server. Make sure it\'s running on port 8000')
      // Можно показать уведомление пользователю
    }
    return Promise.reject(error)
  }
)

export const api = {
    async search(query) {
        const response = await apiClient.post('/search', { query })
        return response.data
    },

    async generate(query) {
        const response = await apiClient.post('/generate', { query })
        return response.data
    },

    async getTaskStatus(taskId) {
        const response = await apiClient.get(`/task/${taskId}`)
        return response.data
    },

    async abortTask(taskId) {
        const response = await apiClient.delete(`/task/${taskId}`)
        return response.data
    },

    async healthCheck() {
        try {
            const response = await apiClient.get('/health')
            return response.data
        } catch (error) {
            console.error('Health check failed:', error.message)
            return {
                status: 'unhealthy',
                error: 'Backend not reachable',
                services: {},
                data: {}
            }
        }
    }
}