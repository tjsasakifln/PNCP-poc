#!/bin/bash

###############################################################################
# Configure Supabase Redirect URLs - Direct API Approach
#
# Alternative script using curl for direct HTTP requests to Supabase API
###############################################################################

set -e

# Configuration
PROJECT_REF="fqqyovlzdzimiwfofdjk"
API_URL="https://api.supabase.com/v1/projects/${PROJECT_REF}/config/auth"

# Load token
if [ -z "$SUPABASE_ACCESS_TOKEN" ]; then
    export SUPABASE_ACCESS_TOKEN=$(grep SUPABASE_ACCESS_TOKEN .env | cut -d '=' -f2)
fi

if [ -z "$SUPABASE_ACCESS_TOKEN" ]; then
    echo "❌ Error: SUPABASE_ACCESS_TOKEN not found"
    exit 1
fi

echo "🔧 Configuring Supabase OAuth Redirect URLs"
echo ""

# Get current configuration
echo "📡 Fetching current configuration..."
CURRENT_CONFIG=$(curl -s -X GET "$API_URL" \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  -H "Content-Type: application/json")

echo "Current config:"
echo "$CURRENT_CONFIG" | jq '.' 2>/dev/null || echo "$CURRENT_CONFIG"
echo ""

# Update redirect URLs
echo "📝 Updating redirect URLs..."

# Prepare JSON payload with redirect URLs
PAYLOAD='{
  "REDIRECT_URLS": "https://bidiq-frontend-production.up.railway.app/auth/callback,http://localhost:3000/auth/callback"
}'

echo "Payload:"
echo "$PAYLOAD" | jq '.'
echo ""

# Send update request
UPDATE_RESPONSE=$(curl -s -X PATCH "$API_URL" \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

echo "Update response:"
echo "$UPDATE_RESPONSE" | jq '.' 2>/dev/null || echo "$UPDATE_RESPONSE"
echo ""

# Verify
echo "🔍 Verifying configuration..."
sleep 2

VERIFY_CONFIG=$(curl -s -X GET "$API_URL" \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  -H "Content-Type: application/json")

REDIRECT_URLS=$(echo "$VERIFY_CONFIG" | jq -r '.REDIRECT_URLS // "(none)"')

echo "Configured redirect URLs:"
echo "$REDIRECT_URLS"
echo ""

# Check if configuration is correct
if echo "$REDIRECT_URLS" | grep -q "auth/callback"; then
    echo "✅ Configuration successful!"
else
    echo "⚠️  Configuration may not have been applied"
    echo "   Please verify manually in Supabase Dashboard:"
    echo "   https://app.supabase.com/project/${PROJECT_REF}/auth/url-configuration"
fi

exit 0
