# 🧠 Jarvis AI - Semantic Home Automation, Desktop & Mobile Assistant

**Jarvis** is a next-generation AI agent that unifies your digital life. He is a **Home Automation Controller**, a **Desktop Assistant**, and a **Mobile Companion**, all powered by local LLMs (Large Language Models).

Unlike traditional voice assistants that rely on rigid keywords, Jarvis uses a **Semantic Intent Parser** to understand context, compound commands, and fuzzy device names across all your devices.

---

## ✨ Key Features

### 🚀 Performance & Speed
- **Hybrid Intelligence:** Combines **Heuristic Matching** (Fuzzy Logic) with **LLMs**.
- **Zero Latency:** Common commands like "Turn on the light" or "Delete note" execute instantly (~0.01s).
- **GPU Acceleration:** Fully optimized for NVIDIA GPUs (RTX 2080 Super+) using CUDA 12.1.
- **Stability & Robustness:**
    - **Generative Notes:** "Create a note about X" automatically generates content using AI.
    - **Shell Safety:** Advanced regex protection prevents accidental shell command execution.
    - **Self-Healing:** Failsafes prevent crashes from missing data or API errors.

### 🖥️ Desktop Assistant
- **Global Access:** Launch from anywhere by running `./run_agent.sh`.
- **System Control:** "Open VS Code", "Launch Chrome", "Turn up the volume".
- **Productivity:** "Type this email for me", "Search the web for..."
- **Local Execution:** Runs entirely on your machine for maximum privacy and speed.

### 📱 Mobile Companion
- **Remote Access:** Control your home and computer from anywhere via **Tailscale**.
- **Voice Interface:** Talk to Jarvis just like a phone call.
- **Responsive Dashboard:** A beautiful, dark-mode UI optimized for mobile devices.

### 🏠 Semantic Home Automation
- **Natural Language Understanding:** "It's too dark in here" -> Turns on the lights.
- **Compound Commands:** "Turn on the kitchen light AND check if the washer is done."
- **Context Awareness:** Distinguishes between "Turn **down** the TV" (Volume) and "Turn **off** the TV" (Power).
- **Auto-Discovery:** Automatically maps all Home Assistant devices on startup.

### 👁️ True Sight (Vision)
- **Visual Awareness:** "Can you see me?" -> Captures webcam image and describes the scene.
- **Screen Analysis:** "Look at my screen" -> Analyzes your desktop content using **LLaVA**.
- **Multi-Modal:** Combines voice commands with visual context for deeper understanding.

### 🛠️ Agentic Capabilities (MCP)
Jarvis uses the **Model Context Protocol (MCP)** to use external tools safely:
- **Obsidian "Second Brain":**
    - "Create a note called Victory"
    - "Read the note called Ideas"
    - "Search notes for AI"
    - "Delete the note called Old Draft"
- **YouTube Transcriber:** "Get the transcript for this video..." (Dockerized)
- **Brave Search:** "Search the web for AI news..." (Dockerized)
- **GitHub Integration:** "Search repositories for Python projects..."
- **Docker Management:** "List all containers", "Get logs from container X"

### 🤖 NEW: Automation Agent & Self-Awareness
Jarvis now has advanced automation and introspection capabilities:
- **Automation Agent:** Delegate multi-step workflows to a specialized planning agent.
    - Example: *"Research the history of AI and write a report to my workspace"*
    - The Automation Agent will: Plan steps → Search the web → Write to file
- **Filesystem Access:** Safe, sandboxed file operations in `/home/soup/jarvis_workspace`.
    - Example: *"List files in my workspace"*, *"Read project_notes.txt"*
- **Self-Review:** Jarvis can **read his own source code** (read-only) to answer questions about his implementation.
    - Example: *"Show me the code for your intent parser"*
- **System Stats:** Query real-time system metrics.
    - Example: *"What is your CPU usage?"*, *"How much RAM are you using?"*

---

## 🏗️ Architecture

