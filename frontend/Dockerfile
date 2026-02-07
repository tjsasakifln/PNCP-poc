# =============================================================================
# BidIQ Uniformes - Frontend Dockerfile (Production)
# =============================================================================
# Multi-stage build for Next.js with standalone output
# Optimized for Railway deployment

# CACHE BUST - forces Railway rebuild (change to invalidate cache)
ARG CACHEBUST=20260207-story168-landing-page-routing-fix

# Stage 1: Dependencies
# Using node:20.11-alpine3.19 instead of node:20-alpine to force layer rebuild
FROM node:20.11-alpine3.19 AS deps
WORKDIR /app

# Force cache invalidation in deps stage too
ARG CACHEBUST
RUN echo "DEPS STAGE CACHE BUST: $CACHEBUST - BUILD $(date +%s)"

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies with verbose output
RUN npm ci && echo "Dependencies installed at $(date)"

# Stage 2: Build
FROM node:20.11-alpine3.19 AS builder
WORKDIR /app

# Redeclare CACHEBUST in builder stage to invalidate cache
ARG CACHEBUST
RUN echo "Cache bust: $CACHEBUST"

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set build-time environment variables
ENV NEXT_TELEMETRY_DISABLED=1

# Build-time args for NEXT_PUBLIC variables (set via Railway service variables)
# IMPORTANT: All NEXT_PUBLIC_* variables must be declared here to be inlined in the build
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ARG NEXT_PUBLIC_BACKEND_URL
ARG NEXT_PUBLIC_APP_NAME=Smart\ PNCP
ARG NEXT_PUBLIC_LOGO_URL=/logo.svg
ARG NEXT_PUBLIC_MIXPANEL_TOKEN
ARG NEXT_PUBLIC_ENABLE_NEW_PRICING

# Convert ARGs to ENVs for Next.js build
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY
ENV NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL
ENV NEXT_PUBLIC_APP_NAME=$NEXT_PUBLIC_APP_NAME
ENV NEXT_PUBLIC_LOGO_URL=$NEXT_PUBLIC_LOGO_URL
ENV NEXT_PUBLIC_MIXPANEL_TOKEN=$NEXT_PUBLIC_MIXPANEL_TOKEN
ENV NEXT_PUBLIC_ENABLE_NEW_PRICING=$NEXT_PUBLIC_ENABLE_NEW_PRICING

# Debug: Print build-time environment variables (remove in production if too verbose)
RUN echo "=== Build-time Environment Variables ===" && \
    echo "NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL" && \
    echo "NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL" && \
    echo "========================================="

# Create build timestamp to prevent caching
RUN echo "BUILD_TIMESTAMP=$(date +%Y%m%d%H%M%S)" > /tmp/build-info.txt && cat /tmp/build-info.txt

# Build the application
# This will inline NEXT_PUBLIC_* vars into the JavaScript bundle
RUN npm run build && echo "Build completed at $(date)"

# Stage 3: Production
FROM node:20.11-alpine3.19 AS runner
WORKDIR /app

# Set production environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy necessary files from builder
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Expose port (Railway will inject PORT env var)
EXPOSE 3000

# Set default port
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

# Start the application
CMD ["node", "server.js"]
