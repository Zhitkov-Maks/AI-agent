# frontend/Dockerfile

# Stage 1: Build - используем Node.js 22
FROM node:22-alpine as build-stage

WORKDIR /app

# Копируем package files
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install --legacy-peer-deps

# Копируем исходники
COPY . .

# Собираем приложение
RUN npm run build

# Stage 2: Production
FROM nginx:stable-alpine

# Установка curl для healthcheck
RUN apk add --no-cache curl

# Копируем собранные ассеты
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Копируем конфигурацию nginx (ДОБАВЬТЕ ЭТУ СТРОКУ!)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Создаём простой healthcheck файл
RUN echo "healthy" > /usr/share/nginx/html/health

# Expose порт
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Запуск nginx
CMD ["nginx", "-g", "daemon off;"]