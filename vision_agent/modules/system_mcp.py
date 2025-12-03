import psutil
import platform
import logging
from typing import List, Dict, Any

class SystemMCP:
    def __init__(self):
        logging.info("🖥️ System MCP initialized")

    def get_system_stats(self) -> str:
        """Get current system statistics (CPU, RAM, Disk)."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            stats = (
                f"System Stats:\n"
                f"- OS: {platform.system()} {platform.release()}\n"
                f"- CPU Usage: {cpu_percent}%\n"
                f"- RAM Usage: {memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)\n"
                f"- Disk Usage: {disk.percent}% ({disk.free // (1024**3)}GB free)\n"
            )
            return stats
        except Exception as e:
            return f"Error getting stats: {e}"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_system_stats",
                "description": "Get current system statistics (CPU, RAM, Disk).",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]

    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if tool_name == "get_system_stats":
            return self.get_system_stats()
        return None
