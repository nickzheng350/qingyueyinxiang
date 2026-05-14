#!/usr/bin/env bash
# =============================================================================
# HydraFlow AI - Docker Deployment Start Script
# =============================================================================
# Usage: ./deploy/scripts/docker-start.sh [options]
#   -b, --build    Build images before starting
#   -d, --detach   Run containers in background (daemon mode)
#   -f, --force     Force rebuild without cache
#   --no-backend    Skip backend API container
#   --no-frontend   Skip frontend container
#   --no-redis      Skip Redis container
#   --with-postgres Start with PostgreSQL
#   --with-monitoring Start with Prometheus + Grafana
#   -h, --help     Show this help message
#
# Examples:
#   ./deploy/scripts/docker-start.sh           # Start all services
#   ./deploy/scripts/docker-start.sh -bd       # Build & start in background
#   ./deploy/scripts/docker-start.sh -bd --with-postgres --with-monitoring
# =============================================================================

set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GRN='\033[0;32m'; YEL='\033[1;33m'; BLU='\033[0;34m'
CYN='\033[0;36m'; NC='\033[0m' # No Color

info()    { echo -e "${GRN}[INFO]${NC}  $*"; }
warn()    { echo -e "${YEL}[WARN]${NC}  $*" >&2; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
section() { echo -e "\n${BLU}══ $* ══${NC}"; }

# ── Defaults ──────────────────────────────────────────────────────────────────
COMPOSE_FILE="docker-compose.yml"
COMPOSE_PROJECT="hydraflow"
DAEMON=false
BUILD=false
FORCE_BUILD=false
SKIP_BACKEND=false
SKIP_FRONTEND=false
SKIP_REDIS=false
WITH_POSTGRES=false
WITH_MONITORING=false

# ── Parse arguments ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    -b|--build)     BUILD=true;     shift ;;
    -d|--detach)    DAEMON=true;    shift ;;
    -f|--force)     FORCE_BUILD=true; shift ;;
    --no-backend)   SKIP_BACKEND=true;  shift ;;
    --no-frontend)  SKIP_FRONTEND=true; shift ;;
    --no-redis)     SKIP_REDIS=true;     shift ;;
    --with-postgres)    WITH_POSTGRES=true;   shift ;;
    --with-monitoring)  WITH_MONITORING=true; shift ;;
    -h|--help)      grep "^#" "$0" | grep -v "^#!/bin/bash" | cut -c3-; exit 0 ;;
    *)              error "Unknown option: $1"; exit 1 ;;
  esac
done

# ── Pre-flight checks ─────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  error "docker-compose.yml not found in: $PROJECT_DIR"
  exit 1
fi

if ! command -v docker &>/dev/null; then
  error "Docker is not installed. Please install Docker first."
  exit 1
fi

if ! docker compose version &>/dev/null && ! docker-compose --version &>/dev/null; then
  error "Docker Compose is not available."
  exit 1
fi

# Detect docker compose command
if docker compose version &>/dev/null; then
  COMPOSE_CMD="docker compose"
else
  COMPOSE_CMD="docker-compose"
fi

# ── Build composition ─────────────────────────────────────────────────────────
build_services() {
  local extra_args=()
  [[ "$FORCE_BUILD" == true ]] && extra_args+=(--no-cache --force-recreate)
  [[ "$FORCE_BUILD" == true ]] && extra_args+=(--force-recreate)

  $COMPOSE_CMD build "${extra_args[@]}" api
  info "Build complete."
}

# ── Docker Compose override file generation ───────────────────────────────────
generate_override() {
  local tmpfile="$PROJECT_DIR/docker-compose.override.yml"

  cat > "$tmpfile" << EOF
# Auto-generated override - do not edit manually
# Generated at $(date -u +"%Y-%m-%dT%H:%M:%SZ")

services:
EOF

  # Dynamically enable/disable services
  if $SKIP_BACKEND; then
    echo "  api: {build: {context: .}, image: hydraflow-ai:latest}" >> "$tmpfile"
    echo "    profiles: [disabled]" >> "$tmpfile"
  fi

  if $SKIP_FRONTEND; then
    echo "  frontend: {image: nginx:1.25-alpine}" >> "$tmpfile"
    echo "    profiles: [disabled]" >> "$tmpfile"
  fi

  if ! $WITH_POSTGRES; then
    cat >> "$tmpfile" << EOF
  postgres:
    profiles: [disabled]
EOF
  fi

  if ! $WITH_MONITORING; then
    cat >> "$tmpfile" << EOF
  prometheus:
    profiles: [disabled]
  grafana:
    profiles: [disabled]
EOF
  fi

  echo "Override written to: $tmpfile"
}

# ── Start containers ────────────────────────────────────────────────────────────
start_services() {
  local up_args=("-d")
  [[ "$DAEMON" == false ]] && up_args=()

  # Build if requested
  if $BUILD || $FORCE_BUILD; then
    section "Building Docker images"
    build_services
  fi

  section "Starting HydraFlow containers"

  # Generate dynamic override
  generate_override

  # Pull latest images first
  info "Pulling base images..."
  $COMPOSE_CMD pull --quiet 2>/dev/null || true

  # Start services
  $COMPOSE_CMD up "${up_args[@]}" --remove-orphans

  # Show status
  sleep 2
  section "Container Status"
  $COMPOSE_CMD ps --format table 2>/dev/null || docker-compose ps

  # Show useful URLs
  echo ""
  info "HydraFlow services:"
  [[ ! $SKIP_BACKEND ]] && echo -e "  ${CYN}API:${NC}   http://localhost:8000"
  [[ ! $SKIP_BACKEND ]] && echo -e "  ${CYN}Docs:${NC}  http://localhost:8000/docs"
  [[ ! $SKIP_FRONTEND ]] && echo -e "  ${CYN}UI:${NC}    http://localhost:3000"
  [[ $WITH_MONITORING ]] && echo -e "  ${CYN}Prom:${NC}  http://localhost:9090"
  [[ $WITH_MONITORING ]] && echo -e "  ${CYN}Graf:${NC}  http://localhost:3001"
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
  echo ""
  echo -e "${CYN}╔══════════════════════════════════════════════╗${NC}"
  echo -e "${CYN}║     HydraFlow AI - Docker Launcher      ║${NC}"
  echo -e "${CYN}╚══════════════════════════════════════════════╝${NC}"
  echo ""

  local mode_str="Foreground"
  $DAEMON && mode_str="Background (daemon)"
  info "Mode: $mode_str"
  [[ $BUILD ]] && info "Will build images first"

  start_services

  if [[ "$DAEMON" == false ]]; then
    echo ""
    warn "Running in foreground. Press Ctrl+C to stop."
    trap '$COMPOSE_CMD down' EXIT
    wait
  else
    section "Useful Commands"
    echo -e "  View logs:     ${CYN}$COMPOSE_CMD logs -f${NC}"
    echo -e "  Stop services: ${CYN}$COMPOSE_CMD down${NC}"
    echo -e "  Restart:       ${CYN}$COMPOSE_CMD restart${NC}"
    echo -e "  Full rebuild:   ${CYN}$COMPOSE_CMD down && $COMPOSE_CMD up -d --build${NC}"
  fi
}

main "$@"