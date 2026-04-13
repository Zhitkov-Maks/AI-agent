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
                <div 
                    class="markdown-content" 
                    v-html="renderedContent"
                ></div>
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
            result: { found: false, content: null, message: null },
            markedLoaded: false
        }
    },
    computed: {
        renderedContent() {
            if (!this.result.content) return ''
            
            // Используем наш кастомный рендерер для API документации
            return this.renderApiDoc(this.result.content)
        }
    },
    mounted() {
        // Можно загрузить marked для подсветки синтаксиса, но не обязательно
        this.loadMarked()
    },
    methods: {
        loadMarked() {
            if (window.marked) {
                this.markedLoaded = true
                return
            }
            
            const script = document.createElement('script')
            script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js'
            script.onload = () => {
                this.markedLoaded = true
            }
            document.head.appendChild(script)
        },
        
        renderApiDoc(content) {
            if (!content) return ''
            
            let html = ''
            
            // Разделяем на эндпоинты (начинаются с ### или ####)
            const endpoints = content.split(/(?=###+ )/g)
            
            for (const endpoint of endpoints) {
                if (!endpoint.trim()) continue
                
                html += '<div class="api-endpoint">'
                
                // Извлекаем заголовок (### POST /api/v1/tasks)
                const titleMatch = endpoint.match(/^#+\s+(.+)$/m)
                if (titleMatch) {
                    const title = titleMatch[1]
                    // Определяем метод HTTP
                    const methodMatch = title.match(/^(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)/i)
                    const method = methodMatch ? methodMatch[1].toUpperCase() : ''
                    
                    let methodClass = 'method-default'
                    if (method === 'GET') methodClass = 'method-get'
                    else if (method === 'POST') methodClass = 'method-post'
                    else if (method === 'PUT') methodClass = 'method-put'
                    else if (method === 'DELETE') methodClass = 'method-delete'
                    else if (method === 'PATCH') methodClass = 'method-patch'
                    
                    html += `<div class="endpoint-title">`
                    if (method) {
                        html += `<span class="http-method ${methodClass}">${method}</span>`
                    }
                    html += `<span class="endpoint-path">${title}</span>`
                    html += `</div>`
                }
                
                // Извлекаем описание
                const descMatch = endpoint.match(/\*\*Описание\*\*:\s*(.+?)(?=\n\*\*|```|$)/s)
                if (descMatch) {
                    html += `<div class="endpoint-description">${descMatch[1].trim()}</div>`
                }
                
                // Извлекаем параметры
                const paramsMatch = endpoint.match(/\*\*Параметры[^:]*\*\*:\s*(.+?)(?=\n\*\*|```|$)/s)
                if (paramsMatch) {
                    let params = paramsMatch[1].trim()
                    
                    // Обработка разных форматов параметров
                    if (params.includes('`')) {
                        // Формат: `title` (строка), `description` (строка)
                        html += '<div class="endpoint-params">'
                        html += '<strong>Параметры:</strong> '
                        const paramItems = params.split(',').map(p => {
                            const match = p.match(/`([^`]+)`\s*\(?([^)]*)\)?/)
                            if (match) {
                                return `<code>${match[1]}</code> <span class="param-type">${match[2] || ''}</span>`
                            }
                            return p
                        })
                        html += paramItems.join(', ')
                        html += '</div>'
                    } else if (params.includes('-')) {
                        // Формат списка: - `id` (integer): описание
                        html += '<div class="endpoint-params"><strong>Параметры:</strong><ul>'
                        const lines = params.split('\n')
                        for (const line of lines) {
                            const match = line.match(/[-*]\s+`([^`]+)`\s*\(?([^):]*)\)?:?\s*(.*)/)
                            if (match) {
                                html += `<li><code>${match[1]}</code>`
                                if (match[2]) {
                                    html += ` <span class="param-type">(${match[2]})</span>`
                                }
                                if (match[3]) {
                                    html += ` - ${match[3]}`
                                }
                                html += '</li>'
                            }
                        }
                        html += '</ul></div>'
                    } else {
                        html += `<div class="endpoint-params"><strong>Параметры:</strong> ${params}</div>`
                    }
                }
                
                // Извлекаем параметры пути
                const pathParamsMatch = endpoint.match(/\*\*Параметры пути\*\*:\s*(.+?)(?=\n\*\*|```|$)/s)
                if (pathParamsMatch) {
                    let params = pathParamsMatch[1].trim()
                    html += '<div class="endpoint-params"><strong>Параметры пути:</strong><ul>'
                    const lines = params.split('\n')
                    for (const line of lines) {
                        const match = line.match(/[-*]\s+`([^`]+)`\s*\(?([^):]*)\)?:?\s*(.*)/)
                        if (match) {
                            html += `<li><code>${match[1]}</code>`
                            if (match[2]) {
                                html += ` <span class="param-type">(${match[2]})</span>`
                            }
                            if (match[3]) {
                                html += ` - ${match[3]}`
                            }
                            html += '</li>'
                        }
                    }
                    html += '</ul></div>'
                }
                
                // Извлекаем ответ
                const responseMatch = endpoint.match(/\*\*Ответ[^:]*\*\*:\s*(.+?)(?=\n###|$)/s)
                if (responseMatch) {
                    let response = responseMatch[1].trim()
                    
                    // Проверяем, есть ли JSON блок
                    const jsonMatch = response.match(/```json\s*([\s\S]*?)```/)
                    if (jsonMatch) {
                        try {
                            const jsonObj = JSON.parse(jsonMatch[1])
                            const formattedJson = JSON.stringify(jsonObj, null, 2)
                            html += '<div class="endpoint-response">'
                            html += '<strong>Ответ:</strong>'
                            html += `<pre class="json-response"><code>${this.escapeHtml(formattedJson)}</code></pre>`
                            html += '</div>'
                        } catch (e) {
                            html += `<div class="endpoint-response"><strong>Ответ:</strong><pre><code>${this.escapeHtml(jsonMatch[1])}</code></pre></div>`
                        }
                    } else {
                        html += `<div class="endpoint-response"><strong>Ответ:</strong> ${this.escapeHtml(response)}</div>`
                    }
                }
                
                html += '</div>'
            }
            
            return html
        },
        
        escapeHtml(text) {
            if (!text) return ''
            return text
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
        },
        
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
