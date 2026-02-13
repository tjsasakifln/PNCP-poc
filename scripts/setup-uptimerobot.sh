#!/bin/bash
# ==============================================================================
# UptimeRobot Monitor Setup for SmartLic — STORY-212 (AC1-AC5)
# ==============================================================================
#
# Prerequisites:
#   1. Sign up at https://uptimerobot.com (free account)
#   2. Navigate to Dashboard > Integrations & API > API
#   3. Create a Main API Key
#   4. Set UPTIMEROBOT_API_KEY environment variable
#
# Usage:
#   export UPTIMEROBOT_API_KEY="ur_xxxxxxxxxxxxxxxxxxxx"
#   bash scripts/setup-uptimerobot.sh
#
# ==============================================================================

set -euo pipefail

BASE_URL="https://api.uptimerobot.com/v2"
API_KEY="${UPTIMEROBOT_API_KEY:?Error: UPTIMEROBOT_API_KEY environment variable is not set}"

echo "=== SmartLic UptimeRobot Setup ==="
echo ""

# Step 1: List existing alert contacts
echo "--- Step 1: Checking existing alert contacts ---"
CONTACTS=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "api_key=${API_KEY}&format=json" \
  "${BASE_URL}/getAlertContacts")

echo "$CONTACTS" | python -m json.tool 2>/dev/null || echo "$CONTACTS"

# Try to find existing contact for tiago.sasaki@gmail.com
CONTACT_ID=$(echo "$CONTACTS" | python -c "
import sys, json
data = json.load(sys.stdin)
for c in data.get('alertcontacts', []):
    if c.get('value') == 'tiago.sasaki@gmail.com':
        print(c['id'])
        sys.exit(0)
print('')
" 2>/dev/null || echo "")

if [ -z "$CONTACT_ID" ]; then
  echo ""
  echo "--- Step 2: Creating email alert contact ---"
  NEW_CONTACT=$(curl -s -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "api_key=${API_KEY}&format=json&type=2&friendly_name=Tiago+Sasaki&value=tiago.sasaki@gmail.com" \
    "${BASE_URL}/newAlertContact")

  echo "$NEW_CONTACT" | python -m json.tool 2>/dev/null || echo "$NEW_CONTACT"

  CONTACT_ID=$(echo "$NEW_CONTACT" | python -c "
import sys, json
data = json.load(sys.stdin)
print(data['alertcontact']['id'])
" 2>/dev/null || echo "")

  if [ -z "$CONTACT_ID" ]; then
    echo "ERROR: Failed to create alert contact. Check API key and try again."
    exit 1
  fi
  echo "Created alert contact ID: ${CONTACT_ID}"
else
  echo "Found existing alert contact ID: ${CONTACT_ID}"
fi

echo ""
echo "--- Step 3: Creating Backend Health Monitor ---"
BACKEND_RESULT=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "api_key=${API_KEY}&format=json&type=1&url=https://bidiq-backend-production.up.railway.app/health&friendly_name=SmartLic+Backend+Health&interval=300&alert_contacts=${CONTACT_ID}_0_0" \
  "${BASE_URL}/newMonitor")

echo "$BACKEND_RESULT" | python -m json.tool 2>/dev/null || echo "$BACKEND_RESULT"

echo ""
echo "--- Step 4: Creating Frontend Health Monitor ---"
FRONTEND_RESULT=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "api_key=${API_KEY}&format=json&type=1&url=https://smartlic.tech/api/health&friendly_name=SmartLic+Frontend+Health&interval=300&alert_contacts=${CONTACT_ID}_0_0" \
  "${BASE_URL}/newMonitor")

echo "$FRONTEND_RESULT" | python -m json.tool 2>/dev/null || echo "$FRONTEND_RESULT"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Monitors created:"
echo "  - SmartLic Backend Health (5-min interval)"
echo "  - SmartLic Frontend Health (5-min interval)"
echo "  - Alert email: tiago.sasaki@gmail.com"
echo ""
echo "Dashboard: https://dashboard.uptimerobot.com/"
echo ""
echo "To verify: Wait 5-10 minutes and check the dashboard for first ping results."
