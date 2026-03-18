
#!/bin/bash
# RealtyIQ Development Environment Setup Script
# Run this when opening a new terminal: source dev-setup.sh

set -e  # Exit on error

echo "🚀 RealtyIQ Development Environment Setup"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ============================================
# 1. Load nvm and check Node.js version
# ============================================
echo "📦 Checking Node.js setup..."

# Load nvm
export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
    source "$NVM_DIR/nvm.sh"
    echo -e "${GREEN}✓${NC} nvm loaded"
else
    echo -e "${RED}✗${NC} nvm not found. Install with:"
    echo "  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash"
    exit 1
fi

# Check for .nvmrc
if [ -f ".nvmrc" ]; then
    REQUIRED_NODE=$(cat .nvmrc)
    echo "  Required Node version: v$REQUIRED_NODE"
    
    # Check current version
    CURRENT_NODE=$(node --version 2>/dev/null || echo "none")
    
    if [ "$CURRENT_NODE" = "v$REQUIRED_NODE" ]; then
        echo -e "${GREEN}✓${NC} Node.js $CURRENT_NODE (correct version)"
    else
        echo -e "${YELLOW}⚠${NC}  Node.js $CURRENT_NODE (expected v$REQUIRED_NODE)"
        echo "  Switching to v$REQUIRED_NODE..."
        
        # Check if version is installed
        if nvm ls "$REQUIRED_NODE" >/dev/null 2>&1; then
            nvm use "$REQUIRED_NODE"
            echo -e "${GREEN}✓${NC} Switched to Node.js v$REQUIRED_NODE"
        else
            echo "  Installing Node.js v$REQUIRED_NODE..."
            nvm install "$REQUIRED_NODE"
            nvm use "$REQUIRED_NODE"
            echo -e "${GREEN}✓${NC} Installed and switched to Node.js v$REQUIRED_NODE"
        fi
    fi
else
    # No .nvmrc, check if Node is installed
    if command -v node >/dev/null 2>&1; then
        NODE_VERSION=$(node --version)
        echo -e "${GREEN}✓${NC} Node.js $NODE_VERSION"
    else
        echo -e "${YELLOW}⚠${NC}  Node.js not installed. Installing latest LTS..."
        nvm install --lts
        nvm use --lts
        echo -e "${GREEN}✓${NC} Node.js installed"
    fi
fi

# Show npm version
NPM_VERSION=$(npm --version 2>/dev/null || echo "N/A")
echo "  npm version: $NPM_VERSION"

echo ""

# ============================================
# 2. Activate Python virtual environment
# ============================================
echo "🐍 Checking Python environment..."

# Look for virtual environment
VENV_PATH=""
if [ -d "venv" ]; then
    VENV_PATH="venv"
elif [ -d ".venv" ]; then
    VENV_PATH=".venv"
elif [ -d "env" ]; then
    VENV_PATH="env"
fi

if [ -n "$VENV_PATH" ]; then
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
        PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
        echo -e "${GREEN}✓${NC} Virtual environment activated ($VENV_PATH)"
        echo "  Python version: $PYTHON_VERSION"
    else
        echo -e "${RED}✗${NC} Virtual environment found but activation script missing"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠${NC}  No virtual environment found (venv, .venv, or env)"
    echo "  Create one with: python3 -m venv venv"
    # Don't exit, continue to load .env
fi

echo ""

# ============================================
# 3. Load environment variables from .env
# ============================================
echo "⚙️  Loading environment variables..."

if [ -f ".env" ]; then
    # Export all variables from .env (ignore comments and empty lines)
    set -a
    source .env
    set +a
    
    # Count variables loaded
    VAR_COUNT=$(grep -c "^[A-Z]" .env 2>/dev/null || echo "0")
    echo -e "${GREEN}✓${NC} Environment variables loaded from .env ($VAR_COUNT variables)"
    
    # Show key variables (without values for security)
    echo "  Key variables set:"
    [ -n "$LLM_CHAT_MODEL_NAME" ] && echo "    • LLM_CHAT_MODEL_NAME"
    [ -n "$REDIS_ENABLED" ] && echo "    • REDIS_ENABLED=$REDIS_ENABLED"
    [ -n "$LANGFUSE_ENABLED" ] && echo "    • LANGFUSE_ENABLED=$LANGFUSE_ENABLED"
    [ -n "$API_URL" ] && echo "    • API_URL"
else
    echo -e "${YELLOW}⚠${NC}  .env file not found"
    echo "  Copy .env.example to .env and configure it"
fi

echo ""

# ============================================
# 4. Check key services
# ============================================
echo "🔍 Checking services..."

# Check Redis
if command -v redis-cli >/dev/null 2>&1; then
    if redis-cli ping >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Redis is running"
    else
        echo -e "${YELLOW}⚠${NC}  Redis not running. Start with: make redis-start"
    fi
else
    echo -e "${YELLOW}⚠${NC}  redis-cli not found (Redis not installed locally)"
fi

# Check Docker
if command -v docker >/dev/null 2>&1; then
    if docker ps >/dev/null 2>&1; then
        RUNNING_CONTAINERS=$(docker ps --format '{{.Names}}' | grep -E "redis|postgres|api" | wc -l | tr -d ' ')
        if [ "$RUNNING_CONTAINERS" -gt 0 ]; then
            echo -e "${GREEN}✓${NC} Docker is running ($RUNNING_CONTAINERS service(s))"
        else
            echo -e "${YELLOW}⚠${NC}  Docker running but no services. Start with: make docker-up"
        fi
    else
        echo -e "${YELLOW}⚠${NC}  Docker not running"
    fi
else
    echo "  Docker not installed"
fi

echo ""

# ============================================
# 5. Summary and next steps
# ============================================
echo "========================================"
echo -e "${GREEN}✓ Development environment ready!${NC}"
echo ""
echo "📝 Quick commands:"
echo "  make dev          - Start UI development server"
echo "  make docker-up    - Start all Docker services"
echo "  make redis-start  - Start Redis only"
echo "  make test         - Run all tests"
echo "  make help         - Show all available commands"
echo ""
echo "🌐 Service URLs:"
echo "  UI:         http://localhost:8002"
echo "  API:        http://localhost:8000"
echo "  pgAdmin:    http://localhost:5555"
echo "  Redis:      localhost:6379"
echo "  PostgreSQL: localhost:8080"
echo ""
echo "📚 Documentation: docs/README.md"
echo ""

# Return to original directory if user was elsewhere
cd - > /dev/null 2>&1 || true
