#!/usr/bin/env bash
# =============================================================================
# Automated Lithology Classification System - Setup Script
# =============================================================================
# Usage: bash scripts/setup.sh [--dev] [--skip-build] [--skip-seed]
# Options:
#   --dev         Use development docker-compose configuration
#   --skip-build  Skip docker-compose build step
#   --skip-seed   Skip database seeding step
# =============================================================================

set -euo pipefail
IFS=$'\n\t'

# -----------------------------------------------------------------------------
# Color codes and logging helpers
# -----------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

log_info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_success() { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_step()    { echo -e "\n${CYAN}==>${NC} ${WHITE}$*${NC}"; }
log_banner()  {
    echo -e "${CYAN}"
    echo "  ╔══════════════════════════════════════════════════════════╗"
    echo "  ║     🪨 Lithology Classification System - Setup          ║"
    echo "  ║        Automated Drill Core Analysis Platform           ║"
    echo "  ╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# -----------------------------------------------------------------------------
# Parse arguments
# -----------------------------------------------------------------------------
DEV_MODE=false
SKIP_BUILD=false
SKIP_SEED=false

for arg in "$@"; do
    case $arg in
        --dev)         DEV_MODE=true ;;
        --skip-build)  SKIP_BUILD=true ;;
        --skip-seed)   SKIP_SEED=true ;;
        --help|-h)
            echo "Usage: $0 [--dev] [--skip-build] [--skip-seed]"
            exit 0
            ;;
        *)
            log_warn "Unknown argument: $arg"
            ;;
    esac
done

COMPOSE_FILE="docker-compose.yml"
if [ "$DEV_MODE" = true ]; then
    COMPOSE_FILE="docker-compose.dev.yml"
    log_warn "Running in DEVELOPMENT mode"
fi

# -----------------------------------------------------------------------------
# Script directory
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

log_banner

# -----------------------------------------------------------------------------
# Step 1: Check Prerequisites
# -----------------------------------------------------------------------------
log_step "Checking prerequisites..."

MISSING_DEPS=()

check_command() {
    local cmd=$1
    local name=${2:-$1}
    local min_version=${3:-""}
    if command -v "$cmd" &>/dev/null; then
        local version
        version=$(${cmd} --version 2>/dev/null | head -n1 || echo "unknown")
        log_success "$name found: $version"
    else
        log_error "$name is required but not installed."
        MISSING_DEPS+=("$name")
    fi
}

check_command "docker"         "Docker"
check_command "docker-compose" "Docker Compose" || check_command "docker compose" "Docker Compose (plugin)"
check_command "python3"        "Python 3"
check_command "curl"           "curl"

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    log_error "Missing required dependencies: ${MISSING_DEPS[*]}"
    log_error "Please install the missing dependencies and run setup again."
    log_error ""
    log_error "  Docker:         https://docs.docker.com/get-docker/"
    log_error "  Docker Compose: https://docs.docker.com/compose/install/"
    log_error "  Python 3:       https://www.python.org/downloads/"
    exit 1
fi

# Check Docker daemon is running
if ! docker info &>/dev/null; then
    log_error "Docker daemon is not running. Please start Docker and try again."
    exit 1
fi
log_success "Docker daemon is running"

# Check Docker Compose version (support both v1 and v2)
if command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    log_error "Docker Compose is not available."
    exit 1
fi
log_success "Using compose command: $COMPOSE_CMD"

# Check available disk space (require at least 10GB)
AVAILABLE_SPACE=$(df -BG "${PROJECT_ROOT}" | awk 'NR==2 {print $4}' | tr -d 'G')
if [ "${AVAILABLE_SPACE:-0}" -lt 10 ]; then
    log_warn "Low disk space detected: ${AVAILABLE_SPACE}GB available. Recommend at least 10GB."
fi

