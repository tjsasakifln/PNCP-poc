@echo off
REM ==============================================================================
REM HOTFIX: Clear Next.js Cache and Force Clean Rebuild (Windows)
REM
REM PURPOSE: Fix "Failed to find Server Action 'x'" errors caused by stale cache
REM
REM USAGE: Double-click this file or run from command prompt
REM
REM WHAT IT DOES:
REM   1. Removes .next build cache (stale chunks)
REM   2. Removes node_modules\.cache (Babel/SWC cache)
REM   3. Clears npm cache
REM   4. Rebuilds from scratch with new Build ID
REM ==============================================================================

echo.
echo ============================================
echo HOTFIX: Clearing Next.js cache and rebuilding...
echo ============================================
echo.

REM Step 1: Remove .next directory
if exist ".next" (
    echo Removing .next cache...
    rmdir /s /q ".next"
    echo [OK] .next removed
) else (
    echo [INFO] No .next directory found
)

REM Step 2: Remove node_modules cache
if exist "node_modules\.cache" (
    echo Removing node_modules\.cache...
    rmdir /s /q "node_modules\.cache"
    echo [OK] node_modules\.cache removed
) else (
    echo [INFO] No node_modules\.cache found
)

REM Step 3: Clear npm cache
echo Clearing npm cache...
call npm cache clean --force

REM Step 4: Reinstall dependencies
echo.
echo Reinstalling dependencies...
call npm ci --prefer-offline

REM Step 5: Clean build
echo.
echo Building Next.js app with new Build ID...
call npm run build

echo.
echo ============================================
echo HOTFIX COMPLETE!
echo ============================================
echo.
echo Next steps:
echo   1. Test locally: npm run dev
echo   2. Deploy to production
echo   3. Clear CDN cache (if using Vercel/Cloudflare)
echo.
echo IMPORTANT FOR PRODUCTION:
echo   - Vercel: Automatic cache clear on deploy
echo   - Railway: May need manual redeploy
echo   - Other CDN: Clear cache manually
echo.
pause
