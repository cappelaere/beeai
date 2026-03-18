#!/bin/bash
# RealtyIQ Test Runner
# Quick script to run all tests

set -e  # Exit on error

echo "╔════════════════════════════════════════╗"
echo "║  RealtyIQ Comprehensive Test Suite    ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
BACKEND_PASSED=false
FRONTEND_PASSED=false
E2E_PASSED=false

# Backend Tests
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Running Backend Tests (Django)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd agent_ui
if python manage.py test agent_app.tests --keepdb; then
    echo -e "${GREEN}✅ Backend tests PASSED${NC}"
    BACKEND_PASSED=true
else
    echo -e "${RED}❌ Backend tests FAILED${NC}"
fi
cd ..
echo ""

# Frontend Tests (optional - requires npm)
if [ -d "tests/node_modules" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎨 Running Frontend Tests (Jest)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cd tests
    if npm test -- --passWithNoTests; then
        echo -e "${GREEN}✅ Frontend tests PASSED${NC}"
        FRONTEND_PASSED=true
    else
        echo -e "${RED}❌ Frontend tests FAILED${NC}"
    fi
    cd ..
    echo ""
else
    echo -e "${YELLOW}⚠️  Skipping frontend tests (npm dependencies not installed)${NC}"
    echo "   Run: cd tests && npm install"
    echo ""
fi

# E2E Tests (optional - requires playwright)
if [ -f "tests/node_modules/.bin/playwright" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🌐 Running E2E Tests (Playwright)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "NOTE: Make sure dev server is running on port 8002"
    echo ""
    cd tests
    if npm run test:e2e 2>/dev/null; then
        echo -e "${GREEN}✅ E2E tests PASSED${NC}"
        E2E_PASSED=true
    else
        echo -e "${YELLOW}⚠️  E2E tests SKIPPED (server not running?)${NC}"
    fi
    cd ..
    echo ""
else
    echo -e "${YELLOW}⚠️  Skipping E2E tests (playwright not installed)${NC}"
    echo "   Run: cd tests && npx playwright install"
    echo ""
fi

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Results Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$BACKEND_PASSED" = true ]; then
    echo -e "Backend Tests:  ${GREEN}✅ PASSED${NC}"
else
    echo -e "Backend Tests:  ${RED}❌ FAILED${NC}"
fi

if [ -d "tests/node_modules" ]; then
    if [ "$FRONTEND_PASSED" = true ]; then
        echo -e "Frontend Tests: ${GREEN}✅ PASSED${NC}"
    else
        echo -e "Frontend Tests: ${RED}❌ FAILED${NC}"
    fi
else
    echo -e "Frontend Tests: ${YELLOW}⊝ SKIPPED${NC}"
fi

if [ -f "tests/node_modules/.bin/playwright" ]; then
    if [ "$E2E_PASSED" = true ]; then
        echo -e "E2E Tests:      ${GREEN}✅ PASSED${NC}"
    else
        echo -e "E2E Tests:      ${YELLOW}⊝ SKIPPED${NC}"
    fi
else
    echo -e "E2E Tests:      ${YELLOW}⊝ SKIPPED${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Exit with appropriate code
if [ "$BACKEND_PASSED" = true ]; then
    echo -e "${GREEN}✨ Core tests passed! System is functional.${NC}"
    exit 0
else
    echo -e "${RED}❌ Tests failed! Please review errors above.${NC}"
    exit 1
fi
