import { defineStore } from 'pinia'
import { api } from '../services/api'

export const useTasksStore = defineStore('tasks', {
    state: () => ({
        tasks: [],
        autoRefresh: false,
        refreshInterval: null
    }),

    actions: {
        addTask(taskId, status = 'pending') {
            if (!this.tasks.find(t => t.task_id === taskId)) {
                this.tasks.push({
                    task_id: taskId,
                    status: status,
                    result: null,
                    error: null
                })
            }
        },

        async refreshTasks() {
            const updatedTasks = []
            for (const task of this.tasks) {
                try {
                    const taskData = await api.getTaskStatus(task.task_id)
                    updatedTasks.push({
                        task_id: task.task_id,
                        status: taskData.status.toLowerCase(),
                        result: taskData.result,
                        error: taskData.error
                    })
                } catch (error) {
                    console.error(`Error fetching task ${task.task_id}:`, error)
                    updatedTasks.push(task)
                }
            }
            
            this.tasks = updatedTasks.filter(t => 
                t.status === 'pending' || 
                t.status === 'processing' || 
                t.status === 'started'
            )
        },

        removeTask(taskId) {
            this.tasks = this.tasks.filter(t => t.task_id !== taskId)
        },

        async abortTask(taskId) {
            await api.abortTask(taskId)
            await this.refreshTasks()
        },

        startAutoRefresh() {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval)
            }
            this.refreshInterval = setInterval(() => {
                this.refreshTasks()
            }, 3000)
            this.autoRefresh = true
        },

        stopAutoRefresh() {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval)
                this.refreshInterval = null
            }
            this.autoRefresh = false
        },

        toggleAutoRefresh() {
            if (this.autoRefresh) {
                this.stopAutoRefresh()
            } else {
                this.startAutoRefresh()
            }
        }
    }
})