# Stage 1 — Build the React app
FROM node:20-alpine AS builder

WORKDIR /app

# Accept VITE_API_URL as build argument (defaults to empty for relative paths)
ARG VITE_API_URL=

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy source code and build
COPY . .
RUN VITE_API_URL=${VITE_API_URL} npm run build

# Stage 2 — Serve with nginx
FROM nginx:alpine

# Copy built files to nginx html directory
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]