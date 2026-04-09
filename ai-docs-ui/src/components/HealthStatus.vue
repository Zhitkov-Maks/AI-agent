<template>
    <div class="health-status">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3 style="color: #333;">🏥 Health Check</h3>
            <button class="btn btn-secondary" @click="checkHealth" style="padding: 8px 16px;">
                🔄 Проверить
            </button>
        </div>
        <div class="health-grid" v-if="healthStatus">
            <div class="health-item">
                <strong>Общий статус</strong>
                <div :class="healthStatus.status === 'healthy' ? 'health-ok' : 'health-error'">
                    {{ healthStatus.status === 'healthy' ? '✅ Здоров' : '❌ Проблемы' }}
                </div>
            </div>
            <div class="health-item">
                <strong>Qdrant</strong>
                <div :class="healthStatus.checks?.qdrant ? 'health-ok' : 'health-error'">
                    {{ healthStatus.checks?.qdrant ? '✅ Работает' : '❌ Ошибка' }}
                </div>
            </div>
            <div class="health-item">
                <strong>Ollama</strong>
                <div :class="healthStatus.checks?.ollama ? 'health-ok' : 'health-error'">
                    {{ healthStatus.checks?.ollama ? '✅ Работает' : '❌ Ошибка' }}
                </div>
            </div>
            <div class="health-item">
                <strong>Документация</strong>
                <div :class="healthStatus.checks?.docs ? 'health-ok' : 'health-error'">
                    {{ healthStatus.checks?.docs ? '✅ Доступна' : '❌ Отсутствует' }}
                </div>
            </div>
            <div class="health-item">
                <strong>RAG Canary</strong>
                <div :class="healthStatus.checks?.rag_canary ? 'health-ok' : 'health-error'">
                    {{ healthStatus.checks?.rag_canary ? '✅ Работает' : '❌ Ошибка' }}
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { api } from '../services/api'

export default {
    name: 'HealthStatus',
    data() {
        return {
            healthStatus: null,
            intervalId: null
        }
    },
    mounted() {
        this.checkHealth()
        // Проверяем здоровье каждые 30 секунд
        this.intervalId = setInterval(() => this.checkHealth(), 30000)
    },
    beforeUnmount() {
        // Очищаем интервал при уничтожении компонента
        if (this.intervalId) {
            clearInterval(this.intervalId)
        }
    },
    methods: {
        async checkHealth() {
            try {
                this.healthStatus = await api.healthCheck()
                console.log('Health status:', this.healthStatus)
                
                // Если общий статус unhealthy, показываем уведомление
                if (this.healthStatus.status === 'unhealthy') {
                    this.$emit('show-message', '⚠️ Некоторые сервисы недоступны!', 'error')
                }
            } catch (error) {
                console.error('Health check error:', error)
                this.healthStatus = {
                    status: 'unhealthy',
                    checks: {
                        qdrant: false,
                        ollama: false,
                        docs: false,
                        rag_canary: false
                    }
                }
            }
        }
    }
}
</script>