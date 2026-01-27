#!/bin/bash

# BidIQ Adaptive Greeting Hook
# Automatically runs on session start or file changes
# Shows context-aware squad suggestions

# Check if we're in a BidIQ project
if [ ! -f "CLAUDE.md" ] || ! grep -q "BidIQ" CLAUDE.md; then
  exit 0
fi

# Run the greeting system
node ".aios-core/development/scripts/bidiq-greeting-system.js"
