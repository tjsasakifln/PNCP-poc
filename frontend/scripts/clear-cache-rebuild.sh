#!/bin/bash

#===============================================================================
# HOTFIX: Clear Next.js Cache and Force Clean Rebuild
#
# PURPOSE: Fix "Failed to find Server Action 'x'" errors caused by stale cache
#
# USAGE:
#   chmod +x scripts/clear-cache-rebuild.sh
#   ./scripts/clear-cache-rebuild.sh
#
# WHAT IT DOES:
#   1. Removes .next build cache (stale chunks)
#   2. Removes node_modules/.cache (Babel/SWC cache)
#   3. Clears npm cache
#   4. Rebuilds from scratch with new Build ID
#===============================================================================

set -e  # Exit on error

echo "🧹 HOTFIX: Clearing Next.js cache and rebuilding..."
echo "=============================================="

# Step 1: Remove .next directory
if [ -d ".next" ]; then
  echo "🗑️  Removing .next cache..."
  rm -rf .next
  echo "✅ .next removed"
else
  echo "ℹ️  No .next directory found"
fi

# Step 2: Remove node_modules cache
if [ -d "node_modules/.cache" ]; then
  echo "🗑️  Removing node_modules/.cache..."
  rm -rf node_modules/.cache
  echo "✅ node_modules/.cache removed"
else
  echo "ℹ️  No node_modules/.cache found"
fi

# Step 3: Clear npm cache (optional but recommended)
echo "🧹 Clearing npm cache..."
npm cache clean --force 2>/dev/null || echo "⚠️  npm cache clean failed (non-critical)"

# Step 4: Reinstall dependencies (ensures no corrupted packages)
echo "📦 Reinstalling dependencies..."
npm ci --prefer-offline

# Step 5: Clean build
echo "🔨 Building Next.js app with new Build ID..."
npm run build

echo ""
echo "=============================================="
echo "✅ HOTFIX COMPLETE!"
echo ""
echo "📝 Next steps:"
echo "   1. Test locally: npm run dev"
echo "   2. Deploy to production"
echo "   3. Clear CDN cache (if using Vercel/Cloudflare)"
echo ""
echo "🚨 IMPORTANT FOR PRODUCTION:"
echo "   - Vercel: Automatic cache clear on deploy"
echo "   - Railway: May need manual redeploy"
echo "   - Other CDN: Clear cache manually"
echo ""