# Check available RAM (require at least 4GB)
if command -v free &>/dev/null; then
    AVAILABLE_RAM=$(free -g | awk 'NR==2 {print $7}')
    if [ "${AVAILABLE_RAM:-0}" -lt 4 ]; then
        log_warn "Low available RAM: ${AVAILABLE_RAM}GB. Recommend at least 4GB free."
    fi
fi

log_success "All prerequisite checks passed!"

# -----------------------------------------------------------------------------
# Step 2: Environment Configuration
# -----------------------------------------------------------------------------
log_step "Setting up environment configuration..."

cd "${PROJECT_ROOT}"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_success "Created .env from .env.example"
        log_warn "⚠️  Please edit .env and update sensitive values before production deployment!"
        log_warn "   Especially: SECRET_KEY, POSTGRES_PASSWORD, SMTP credentials"
    else
        log_error ".env.example not found. Cannot create .env file."
        exit 1
    fi
else
    log_info ".env already exists. Skipping copy."
fi

# Generate a new secret key if the default one is used
if grep -q "your-super-secret-key-change-in-production" .env; then
    NEW_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/your-super-secret-key-change-in-production.*/${NEW_SECRET}/" .env
    else
        sed -i "s/your-super-secret-key-change-in-production.*/${NEW_SECRET}/" .env
    fi
    log_success "Generated new SECRET_KEY"
fi

# -----------------------------------------------------------------------------
# Step 3: Create Required Directories
# -----------------------------------------------------------------------------
log_step "Creating required directories..."

DIRECTORIES=(
    "uploads"
    "uploads/images"
    "uploads/datasets"
    "uploads/reports"
    "model_weights"
    "faiss_index"
    "knowledge_base"
    "logs"
    "nginx/conf.d"
    "scripts"
)

for dir in "${DIRECTORIES[@]}"; do
    if [ ! -d "${dir}" ]; then
        mkdir -p "${dir}"
        log_success "Created directory: ${dir}"
    else
        log_info "Directory exists: ${dir}"
    fi
done

# Create .gitkeep files to preserve empty directories in git
for dir in uploads model_weights faiss_index knowledge_base logs; do
    touch "${dir}/.gitkeep" 2>/dev/null || true
done

# Create init_db.sql if it doesn't exist
if [ ! -f "scripts/init_db.sql" ]; then
    cat > scripts/init_db.sql << 'SQL'
-- Initialize PostgreSQL database for Lithology Classification System
-- This script runs on first container startup

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create test database
SELECT 'CREATE DATABASE lithology_test_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'lithology_test_db')\gexec

\echo 'Database initialization complete.'
SQL
    log_success "Created scripts/init_db.sql"
fi

log_success "Directory structure created!"

# -----------------------------------------------------------------------------
# Step 4: Build Docker Images
# -----------------------------------------------------------------------------
if [ "$SKIP_BUILD" = false ]; then
    log_step "Building Docker images..."
    log_info "This may take several minutes on first run..."

    if $COMPOSE_CMD -f "${COMPOSE_FILE}" build --parallel 2>&1; then
        log_success "Docker images built successfully!"
    else
        log_error "Docker build failed. Check the output above for details."
        exit 1
    fi
else
    log_info "Skipping Docker build (--skip-build flag set)"
fi

# -----------------------------------------------------------------------------
# Step 5: Start Services
# -----------------------------------------------------------------------------
log_step "Starting services..."

if $COMPOSE_CMD -f "${COMPOSE_FILE}" up -d 2>&1; then
    log_success "Services started!"
else
    log_error "Failed to start services."
    log_error "Run '$COMPOSE_CMD logs' for more details."
    exit 1
fi

# -----------------------------------------------------------------------------
# Step 6: Wait for Services to be Healthy
# -----------------------------------------------------------------------------
log_step "Waiting for services to become healthy..."

wait_for_service() {
    local service=$1
    local url=$2
    local max_attempts=${3:-30}
    local attempt=0

    log_info "Waiting for ${service}..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "${url}" &>/dev/null; then
            log_success "${service} is healthy!"
            return 0
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 3
    done
    echo ""
    log_warn "${service} did not become healthy after $((max_attempts * 3)) seconds"
    return 1
}

