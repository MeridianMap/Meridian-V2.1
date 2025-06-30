# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY . .
RUN npm ci && npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# Default nginx config is fine for static SPA
