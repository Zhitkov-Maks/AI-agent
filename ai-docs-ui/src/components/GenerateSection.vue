<template>
    <div class="card">
        <h2>✨ Генерация документации</h2>
        <div class="search-box">
            <input 
                type="text" 
                v-model="query" 
                placeholder="Опишите, какую документацию нужно создать..."
                @keyup.enter="handleGenerate"
                :disabled="loading"
            >
            <button class="btn btn-success" @click="handleGenerate" :disabled="loading">
                <span v-if="loading" class="spinner"></span>
                <span v-else>🚀 Сгенерировать</span>
            </button>
        </div>
        <div v-if="message" :class="['alert', messageClass]">
            {{ message }}
        </div>
    </div>
</template>

<script>
import { api } from '../services/api'
import { useTasksStore } from '../stores/tasks'

export default {
    name: 'GenerateSection',
    data() {
        return {
            query: '',
            loading: false,
            message: '',
            messageClass: ''
        }
    },
    methods: {
        async handleGenerate() {
            if (!this.query.trim()) {
                this.showMessage('Введите описание документации', 'alert-error')
                return
            }
            
            this.loading = true
            try {
                const response = await api.generate(this.query)
                
                if (response.success) {
                    this.showMessage(response.message, 'alert-success')
                    const tasksStore = useTasksStore()
                    tasksStore.addTask(response.task_id)
                    tasksStore.refreshTasks()
                    this.query = ''
                } else {
                    this.showMessage(response.message, 'alert-error')
                }
            } catch (error) {
                console.error('Generate error:', error)
                this.showMessage('Ошибка при генерации', 'alert-error')
            } finally {
                this.loading = false
                setTimeout(() => {
                    this.message = ''
                }, 5000)
            }
        },
        showMessage(message, messageClass) {
            this.message = message
            this.messageClass = messageClass
        }
    }
}
</script>