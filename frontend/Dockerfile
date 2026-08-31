# ==============================================================================
# Stage 1: Build static assets with Node.js
# ==============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies using npm ci for deterministic builds
COPY package.json package-lock.json ./
RUN npm ci

# Vite build-time environment variable arguments
ARG VITE_API_BASE_URL
ARG VITE_USE_MOCK_API
ARG VITE_MAP_TILE_URL
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY

# Expose build args to environment for Vite bundle baking
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_USE_MOCK_API=$VITE_USE_MOCK_API \
    VITE_MAP_TILE_URL=$VITE_MAP_TILE_URL \
    VITE_SUPABASE_URL=$VITE_SUPABASE_URL \
    VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY

# Copy source code and build production bundle
COPY . .
RUN npm run build

# ==============================================================================
# Stage 2: Serve static assets with Nginx
# ==============================================================================
FROM nginx:1.27-alpine AS runner

# Remove default nginx static assets and config
RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/default.conf

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/health || exit 1

CMD ["nginx", "-g", "daemon off;"]

