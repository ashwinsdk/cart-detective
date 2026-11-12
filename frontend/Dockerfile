FROM node:20-slim AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . ./
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 5173

# Configure Nginx for Vite SPA routing
RUN sed -i 's/listen       80;/listen       5173;/' /etc/nginx/conf.d/default.conf && \
    sed -i '/location \/ {/a try_files $uri $uri/ /index.html;' /etc/nginx/conf.d/default.conf

CMD ["nginx", "-g", "daemon off;"]
