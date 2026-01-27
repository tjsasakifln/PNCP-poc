#!/bin/bash

# BidIQ Activation Script
# Intelligently detects context and activates appropriate squad
# Usage: source bidiq-activate.sh [context]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(pwd)"

# Function: Show greeting
show_greeting() {
  echo -e "${BLUE}"
  echo "╔════════════════════════════════════════════════════════════════╗"
  echo "║            🚀 BidIQ Development Assistant                      ║"
  echo "╚════════════════════════════════════════════════════════════════╝${NC}"
  echo ""
}

# Function: Detect context
detect_context() {
  local pwd="$(pwd)"

  # Check directory
  if [[ "$pwd" == *"/backend"* ]]; then
    echo "backend"
    return
  fi

  if [[ "$pwd" == *"/frontend"* ]]; then
    echo "frontend"
    return
  fi

  if [[ "$pwd" == *"/stories"* ]]; then
    echo "feature"
    return
  fi

  # Check git branch
  if git rev-parse --git-dir > /dev/null 2>&1; then
    local branch=$(git branch --show-current)

    if [[ "$branch" == feature/* ]]; then
      echo "feature"
      return
    fi

    if [[ "$branch" == fix/* ]]; then
      echo "backend"  # Could be either
      return
    fi
  fi

  # Default
  echo "feature"
}

# Function: Suggest squad
suggest_squad() {
  local context=$1

  case "$context" in
    backend)
      echo "team-bidiq-backend"
      ;;
    frontend)
      echo "team-bidiq-frontend"
      ;;
    feature)
      echo "team-bidiq-feature"
      ;;
    *)
      echo "team-bidiq-feature"
      ;;
  esac
}

# Function: Get squad command
get_squad_command() {
  local squad=$1

  case "$squad" in
    team-bidiq-backend)
      echo "backend"
      ;;
    team-bidiq-frontend)
      echo "frontend"
      ;;
    team-bidiq-feature)
      echo "feature"
      ;;
    *)
      echo "feature"
      ;;
  esac
}

# Main execution
main() {
  show_greeting

  # Check if we're in BidIQ project
  if [ ! -f "CLAUDE.md" ] || ! grep -q "BidIQ" CLAUDE.md; then
    echo -e "${YELLOW}Not in a BidIQ project${NC}"
    return 1
  fi

  # Detect context
  local context="${1:-$(detect_context)}"
  local squad=$(suggest_squad "$context")
  local command=$(get_squad_command "$squad")

  echo -e "${GREEN}✨ Detected: $context${NC}"
  echo -e "${BLUE}📋 Recommended Squad:${NC} $squad"
  echo ""
  echo -e "${YELLOW}🚀 Next Step:${NC}"
  echo -e "   Type: ${GREEN}/bidiq $command${NC}"
  echo ""
}

# Run main
main "$@"
