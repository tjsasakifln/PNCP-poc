# =============================================================================
# BidIQ Uniformes - Frontend Dockerfile (Production)
# =============================================================================
# Multi-stage build for Next.js with standalone output
# Optimized for Railway deployment

# CACHE BUST - forces Railway rebuild
ARG CACHEBUST=20260204v1

# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Stage 2: Build
FROM node:20-alpine AS builder
WORKDIR /app

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

# Build the application
RUN npm run build

# Stage 3: Production
FROM node:20-alpine AS runner
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
