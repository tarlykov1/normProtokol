FROM node:20-alpine AS builder
WORKDIR /app

COPY frontend/package*.json /app/
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY frontend /app

ARG VITE_API_BASE_URL=http://127.0.0.1:18000/api
ARG VITE_USE_MOCK_API=false
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_USE_MOCK_API=${VITE_USE_MOCK_API}

RUN npm run build

FROM nginx:1.27-alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
