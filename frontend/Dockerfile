# =============================================================================
# Frontend Dockerfile - Multi-stage Node 20
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM node:20-alpine AS builder

LABEL maintainer="Lithology AI Team <team@lithology.ai>"
LABEL description="Automated Lithology Classification System - Frontend Builder"

# Build arguments
ARG VITE_API_BASE_URL=/api/v1
ARG VITE_APP_NAME="Lithology AI"
ARG VITE_APP_VERSION=1.0.0
ARG BUILDKIT_INLINE_CACHE=1

# Set environment variables for build
ENV NODE_ENV=production \
    VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_APP_NAME=${VITE_APP_NAME} \
    VITE_APP_VERSION=${VITE_APP_VERSION}

# Install build dependencies
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++

# Set working directory
WORKDIR /build

# Copy package files first for better layer caching
COPY package.json package-lock.json* ./

# Install dependencies (use ci for reproducible installs)
RUN npm ci --prefer-offline --no-audit

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Verify build output
RUN ls -la /build/dist/

# -----------------------------------------------------------------------------
# Stage 2: Production Nginx Server
# -----------------------------------------------------------------------------
FROM nginx:1.25-alpine AS production

LABEL maintainer="Lithology AI Team <team@lithology.ai>"
LABEL description="Automated Lithology Classification System - Frontend Production"
LABEL version="1.0.0"

# Install curl for healthcheck
RUN apk add --no-cache curl

# Remove default nginx configuration
RUN rm -rf /etc/nginx/conf.d/default.conf \
    && rm -rf /usr/share/nginx/html/*

# Copy custom nginx configuration for SPA routing
COPY --from=builder /build/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built static files from builder stage
COPY --from=builder /build/dist /usr/share/nginx/html

# Create nginx cache directory with proper permissions
RUN mkdir -p /var/cache/nginx \
             /var/log/nginx \
             /var/run \
    && chown -R nginx:nginx /var/cache/nginx \
                            /var/log/nginx \
                            /usr/share/nginx/html \
    && chmod -R 755 /usr/share/nginx/html

# Create nginx.conf if it doesn't exist in the source
RUN if [ ! -f /etc/nginx/conf.d/default.conf ]; then \
    cat > /etc/nginx/conf.d/default.conf << 'NGINX_EOF' \
server { \
    listen 3000; \
    listen [::]:3000; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    \
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ { \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
    } \
} \
NGINX_EOF \
fi

# Write the nginx config for SPA
RUN cat > /etc/nginx/conf.d/default.conf << 'NGINX_CONF'
server {
    listen 3000;
    listen [::]:3000;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Handle SPA routing - serve index.html for all non-file routes
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    # Cache static assets aggressively
    location ~* \.(js|css|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Cache images
    location ~* \.(png|jpg|jpeg|gif|ico|svg|webp)$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
        access_log off;
    }

    # Deny access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Error pages
    error_page 404 /index.html;
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
NGINX_CONF

# Expose frontend port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
