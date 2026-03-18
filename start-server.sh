#!/bin/bash
# RealtyIQ Server Startup Script
# This script safely starts the development server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Starting RealtyIQ Development Server"
echo ""

# Check if port 8002 is already in use
if lsof -Pi :8002 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Port 8002 is already in use${NC}"
    echo ""
    echo "Options:"
    echo "  1) Stop the existing server and start a new one"
    echo "  2) Keep the existing server running"
    echo "  3) Cancel"
    echo ""
    read -p "Enter choice [1-3]: " choice
    
    case $choice in
        1)
            echo ""
            echo "Stopping existing server..."
            lsof -ti:8002 | xargs kill -9 2>/dev/null || true
            sleep 1
            echo -e "${GREEN}✅ Stopped existing server${NC}"
            echo ""
            ;;
        2)
            echo ""
            echo -e "${GREEN}✅ Server is already running on http://localhost:8002${NC}"
            exit 0
            ;;
        *)
            echo ""
            echo "Cancelled"
            exit 0
            ;;
    esac
fi

# Delete old log files
rm ./logs/*log

# Start the server
echo "Starting server..."
echo ""
cd "$(dirname "$0")"
make dev-ui
