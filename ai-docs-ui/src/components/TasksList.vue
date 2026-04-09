<template>
    <div class="card">
        <h2>📋 Активные задачи</h2>
        <div class="auto-refresh">
            <label>
                <input type="checkbox" v-model="tasksStore.autoRefresh" @change="toggleAutoRefresh">
                Автообновление (каждые 3 сек)
            </label>
            <button class="btn btn-secondary" @click="refreshTasks" style="margin-left: auto;">
                🔄 Обновить
            </button>
        </div>
        
        <div v-if="tasksStore.tasks.length === 0" class="empty-state">
            Нет активных задач
        </div>
        <table v-else class="tasks-table">
            <thead>
                <tr>
                    <th>ID задачи</th>
                    <th>Статус</th>
                    <th>Результат</th>
                    <th>Действия</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="task in tasksStore.tasks" :key="task.task_id">
                    <td style="font-family: monospace; font-size: 12px;">
                        {{ task.task_id.substring(0, 8) }}...
                    </td>
                    <td>
                        <span :class="['task-status', getStatusClass(task.status)]">
                            {{ getStatusText(task.status) }}
                        </span>
                    </td>
                    <td>
                        <div v-if="task.result">
                            <span v-if="task.result.file_path">
                                📄 {{ task.result.file_path.split('/').pop() }}
                            </span>
                            <span v-else-if="task.result.content">
                                {{ task.result.content.substring(0, 50) }}...
                            </span>
                        </div>
                        <div v-else-if="task.error" style="color: #f56565;">
                            ❌ {{ task.error }}
                        </div>
                        <div v-else>-</div>
                    </td>
                    <td class="task-actions">
                        <button 
                            v-if="task.status === 'pending' || task.status === 'processing'"
                            class="icon-btn" 
                            @click="handleAbortTask(task.task_id)"
                            title="Отменить задачу"
                        >
                            🛑
                        </button>
                        <button 
                            v-if="task.result && task.result.content"
                            class="icon-btn" 
                            @click="showResult(task.result.content)"
                            title="Показать результат"
                        >
                            👁️
                        </button>
                        <button 
                            class="icon-btn" 
                            @click="tasksStore.removeTask(task.task_id)"
                            title="Удалить из списка"
                        >
                            🗑️
                        </button>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>

<script>
import { useTasksStore } from '../stores/tasks'
import { api } from '../services/api'

export default {
    name: 'TasksList',
    data() {
        return {
            tasksStore: useTasksStore()
        }
    },
    mounted() {
        this.tasksStore.refreshTasks()
    },
    beforeUnmount() {
        if (this.tasksStore.autoRefresh) {
            this.tasksStore.stopAutoRefresh()
        }
    },
    methods: {
        async refreshTasks() {
            await this.tasksStore.refreshTasks()
        },
        async handleAbortTask(taskId) {
            try {
                await this.tasksStore.abortTask(taskId)
                this.$emit('show-message', `Задача ${taskId.substring(0, 8)} отменена`, 'success')
            } catch (error) {
                console.error('Error aborting task:', error)
                this.$emit('show-message', 'Ошибка при отмене задачи', 'error')
            }
        },
        showResult(content) {
            this.$emit('show-result', content)
        },
        toggleAutoRefresh() {
            this.tasksStore.toggleAutoRefresh()
        },
        getStatusClass(status) {
            const classes = {
                'pending': 'status-pending',
                'processing': 'status-processing',
                'started': 'status-processing',
                'success': 'status-success',
                'failure': 'status-failure'
            }
            return classes[status] || 'status-pending'
        },
        getStatusText(status) {
            const texts = {
                'pending': '⏳ Ожидание',
                'processing': '🔄 Обработка',
                'started': '🔄 Обработка',
                'success': '✅ Выполнено',
                'failure': '❌ Ошибка'
            }
            return texts[status] || status
        }
    }
}
</script>