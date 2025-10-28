# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Bağımlılıkları yükle
COPY package*.json ./
RUN npm ci

# Uygulamayı build et
COPY . .
# Increase Node.js memory limit for build
ENV NODE_OPTIONS="--max-old-space-size=2048"
RUN npm run build

# Production stage
FROM nginx:alpine

# Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Build dosyalarını kopyala
COPY --from=builder /app/dist /usr/share/nginx/html

# Port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

