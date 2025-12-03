#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "=== JARVIS SYSTEM DIAGNOSTICS ==="

# 1. Run Council Verification Script
echo -n "Running Council Verification (verify_council.py)... "
export PYTHONPATH=$PYTHONPATH:/mnt/fast_data/projects/vision_agent
/mnt/fast_data/projects/vision_agent/vision_agent/venv/bin/python3 verify_council.py > /tmp/council_verify.log 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
    echo "--- Log Output ---"
    cat /tmp/council_verify.log
    echo "------------------"
fi

# 2. Check Service Ports
echo -n "Checking Server Port (8000)... "
if lsof -i :8000 > /dev/null; then
    echo -e "${GREEN}ACTIVE${NC}"
else
    echo -e "${RED}INACTIVE${NC} (Server might be down)"
fi

echo -n "Checking Qdrant (6333)... "
if lsof -i :6333 > /dev/null; then
    echo -e "${GREEN}ACTIVE${NC}"
else
    echo -e "${RED}INACTIVE${NC}"
fi

echo -n "Checking Ollama (11434)... "
if lsof -i :11434 > /dev/null; then
    echo -e "${GREEN}ACTIVE${NC}"
else
    echo -e "${RED}INACTIVE${NC}"
fi

echo "=== DIAGNOSTICS COMPLETE ==="
