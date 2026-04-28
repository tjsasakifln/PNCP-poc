# =============================================================================
# BidIQ Uniformes - Frontend Dockerfile (Production)
# =============================================================================
# Multi-stage build for Next.js with standalone output
# Optimized for Railway deployment

# CACHE BUST - forces Railway rebuild (change to invalidate cache)
# GTM-FIX-002: Add missing NEXT_PUBLIC_* build ARGs for Sentry/Mixpanel/Stripe
ARG CACHEBUST=20260426-seo020-backend-url-arg

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
RUN npm ci --legacy-peer-deps && echo "Dependencies installed at $(date)"

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
# STORY-SEO-020: server-only BACKEND_URL needed by sitemap.ts at build time.
# Without this, frontend/app/sitemap.ts falls back to localhost:8000, producing
# sitemap-4.xml with 0 <loc> entries in production.
ARG BACKEND_URL
ARG NEXT_PUBLIC_CANONICAL_URL
ARG NEXT_PUBLIC_APP_URL
ARG NEXT_PUBLIC_APP_NAME=SmartLic
ARG NEXT_PUBLIC_LOGO_URL=/logo.svg
# Observability (GTM-FIX-002)
ARG NEXT_PUBLIC_SENTRY_DSN
ARG NEXT_PUBLIC_ENVIRONMENT=production
ARG NEXT_PUBLIC_MIXPANEL_TOKEN
ARG NEXT_PUBLIC_ENABLE_ANALYTICS
# MS Clarity (heatmaps + session recordings). Without this ARG the project ID
# never reaches the Next.js build, ClarityAnalytics.tsx reads `undefined` from
# process.env at runtime, and the script tag is never injected — Clarity
# dashboard stays in the "ALMOST THERE" empty state forever (verified
# 2026-04-27 goofy-llama; same class of bug as PR #531 BACKEND_URL ARG fix).
ARG NEXT_PUBLIC_CLARITY_PROJECT_ID
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
ENV BACKEND_URL=$BACKEND_URL
ENV NEXT_PUBLIC_CANONICAL_URL=$NEXT_PUBLIC_CANONICAL_URL
ENV NEXT_PUBLIC_APP_URL=$NEXT_PUBLIC_APP_URL
ENV NEXT_PUBLIC_APP_NAME=$NEXT_PUBLIC_APP_NAME
ENV NEXT_PUBLIC_LOGO_URL=$NEXT_PUBLIC_LOGO_URL
ENV NEXT_PUBLIC_SENTRY_DSN=$NEXT_PUBLIC_SENTRY_DSN
ENV NEXT_PUBLIC_ENVIRONMENT=$NEXT_PUBLIC_ENVIRONMENT
ENV NEXT_PUBLIC_MIXPANEL_TOKEN=$NEXT_PUBLIC_MIXPANEL_TOKEN
ENV NEXT_PUBLIC_ENABLE_ANALYTICS=$NEXT_PUBLIC_ENABLE_ANALYTICS
ENV NEXT_PUBLIC_CLARITY_PROJECT_ID=$NEXT_PUBLIC_CLARITY_PROJECT_ID
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
    echo "BACKEND_URL=$BACKEND_URL" && \
    echo "NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL" && \
    echo "NEXT_PUBLIC_CANONICAL_URL=$NEXT_PUBLIC_CANONICAL_URL" && \
    echo "NEXT_PUBLIC_APP_URL=$NEXT_PUBLIC_APP_URL" && \
    echo "NEXT_PUBLIC_SENTRY_DSN=$(echo $NEXT_PUBLIC_SENTRY_DSN | head -c 30)..." && \
    echo "NEXT_PUBLIC_MIXPANEL_TOKEN=$(echo $NEXT_PUBLIC_MIXPANEL_TOKEN | head -c 10)..." && \
    echo "NEXT_PUBLIC_CLARITY_PROJECT_ID=$NEXT_PUBLIC_CLARITY_PROJECT_ID" && \
    echo "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=$(echo $NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY | head -c 15)..." && \
    echo "SENTRY_ORG=$SENTRY_ORG" && \
    echo "SENTRY_PROJECT=$SENTRY_PROJECT" && \
    echo "========================================="

# Create build timestamp to prevent caching
RUN echo "BUILD_TIMESTAMP=$(date +%Y%m%d%H%M%S)" > /tmp/build-info.txt && cat /tmp/build-info.txt

# SEO-PROG-008: Build-time assertion — fail fast if BACKEND_URL absent in prod build.
# Memory `reference_frontend_dockerfile_backend_url_gap_2026_04_24`: build-time SSG
# fetches (sitemap.ts, /cnpj/[cnpj], /fornecedores/[cnpj], etc.) silently fall back
# to localhost:8000 if Railway service var is missing → sitemap-4.xml renders with 0
# entries → GSC indexing collapses. Asserting at build prevents silent regression.
RUN if [ "$NEXT_PUBLIC_ENVIRONMENT" = "production" ]; then \
      if [ -z "$BACKEND_URL" ]; then \
        echo "ERROR: BACKEND_URL is required in production builds. Set Railway service variable bidiq-frontend.BACKEND_URL=https://api.smartlic.tech" >&2; \
        exit 1; \
      fi; \
      if [ -z "$NEXT_PUBLIC_BACKEND_URL" ]; then \
        echo "ERROR: NEXT_PUBLIC_BACKEND_URL is required in production builds (client-side fetches). Set Railway service variable bidiq-frontend.NEXT_PUBLIC_BACKEND_URL=https://api.smartlic.tech" >&2; \
        exit 1; \
      fi; \
      echo "BACKEND_URL assertion: OK (BACKEND_URL=$BACKEND_URL, NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL)"; \
    else \
      echo "BACKEND_URL assertion: SKIPPED (NEXT_PUBLIC_ENVIRONMENT=$NEXT_PUBLIC_ENVIRONMENT, not production)"; \
    fi

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

# SLA-001: Copy graceful shutdown wrapper script
COPY --chown=nextjs:nodejs start.sh ./start.sh
RUN chmod +x start.sh

# Switch to non-root user
USER nextjs

# Expose port (Railway will inject PORT env var at runtime)
EXPOSE 3000

# IMPORTANT: Do NOT set ENV PORT here - let Railway inject it at runtime
# Next.js standalone server.js respects process.env.PORT automatically
ENV HOSTNAME="0.0.0.0"

# SLA-002: Cap Node.js heap at 512MB to prevent OOM kills on Railway 1GB plans.
# Without this, V8 defaults to ~1.5GB heap which exceeds container memory limit,
# triggering silent OOM kills (SIGKILL) with no error logs.
ENV NODE_OPTIONS="--max-old-space-size=512"

# Railway has its own healthcheck system - no need for Docker HEALTHCHECK
# This avoids conflicts and lets Railway manage the health monitoring

# SLA-001: Use shell wrapper for proper SIGTERM handling during deploys
CMD ["/app/start.sh"]
