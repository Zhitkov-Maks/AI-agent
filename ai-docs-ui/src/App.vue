<template>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Docs Assistant</h1>
            <p>Интеллектуальный поиск и генерация документации</p>
        </div>

        <div class="main-grid">
            <SearchSection @show-message="showMessage" />
            <GenerateSection @show-message="showMessage" />
        </div>

        <TasksList 
            @show-message="showMessage"
            @show-result="showResultModal"
        />

        <HealthStatus />

        <!-- Modal -->
        <div v-if="modalVisible" class="modal" @click.self="modalVisible = false">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Результат генерации</h3>
                    <button class="modal-close" @click="modalVisible = false">&times;</button>
                </div>
                <div class="modal-body">
                    <pre style="white-space: pre-wrap; word-wrap: break-word;">{{ modalContent }}</pre>
                </div>
            </div>
        </div>

        <!-- Toast Notifications -->
        <div v-if="toastMessage" :class="['alert', toastClass]" style="position: fixed; bottom: 20px; right: 20px; max-width: 400px; z-index: 2000;">
            {{ toastMessage }}
        </div>
    </div>
</template>

<script>
import SearchSection from './components/SearchSection.vue'
import GenerateSection from './components/GenerateSection.vue'
import TasksList from './components/TasksList.vue'
import HealthStatus from './components/HealthStatus.vue'

export default {
    name: 'App',
    components: {
        SearchSection,
        GenerateSection,
        TasksList,
        HealthStatus
    },
    data() {
        return {
            modalVisible: false,
            modalContent: '',
            toastMessage: '',
            toastClass: '',
            toastTimeout: null
        }
    },
    methods: {
        showMessage(message, type) {
            if (this.toastTimeout) {
                clearTimeout(this.toastTimeout)
            }

            const classMap = {
                success: 'alert-success',
                error: 'alert-error',
                info: 'alert-info'
            }

            this.toastMessage = message
            this.toastClass = classMap[type] || 'alert-info'
            
            this.toastTimeout = setTimeout(() => {
                this.toastMessage = ''
            }, 5000)
        },
        showResultModal(content) {
            this.modalContent = content
            this.modalVisible = true
        }
    }
}
</script>