# Wait for database
DB_HEALTHY=false
log_info "Waiting for PostgreSQL to be ready..."
for i in $(seq 1 30); do
    if $COMPOSE_CMD -f "${COMPOSE_FILE}" exec -T db pg_isready -U postgres &>/dev/null; then
        log_success "PostgreSQL is ready!"
        DB_HEALTHY=true
        break
    fi
    echo -n "."
    sleep 3
done
echo ""
if [ "$DB_HEALTHY" = false ]; then
    log_warn "PostgreSQL may not be fully ready. Continuing anyway..."
fi

# Wait for Redis
REDIS_HEALTHY=false
log_info "Waiting for Redis to be ready..."
for i in $(seq 1 20); do
    if $COMPOSE_CMD -f "${COMPOSE_FILE}" exec -T redis redis-cli ping &>/dev/null; then
        log_success "Redis is ready!"
        REDIS_HEALTHY=true
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

# Wait for backend API
wait_for_service "Backend API" "http://localhost:8000/health" 40
wait_for_service "Frontend"    "http://localhost:3000"        20

# -----------------------------------------------------------------------------
# Step 7: Run Database Migrations
# -----------------------------------------------------------------------------
log_step "Running database migrations..."

if $COMPOSE_CMD -f "${COMPOSE_FILE}" exec -T backend alembic upgrade head 2>&1; then
    log_success "Database migrations completed!"
else
    log_warn "Database migrations may have failed. Check logs: $COMPOSE_CMD logs backend"
fi

# -----------------------------------------------------------------------------
# Step 8: Seed Database
# -----------------------------------------------------------------------------
if [ "$SKIP_SEED" = false ]; then
    log_step "Seeding database with initial data..."

    if $COMPOSE_CMD -f "${COMPOSE_FILE}" exec -T backend python scripts/seed_db.py 2>&1; then
        log_success "Database seeded successfully!"
    else
        log_warn "Database seeding may have encountered issues. This is OK if data already exists."
    fi
else
    log_info "Skipping database seed (--skip-seed flag set)"
fi

# -----------------------------------------------------------------------------
# Step 9: Print Success Summary
# -----------------------------------------------------------------------------
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          🎉  Setup Complete! System is Ready  🎉         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${WHITE}Application URLs:${NC}"
echo -e "  ${CYAN}➜${NC}  Frontend:       ${GREEN}http://localhost:80${NC}"
echo -e "  ${CYAN}➜${NC}  Backend API:    ${GREEN}http://localhost:8000${NC}"
echo -e "  ${CYAN}➜${NC}  Swagger UI:     ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  ${CYAN}➜${NC}  ReDoc:          ${GREEN}http://localhost:8000/redoc${NC}"
echo ""
echo -e "  ${WHITE}Default Credentials:${NC}"
echo -e "  ${CYAN}➜${NC}  Admin:  ${YELLOW}admin@lithology.ai${NC} / ${YELLOW}Admin@123456${NC}"
echo -e "  ${CYAN}➜${NC}  Demo:   ${YELLOW}demo@lithology.ai${NC}  / ${YELLOW}Demo@123456${NC}"
echo ""
echo -e "  ${WHITE}Useful Commands:${NC}"
echo -e "  ${CYAN}➜${NC}  View logs:      ${WHITE}make logs${NC}  or  ${WHITE}${COMPOSE_CMD} logs -f${NC}"
echo -e "  ${CYAN}➜${NC}  Stop services:  ${WHITE}make down${NC}  or  ${WHITE}${COMPOSE_CMD} down${NC}"
echo -e "  ${CYAN}➜${NC}  Run tests:      ${WHITE}make test${NC}"
echo ""
echo -e "  ${YELLOW}⚠️  Remember to update SECRET_KEY and passwords in .env before production!${NC}"
echo ""
