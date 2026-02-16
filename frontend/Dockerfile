# =============================================================================
# BidIQ Uniformes - Frontend Dockerfile (Production)
# =============================================================================
# Multi-stage build for Next.js with standalone output
# Optimized for Railway deployment

# CACHE BUST - forces Railway rebuild (change to invalidate cache)
# GTM-FIX-002: Add missing NEXT_PUBLIC_* build ARGs for Sentry/Mixpanel/Stripe
ARG CACHEBUST=20260216-gtm-fix-002-observability

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
# GTM-FIX-002: Added Sentry, Stripe, analytics, and feature flag vars
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ARG NEXT_PUBLIC_BACKEND_URL
ARG NEXT_PUBLIC_CANONICAL_URL
ARG NEXT_PUBLIC_APP_URL
ARG NEXT_PUBLIC_APP_NAME=SmartLic
ARG NEXT_PUBLIC_LOGO_URL=/logo.svg
# Observability (GTM-FIX-002)
ARG NEXT_PUBLIC_SENTRY_DSN
ARG NEXT_PUBLIC_ENVIRONMENT=production
ARG NEXT_PUBLIC_MIXPANEL_TOKEN
ARG NEXT_PUBLIC_ENABLE_ANALYTICS
# Stripe
ARG NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
ARG NEXT_PUBLIC_ENABLE_NEW_PRICING
ARG NEXT_PUBLIC_ENABLE_ANNUAL_PLANS
# Feature flags
ARG NEXT_PUBLIC_ENABLE_DARK_MODE
ARG NEXT_PUBLIC_ENABLE_SAVED_SEARCHES
ARG NEXT_PUBLIC_ENABLE_SSE_PROGRESS
# Sentry webpack plugin (source map upload)
ARG SENTRY_DSN
ARG SENTRY_AUTH_TOKEN
ARG SENTRY_ORG
ARG SENTRY_PROJECT

# Convert ARGs to ENVs for Next.js build
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY
ENV NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL
ENV NEXT_PUBLIC_CANONICAL_URL=$NEXT_PUBLIC_CANONICAL_URL
ENV NEXT_PUBLIC_APP_URL=$NEXT_PUBLIC_APP_URL
ENV NEXT_PUBLIC_APP_NAME=$NEXT_PUBLIC_APP_NAME
ENV NEXT_PUBLIC_LOGO_URL=$NEXT_PUBLIC_LOGO_URL
ENV NEXT_PUBLIC_SENTRY_DSN=$NEXT_PUBLIC_SENTRY_DSN
ENV NEXT_PUBLIC_ENVIRONMENT=$NEXT_PUBLIC_ENVIRONMENT
ENV NEXT_PUBLIC_MIXPANEL_TOKEN=$NEXT_PUBLIC_MIXPANEL_TOKEN
ENV NEXT_PUBLIC_ENABLE_ANALYTICS=$NEXT_PUBLIC_ENABLE_ANALYTICS
ENV NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=$NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
ENV NEXT_PUBLIC_ENABLE_NEW_PRICING=$NEXT_PUBLIC_ENABLE_NEW_PRICING
ENV NEXT_PUBLIC_ENABLE_ANNUAL_PLANS=$NEXT_PUBLIC_ENABLE_ANNUAL_PLANS
ENV NEXT_PUBLIC_ENABLE_DARK_MODE=$NEXT_PUBLIC_ENABLE_DARK_MODE
ENV NEXT_PUBLIC_ENABLE_SAVED_SEARCHES=$NEXT_PUBLIC_ENABLE_SAVED_SEARCHES
ENV NEXT_PUBLIC_ENABLE_SSE_PROGRESS=$NEXT_PUBLIC_ENABLE_SSE_PROGRESS
ENV SENTRY_DSN=$SENTRY_DSN
ENV SENTRY_AUTH_TOKEN=$SENTRY_AUTH_TOKEN
ENV SENTRY_ORG=$SENTRY_ORG
ENV SENTRY_PROJECT=$SENTRY_PROJECT

# Debug: Print build-time environment variables
RUN echo "=== Build-time Environment Variables ===" && \
    echo "NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL" && \
    echo "NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL" && \
    echo "NEXT_PUBLIC_CANONICAL_URL=$NEXT_PUBLIC_CANONICAL_URL" && \
    echo "NEXT_PUBLIC_APP_URL=$NEXT_PUBLIC_APP_URL" && \
    echo "NEXT_PUBLIC_SENTRY_DSN=$(echo $NEXT_PUBLIC_SENTRY_DSN | head -c 30)..." && \
    echo "NEXT_PUBLIC_MIXPANEL_TOKEN=$(echo $NEXT_PUBLIC_MIXPANEL_TOKEN | head -c 10)..." && \
    echo "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=$(echo $NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY | head -c 15)..." && \
    echo "SENTRY_ORG=$SENTRY_ORG" && \
    echo "SENTRY_PROJECT=$SENTRY_PROJECT" && \
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

# Expose port (Railway will inject PORT env var at runtime)
EXPOSE 3000

# IMPORTANT: Do NOT set ENV PORT here - let Railway inject it at runtime
# Next.js standalone server.js respects process.env.PORT automatically
ENV HOSTNAME="0.0.0.0"

# Railway has its own healthcheck system - no need for Docker HEALTHCHECK
# This avoids conflicts and lets Railway manage the health monitoring

# Start the application
CMD ["node", "server.js"]
