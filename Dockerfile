# =============================================================================
# Railway Monorepo Dockerfile - Frontend Service
# =============================================================================
# This Dockerfile is placed at the root to help Railway find it
# It builds the frontend service located in the frontend/ directory
# =============================================================================

# CACHE BUST - forces Railway rebuild
ARG CACHEBUST=20260207-story168-landing-page-routing-fix

# Stage 1: Dependencies
FROM node:20.11-alpine3.19 AS deps
WORKDIR /app

# Force cache invalidation
ARG CACHEBUST
RUN echo "DEPS STAGE CACHE BUST: $CACHEBUST - BUILD $(date +%s)"

# Copy package files from frontend directory
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm ci && echo "Dependencies installed at $(date)"

# Stage 2: Build
FROM node:20.11-alpine3.19 AS builder
WORKDIR /app

# Redeclare CACHEBUST
ARG CACHEBUST
RUN echo "Cache bust: $CACHEBUST"

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy all frontend files
COPY frontend/ ./

# Set build-time environment variables
ENV NEXT_TELEMETRY_DISABLED=1

# Build-time args for NEXT_PUBLIC variables
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ARG NEXT_PUBLIC_BACKEND_URL
ARG NEXT_PUBLIC_APP_NAME=SmartLic
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

# Build Next.js
RUN npm run build

# Stage 3: Production
FROM node:20.11-alpine3.19 AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy standalone bundle
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Set ownership
RUN chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
