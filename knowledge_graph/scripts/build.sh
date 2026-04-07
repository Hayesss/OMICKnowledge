#!/bin/bash
# Build script for knowledge graph
# Usage: ./scripts/build.sh [options]

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
BUILD_GRAPH=true
BUILD_MEMORY=true
VALIDATE=true
TEST=true
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-graph)
            BUILD_GRAPH=false
            shift
            ;;
        --no-memory)
            BUILD_MEMORY=false
            shift
            ;;
        --no-validate)
            VALIDATE=false
            shift
            ;;
        --no-test)
            TEST=false
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --no-graph      Skip building graph JSON"
            echo "  --no-memory     Skip building memory store"
            echo "  --no-validate   Skip validation"
            echo "  --no-test       Skip tests"
            echo "  --verbose, -v   Verbose output"
            echo "  --help, -h      Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "========================================"
echo "  Knowledge Graph Build"
echo "========================================"
echo ""

# Check dependencies
echo -e "${BLUE}Checking dependencies...${NC}"

if ! command -v pixi &> /dev/null; then
    echo -e "${RED}Error: pixi not found${NC}"
    echo "Install from: https://pixi.sh/"
    exit 1
fi

if [ "$VERBOSE" = true ]; then
    echo "  ✓ pixi found"
fi

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pixi install --quiet

# Validation
if [ "$VALIDATE" = true ]; then
    echo ""
    echo -e "${BLUE}Running validation...${NC}"
    if pixi run validate; then
        echo -e "${GREEN}✓ Validation passed${NC}"
    else
        echo -e "${RED}✗ Validation failed${NC}"
        exit 1
    fi
fi

# Tests
if [ "$TEST" = true ]; then
    echo ""
    echo -e "${BLUE}Running tests...${NC}"
    if pixi run test; then
        echo -e "${GREEN}✓ Tests passed${NC}"
    else
        echo -e "${RED}✗ Tests failed${NC}"
        exit 1
    fi
fi

# Build graph
if [ "$BUILD_GRAPH" = true ]; then
    echo ""
    echo -e "${BLUE}Building graph...${NC}"
    if pixi run build; then
        echo -e "${GREEN}✓ Graph built${NC}"
        if [ "$VERBOSE" = true ]; then
            echo "  Output: web/data/graph.json"
            if [ -f "web/data/graph.json" ]; then
                SIZE=$(du -h web/data/graph.json | cut -f1)
                echo "  Size: $SIZE"
            fi
        fi
    else
        echo -e "${RED}✗ Graph build failed${NC}"
        exit 1
    fi
fi

# Build memory store
if [ "$BUILD_MEMORY" = true ]; then
    echo ""
    echo -e "${BLUE}Building memory store...${NC}"
    if pixi run build-memory; then
        echo -e "${GREEN}✓ Memory store built${NC}"
        if [ "$VERBOSE" = true ]; then
            echo "  Output: memory_store/"
            if [ -d "memory_store" ]; then
                ITEMS=$(ls memory_store/items.jsonl 2>/dev/null | wc -l)
                echo "  Items: $ITEMS"
            fi
        fi
    else
        echo -e "${RED}✗ Memory store build failed${NC}"
        exit 1
    fi
fi

# Summary
echo ""
echo "========================================"
echo -e "${GREEN}Build completed successfully!${NC}"
echo "========================================"
echo ""

if [ "$BUILD_GRAPH" = true ] && [ -f "web/data/graph.json" ]; then
    echo -e "${BLUE}Graph visualization:${NC}"
    echo "  File: web/data/graph.json"
    NODES=$(grep -o '"id"' web/data/graph.json | wc -l)
    echo "  Nodes: $NODES"
    echo "  View: http://localhost:8080"
    echo ""
fi

if [ "$BUILD_MEMORY" = true ] && [ -d "memory_store" ]; then
    echo -e "${BLUE}Memory store:${NC}"
    echo "  Directory: memory_store/"
    if [ -f "memory_store/config.json" ]; then
        ITEMS=$(.pixi/envs/default/bin/python -c "import json; print(json.load(open('memory_store/config.json'))['n_items'])" 2>/dev/null || echo "?")
        echo "  Items: $ITEMS"
    fi
    echo "  API: http://localhost:8000"
    echo ""
fi

echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Start API: pixi run serve-memory"
echo "  2. Start web: pixi run serve"
echo "  3. Open WebUI: ./scripts/start_openwebui_stack.sh"
