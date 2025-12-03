# Jarvis Development Guide

## Quick Reference

### Project Location
- **Main Project:** `/mnt/fast_data/projects/vision_agent`
- **Virtual Environment:** `/mnt/fast_data/projects/vision_agent/vision_agent/venv`
- **Workspace:** `/home/soup/jarvis_workspace`

### Essential Commands

```bash
# Start Jarvis
cd /mnt/fast_data/projects/vision_agent
./run_agent.sh

# Manual start (if run_agent.sh fails)
cd /mnt/fast_data/projects/vision_agent
export PYTHONPATH=$PYTHONPATH:.
vision_agent/venv/bin/python3 -m vision_agent.main

# Run Tests
./run_tests.sh

# Start Web Server (Mobile UI)
cd /mnt/fast_data/projects/vision_agent
vision_agent/venv/bin/python3 server.py

# Check Services
docker ps                    # Check Docker containers
ollama list                  # Check Ollama models
lsof -i :8000               # Check web server
lsof -i :11434              # Check Ollama
lsof -i :6333               # Check Qdrant
```

## Recent Changes (Council Round 2)

### 1. Security Enhancements (Gamma)
- **File:** `run_agent.sh`
- **Changes:** Added `chmod 700` for workspace, `chmod 600` for SSL certs
- **Purpose:** Enforce strict permissions

### 2. Testing Infrastructure (Beta)
- **File:** `run_tests.sh`
- **Changes:** New unified test runner
- **Usage:** `./run_tests.sh` to verify all systems

### 3. System Statistics (Iota)
- **File:** `vision_agent/modules/system_mcp.py` (NEW)
- **Changes:** Added `get_system_stats` tool using `psutil`
- **Usage:** Ask Jarvis "What is your CPU usage?"

### 4. Documentation (Eta)
- **File:** `README.md`
- **Changes:** Complete rewrite with new Automation capabilities

### 5. Tool Routing Fix (Previous Session)
- **File:** `vision_agent/interactive_agent.py`
- **Changes:** Switched from manual `get_server_for_tool` to unified `execute_tool`
- **Impact:** Fixed `fs_read_file` routing to internal handler

### 6. Filesystem Path Resolution (Previous Session)
- **File:** `vision_agent/modules/filesystem_mcp.py`
- **Changes:** Improved `_get_safe_path` to check workspace first, then read-only paths
- **Impact:** Jarvis can now read his own source code

## How to Continue Development

### Adding a New MCP Tool

1. **Create the tool module:**
   ```bash
   cd /mnt/fast_data/projects/vision_agent/vision_agent/modules
   touch my_new_mcp.py
   ```

2. **Implement the tool:** (Example)
   ```python
   import logging
   from typing import List, Dict, Any

   class MyNewMCP:
       def __init__(self):
           logging.info("🔧 MyNew MCP initialized")

       def my_action(self, param: str) -> str:
           """Do something useful."""
           return f"Result: {param}"

       def get_tools(self) -> List[Dict[str, Any]]:
           return [
               {
                   "name": "my_action",
                   "description": "Does something useful",
                   "parameters": {
                       "type": "object",
                       "properties": {
                           "param": {"type": "string"}
                       },
                       "required": ["param"]
                   }
               }
           ]

       def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
           if tool_name == "my_action":
               return self.my_action(arguments.get("param"))
           return None
   ```

3. **Register it in `interactive_agent.py`:**
   ```python
   # Import at top
   from vision_agent.modules.my_new_mcp import MyNewMCP

   # In __init__ (around line 155)
   self.my_new_mcp = MyNewMCP()
   for tool in self.my_new_mcp.get_tools():
       self.mcp_manager.register_tool(tool["name"], self.my_new_mcp.handle_tool_call, tool)
   ```

4. **Update Intent Parser prompt** (`vision_agent/modules/intent_parser.py`, line ~160):
   ```python
   # Add to AVAILABLE TOOLS list
   # - my_action(param)  <-- Brief description
   ```

5. **Test it:**
   ```bash
   ./run_agent.sh
   # Then ask: "Jarvis, run my action with test"
   ```

### Debugging Tips

1. **Check Logs:**
   - Jarvis prints colorful logs to stdout
   - Look for `❌` (errors), `⚠️` (warnings), `✅` (success)

2. **Common Issues:**
   - **Import Errors:** Make sure `PYTHONPATH` includes project root
   - **Tool Not Found:** Check `mcp_manager.internal_tools` has your tool
   - **Indentation Errors:** Python is strict about spacing

3. **Test Tools Independently:**
   ```bash
   cd /mnt/fast_data/projects/vision_agent
   export PYTHONPATH=$PYTHONPATH:.
   vision_agent/venv/bin/python3
   >>> from vision_agent.modules.system_mcp import SystemMCP
   >>> mcp = SystemMCP()
   >>> print(mcp.get_system_stats())
   ```

### Git Workflow

```bash
cd /mnt/fast_data/projects/vision_agent

# Check status
git status

# Stage changes
git add vision_agent/modules/my_new_mcp.py
git add vision_agent/interactive_agent.py

# Commit
git commit -m "Add MyNewMCP tool for X feature"

# Push (if you have a remote)
git push origin main
```

## Architecture Overview

```
User Input (Voice/Text)
    ↓
Intent Parser (LLM: Phi-3 or LLaMA 3.1)
    ↓
Interactive Agent
    ↓
├─→ Home Automation Module (if home control)
├─→ MCP Manager (if tool call)
│       ↓
│   ├─→ Internal Tools (Python)
│   │   ├─→ FilesystemMCP
│   │   ├─→ SystemMCP
│   │   └─→ AutomationAgent
│   │
│   └─→ External Tools (Docker/MCP)
│       ├─→ Obsidian
│       ├─→ YouTube
│       └─→ Brave Search
│
└─→ Direct Execution (System commands, chat)
```

## Next Steps (TODO)

1. **UI Polish:** Update `static/index.html` with pulsing "Thinking" animation
2. **Performance:** Review imports in `server.py` for lazy loading
3. **Features:**
   - Add SQLite MCP for database queries
   - Implement task scheduling (cron-like)
   - Add macro recording/playback
4. **Documentation:** Add inline comments to complex functions

## Contact & Support

- **GitHub Issues:** (if public repo)
- **Local Development:** You're on your own now! But you have all the tools. 🚀

---

**Last Updated:** 2025-12-03 (Council Round 2)
