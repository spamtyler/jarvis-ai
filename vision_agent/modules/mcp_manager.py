import json
import subprocess
import logging
import os
import ollama
from vision_agent.modules.filesystem_mcp import FilesystemMCP
from vision_agent.modules.obsidian_mcp import ObsidianMCP
from vision_agent.modules.coding_agent import CodingAgent
from vision_agent.modules.system_repair import SystemRepairAgent

class MCPManager:
    def __init__(self):
        self.servers = {
            "docker": ["/mnt/fast_data/projects/vision_agent/docker_launcher.sh"],
            "brave": ["/mnt/fast_data/projects/vision_agent/brave_search_launcher.sh"],
            "duckduckgo": ["/mnt/fast_data/projects/vision_agent/duckduckgo_launcher.sh"],
            "github": ["/mnt/fast_data/projects/vision_agent/github_launcher.sh"],
            "wikipedia": ["/mnt/fast_data/projects/vision_agent/wikipedia_launcher.sh"],
            "paper_search": ["/mnt/fast_data/projects/vision_agent/paper_search_launcher.sh"],
            "playwright": ["/mnt/fast_data/projects/vision_agent/playwright_launcher.sh"],
            "sqlite": ["/mnt/fast_data/projects/vision_agent/sqlite_launcher.sh"],
            "youtube": ["/mnt/fast_data/projects/vision_agent/youtube_launcher.sh"],
            # "filesystem": REMOVED (Internal)
            # "obsidian": REMOVED (Internal)
        }
        self.tools = []
        self.internal_tools: Dict[str, Callable] = {}
        self.internal_tool_schemas: List[Dict] = []
        
        # Initialize Internal MCPs
        self.fs_mcp = FilesystemMCP()
        self.obsidian_mcp = ObsidianMCP()
        self.coding_agent = CodingAgent(self)
        self.system_repair = SystemRepairAgent(self)
        
        # Register Filesystem Tools
        for tool in self.fs_mcp.get_tools():
            method_name = tool["name"].replace("fs_", "") if tool["name"].startswith("fs_") else tool["name"]
            self.register_tool(tool["name"], self._wrap_mcp_method(getattr(self.fs_mcp, method_name)), tool)

        # Register Obsidian Tools
        for tool in self.obsidian_mcp.get_tools():
            self.register_tool(tool["name"], self._wrap_mcp_method(getattr(self.obsidian_mcp, tool["name"])), tool)
            
        # Register Coding Agent
        self.register_tool(
            "run_coding_task",
            self.coding_agent.run_coding_task,
            {
                "name": "run_coding_task",
                "description": "Delegate a complex coding or software development task to the Council of Agents.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "goal": {"type": "string", "description": "The coding objective."}
                    },
                    "required": ["goal"]
                }
            }
        )

        # Register System Repair Agent
        self.register_tool(
            "run_system_repair",
            self.system_repair.run_repair,
            {
                "name": "run_system_repair",
                "description": "Diagnose and repair system issues (Linux, Network, Packages).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "issue": {"type": "string", "description": "Description of the system issue."}
                    },
                    "required": ["issue"]
                }
            }
        )
        
        # Register Internal Tools
        self.register_tool(
            "synthesize_content",
            self._synthesize_content,
            {
                "name": "synthesize_content",
                "description": "Synthesize raw information into a well-structured summary using an LLM.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "The topic of the research."},
                        "content": {"type": "string", "description": "The raw content to summarize."}
                    },
                    "required": ["topic", "content"]
                }
            }
        )
        
        self.refresh_tools()

    def _wrap_mcp_method(self, method: Callable) -> Callable:
        """Wraps an MCP class method to match the (tool_name, args) signature."""
        def wrapper(tool_name: str, args: Dict[str, Any]) -> Any:
            return method(**args)
        return wrapper

    def _synthesize_content(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Internal tool to synthesize content using Llama 3.1."""
        topic = args.get("topic", "Unknown Topic")
        content = args.get("content", "")
        
        # FIX: Handle list input (common when agent passes multiple search results)
        if isinstance(content, list):
            content = "\n\n".join([str(c) for c in content])
        
        if not content:
            return "Error: No content provided to synthesize."
            
        logging.info(f"🧠 Synthesizing content for topic: {topic}")
        
        try:
            response = ollama.chat(model="llama3.1", messages=[
                {'role': 'system', 'content': f"You are a research assistant. Synthesize the provided content into a comprehensive, well-structured markdown summary about '{topic}'. Focus on clarity, key facts, and actionable insights."},
                {'role': 'user', 'content': content}
            ])
            return response['message']['content']
        except Exception as e:
            return f"Error synthesizing content: {str(e)}"

    def register_tool(self, name: str, handler: Callable, schema: Dict[str, Any]):
        """Register an internal python function as a tool."""
        self.internal_tools[name] = handler
        self.internal_tool_schemas.append(schema)
        logging.info(f"🔌 MCP Manager: Registered internal tool '{name}'")

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return all available tools (external + internal)."""
        return self.tools + self.internal_tool_schemas

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool (either internal or external)."""
        # Check internal first
        if tool_name in self.internal_tools:
            try:
                return self.internal_tools[tool_name](tool_name, arguments)
            except Exception as e:
                return f"Error executing internal tool {tool_name}: {e}"
        
        # Fallback to external
        server = self.get_server_for_tool(tool_name)
        if server:
            # Tool Name Mapping (Internal -> Actual MCP Name)
            # Some MCP servers use generic names like "search" which we rename internally to avoid conflicts
            actual_tool_name = tool_name
            if tool_name == "duckduckgo_search":
                actual_tool_name = "search"
            elif tool_name == "wikipedia_search":
                actual_tool_name = "search"
            
            return self.call_tool(server, actual_tool_name, arguments)
        
        return f"Error: Tool '{tool_name}' not found."

    def refresh_tools(self):
        """
        Connects to all servers and fetches their tool definitions.
        (Simplified: We just hardcode the known tools for now to avoid async complexity in this synchronous agent, 
         or we could implement a quick 'list_tools' call via subprocess).
        """
        # For this v1 implementation, we will define the tools we KNOW exist because
        # implementing a full async JSON-RPC client in this synchronous codebase is complex.
        # Ideally, we would query the servers.
        
        self.tools = [
            # Docker Tools
            {
                "name": "list_containers",
                "description": "List all docker containers. Returns JSON.",
                "parameters": {"type": "object", "properties": {"all": {"type": "boolean"}}}
            },
            {
                "name": "inspect_container",
                "description": "Get detailed info about a container.",
                "parameters": {"type": "object", "properties": {"container_id": {"type": "string"}}, "required": ["container_id"]}
            },
            {
                "name": "get_logs",
                "description": "Get logs from a container.",
                "parameters": {"type": "object", "properties": {"container_id": {"type": "string"}, "tail": {"type": "integer"}}, "required": ["container_id"]}
            },
            # Brave Tools
            {
                "name": "brave_web_search",
                "description": "Search the internet for information.",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
            },
            # DuckDuckGo Tools
            {
                "name": "duckduckgo_search",
                "description": "Search the web using DuckDuckGo (privacy-focused).",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
            },
            # Wikipedia Tools
            {
                "name": "wikipedia_search",
                "description": "Search Wikipedia for factual information.",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
            },
            # Paper Search Tools (ArXiv, PubMed, etc.)
            {
                "name": "search_papers",
                "description": "Search academic papers from ArXiv, PubMed, and other sources.",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
            },
             # GitHub Tools
            {
                "name": "search_repositories",
                "description": "Search for GitHub repositories.",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
            },
            # YouTube Tools
            {
                "name": "get_transcript",
                "description": "Get the transcript of a YouTube video.",
                "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}
            },
            # Playwright Tools (Web Automation)
            {
                "name": "playwright_navigate",
                "description": "Navigate to a URL in a browser.",
                "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}
            },
            {
                "name": "playwright_screenshot",
                "description": "Take a screenshot of the current page.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "playwright_get_content",
                "description": "Get the text content of the current page.",
                "parameters": {"type": "object", "properties": {}}
            },
            # SQL Tools (Natural Language Database Queries)
            {
                "name": "query_database",
                "description": "Execute SQL queries on SQLite databases using natural language.",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
            },
            {
                "name": "create_table",
                "description": "Create a new table in the database.",
                "parameters": {"type": "object", "properties": {"table_name": {"type": "string"}, "schema": {"type": "string"}}, "required": ["table_name", "schema"]}
            },
            # Obsidian Tools
            {
                "name": "create_note",
                "description": "Create a new note in Obsidian.",
                "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}, "folder": {"type": "string"}}, "required": ["title", "content"]}
            },
            {
                "name": "read_note",
                "description": "Read a note from Obsidian.",
                "parameters": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}
            },
            {
                "name": "search_notes",
                "description": "Search for notes in Obsidian.",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
            },
            {
                "name": "append_to_note",
                "description": "Append content to an existing note.",
                "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}}, "required": ["title", "content"]}
            },
            {
                "name": "delete_note",
                "description": "Delete a note from Obsidian.",
                "parameters": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}
            }
        ]
        logging.info(f"🔌 MCP Manager: Loaded {len(self.tools)} external tools.")

    def call_tool(self, server_name, tool_name, arguments):
        """
        Executes a tool on the specified server using a temporary subprocess.
        Note: This is a 'stateless' call. Long-lived sessions would require keeping the process open.
        """
        command = self.servers.get(server_name)
        if not command:
            return f"Error: Server '{server_name}' not configured."

        logging.info(f"🔌 MCP Call: {server_name} -> {tool_name}({arguments})")
        
        # FAILSAFE: Ensure create_note has a title
        if tool_name == "create_note" and isinstance(arguments, dict):
            if not arguments.get("title"):
                import time
                content = arguments.get("content", "")
                if content:
                    # Use first 5 words
                    fallback = " ".join(content.split()[:5])
                    fallback = "".join([c for c in fallback if c.isalnum() or c == " "]).strip()
                    arguments["title"] = fallback
                else:
                    arguments["title"] = f"Untitled Note {int(time.time())}"
                logging.warning(f"🛡️ MCP Manager: Auto-generated title '{arguments['title']}'")
            
            if "content" not in arguments:
                arguments["content"] = ""
                logging.warning("🛡️ MCP Manager: Auto-filled empty content")
        
        # We need to construct a JSON-RPC request
        # Since we are using 'docker run', we can't easily keep the connection open in this simple implementation.
        # However, MCP servers usually expect an 'initialize' handshake.
        # A full client is complex. 
        
        # ALTERNATIVE: Use 'claude code' as a subprocess? No, that requires auth.
        
        # Let's try to run a simple python script that uses the 'mcp' library to make ONE call.
        # We can generate a temporary script to execute the call.
        
        try:
            # Create a temp script to run the tool
            script_content = f"""
import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    server_params = StdioServerParameters(
        command="{command[0]}",
        args=[],
        env=os.environ
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("{tool_name}", {arguments})
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(run())
"""
            temp_script = "/tmp/mcp_call.py"
            with open(temp_script, "w") as f:
                f.write(script_content)
                
            # Run it
            # Capture ONLY stdout to get the clean JSON result.
            # Stderr will contain logs from the server/docker, which we don't want in the result.
            process = subprocess.run(["python3", temp_script], capture_output=True, text=True, check=True)
            return process.stdout
            
        except subprocess.CalledProcessError as e:
            error_output = e.stderr # Capture stderr for the error message
            logging.error(f"❌ Tool Execution Failed: {error_output}")
            return f"Tool Execution Failed: {error_output}"
        except Exception as e:
            logging.error(f"❌ MCP Error: {e}")
            return f"Error: {e}"

    def get_server_for_tool(self, tool_name):
        # Map tools to servers (Simple mapping for now)
        if "container" in tool_name or "docker" in tool_name: return "docker"
        if "brave" in tool_name: return "brave"
        if "duckduckgo" in tool_name: return "duckduckgo"
        if "wikipedia" in tool_name: return "wikipedia"
        if "paper" in tool_name: return "paper_search"
        if "playwright" in tool_name: return "playwright"
        if "database" in tool_name or "sql" in tool_name or "table" in tool_name: return "sqlite"
        if "github" in tool_name or "repo" in tool_name: return "github"
        if "file" in tool_name: return "filesystem"
        if "transcript" in tool_name or "youtube" in tool_name: return "youtube"
        if "note" in tool_name or "obsidian" in tool_name: return "obsidian"
        return None
