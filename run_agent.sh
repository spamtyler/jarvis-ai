#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "   ___  __   __  ___  __   __  ___  "
echo "  |   ||  | |  ||   ||  | |  ||   | "
echo "  |   ||  |_|  ||   ||  |_|  ||   | "
echo "  |   ||       ||   ||       ||   | "
echo "  |   ||       ||   ||       ||   | "
echo "  |___||_| |_| |___||_| |_| |___| "
echo "     J  A  R  V  I  S   A  I      "
echo -e "${NC}"

PROJECT_ROOT="/mnt/fast_data/projects/vision_agent"
VENV_PATH="$PROJECT_ROOT/vision_agent/venv"
WORKSPACE="/home/soup/jarvis_workspace"

echo -e "${YELLOW}[*] Performing System Checks...${NC}"

# 1. Check Root Directory
if [ ! -d "$PROJECT_ROOT" ]; then
    echo -e "${RED}[!] Error: Project root not found at $PROJECT_ROOT${NC}"
    exit 1
fi

# 2. Check Virtual Environment
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}[!] Error: Virtual environment not found at $VENV_PATH${NC}"
    echo "    Please run setup.sh first."
    exit 1
fi

# 3. Check Ollama
if ! pgrep -x "ollama" > /dev/null; then
    echo -e "${YELLOW}[!] Warning: Ollama is not running.${NC}"
    echo "    Starting Ollama..."
    ollama serve > /dev/null 2>&1 &
    sleep 2
fi

# 4. Security Enforcement (Gamma Protocol)
echo -e "${YELLOW}[*] Enforcing Security Protocols...${NC}"

# Workspace Permissions (700 - Only User)
if [ ! -d "$WORKSPACE" ]; then
    mkdir -p "$WORKSPACE"
fi
chmod 700 "$WORKSPACE"
echo -e "${GREEN}[+] Workspace permissions secured ($WORKSPACE).${NC}"

# SSL Cert Permissions (600 - Read/Write User Only)
if [ -f "cert.pem" ]; then
    chmod 600 cert.pem
    chmod 600 key.pem
    echo -e "${GREEN}[+] SSL Certificate permissions secured.${NC}"
fi

# 5. Launch Agent
echo -e "${BLUE}[*] Launching Jarvis...${NC}"
cd "$PROJECT_ROOT" || exit
export PYTHONPATH=$PYTHONPATH:.
"$VENV_PATH/bin/python3" -m vision_agent.main
