<template>
    <div class="card">
        <h2>🔍 Поиск документации</h2>
        <div class="search-box">
            <input 
                type="text" 
                v-model="query" 
                placeholder="Введите запрос для поиска..."
                @keyup.enter="handleSearch"
                :disabled="loading"
            >
            <button class="btn btn-primary" @click="handleSearch" :disabled="loading">
                <span v-if="loading" class="spinner"></span>
                <span v-else>🔍 Найти</span>
            </button>
        </div>
        <div class="result-area">
            <div v-if="result.found" class="result-content">
                <strong>📄 Результат поиска:</strong>
                <div style="margin-top: 10px;">{{ result.content }}</div>
            </div>
            <div v-else-if="result.message" class="empty-state">
                {{ result.message }}
            </div>
            <div v-else class="empty-state">
                💡 Введите запрос для поиска в документации
            </div>
        </div>
    </div>
</template>

<script>
import { api } from '../services/api'

export default {
    name: 'SearchSection',
    data() {
        return {
            query: '',
            loading: false,
            result: { found: false, content: null, message: null }
        }
    },
    methods: {
        async handleSearch() {
            if (!this.query.trim()) {
                this.showMessage('Введите запрос для поиска', 'error')
                return
            }
            
            this.loading = true
            try {
                const response = await api.search(this.query)
                this.result = response
                if (!response.found) {
                    this.$emit('show-message', response.message || 'Ничего не найдено', 'info')
                }
            } catch (error) {
                console.error('Search error:', error)
                this.result = {
                    found: false,
                    message: 'Ошибка при поиске. Проверьте соединение с сервером.'
                }
                this.$emit('show-message', this.result.message, 'error')
            } finally {
                this.loading = false
            }
        },
        showMessage(message, type) {
            this.$emit('show-message', message, type)
        }
    }
}
</script>