### Core Components
- **Intent Parser (LLM):** Qwen 2.5 (7B params) for high-precision intent classification and JSON generation.
- **Memory Bank (RAG):** **ChromaDB** vector database for episodic memory and fact learning.
- **Hybrid Brain:**
    - **Automation Agent:** Specialized DeepSeek-R1 / Llama 3.1 planner for complex research workflows.
    - **Coding Council:** Multi-agent system (Architect + Engineer) for software development.
    - **System Repair (The Surgeon):** Safe, sequential agent for Linux diagnostics and repair.
    - **Vision Expert (The Eye):** Fast, single-shot image analysis using LLaVA.
    - **Memory Archivist (The Librarian):** Background process for organizing the Obsidian Vault.
- **MCP Manager:** Unified tool registry supporting both external (Docker) and **Direct Execution** (Internal) tools.

### MCP Tools
1. **External (Docker-based):**
   - Brave Search, YouTube Transcriber, GitHub Search, Docker Management
2. **Internal (Direct Execution):**
   - **FilesystemMCP:** Safe file operations in sandboxed workspace.
   - **ObsidianMCP:** Instant note creation and retrieval (<0.1s latency).
   - **SystemMCP:** Real-time system statistics.
   - **AutomationAgent:** Multi-step workflow planning.
   - **CodingAgent:** Software development council.
   - **SystemRepairAgent:** Linux diagnostics.

---

## 🚀 Quick Start

### Prerequisites
- **OS:** Ubuntu 20.04+ (or compatible Linux)
- **GPU:** NVIDIA GPU with CUDA 11.5+
- **Python:** 3.10+
- **Ollama:** For local LLM inference
- **Docker:** For MCP tools (optional but recommended)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/jarvis-ai.git
   cd jarvis-ai
   ```

2. **Run the setup script:**
   ```bash
   ./setup.sh
   ```
   This will:
   - Create a Python virtual environment
   - Install all dependencies
   - Download required models (Phi-3, LLaMA 3.1, LLaVA)
   - Configure MCP servers

3. **Start Jarvis:**
   ```bash
   ./run_agent.sh
   ```

4. **Access the Mobile UI (optional):**
   - Start the web server: `cd vision_agent && python server.py`
   - Open your browser: `https://localhost:8000`

---

## 🧪 Testing & Verification

Run the comprehensive test suite:
```bash
./run_tests.sh
```

This will verify:
- Filesystem security and sandboxing
- Tool routing (internal vs external)
- Service health (Ollama, Qdrant, Web Server)

---

## 📡 Remote Access

### Tailscale Setup
1. Install Tailscale: `curl -fsSL https://tailscale.com/install.sh | sh`
2. Authenticate: `sudo tailscale up`
3. Get your Tailscale IP: `tailscale ip -4`
4. Access Jarvis from your phone: `https://<tailscale-ip>:8000`

---

## 🔒 Security

- **Sandboxed Filesystem:** All file operations are restricted to `/home/soup/jarvis_workspace`.
- **Read-Only Source Access:** Jarvis can read his own code but cannot modify it.
- **SSL/TLS:** Self-signed certificates for HTTPS (mobile access).
- **No Cloud Dependencies:** All processing happens locally on your machine.

---

## 🛠️ Development

### Project Structure
```
vision_agent/
├── main.py                 # Entry point
├── interactive_agent.py    # Core agent logic
├── server.py              # FastAPI web server
├── modules/
│   ├── intent_parser.py   # LLM-based intent classification
│   ├── mcp_manager.py     # MCP tool registry
│   ├── filesystem_mcp.py  # File operations
│   ├── system_mcp.py      # System statistics
│   ├── automation_agent.py # Multi-step workflow planner
│   ├── memory_bank.py     # Vector database (Qdrant)
│   └── ...
├── static/
│   └── index.html         # Mobile UI
└── run_agent.sh           # Startup script
```

### Adding New Tools
To add a new MCP tool:
1. Create a new class in `vision_agent/modules/<tool_name>_mcp.py`
2. Implement `get_tools()` and `handle_tool_call()`
3. Register it in `InteractiveAgent.__init__()`:
   ```python
   self.my_mcp = MyMCP()
   for tool in self.my_mcp.get_tools():
       self.mcp_manager.register_tool(tool["name"], self.my_mcp.handle_tool_call, tool)
   ```

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **Ollama** for local LLM inference
- **Qdrant** for vector database
- **Model Context Protocol (MCP)** for tool integration
- **Home Assistant** for smart home control
