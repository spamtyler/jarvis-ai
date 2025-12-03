import os
import logging
from typing import List, Dict, Any

class FilesystemMCP:
    def __init__(self, root_dir: str = "/home/soup/jarvis_workspace"):
        self.root_dir = os.path.abspath(root_dir)
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir)
        logging.info(f"📂 Filesystem MCP initialized at {self.root_dir}")

    def _is_safe_path(self, path: str) -> bool:
        """Ensure path is within the root directory."""
        abs_path = os.path.abspath(os.path.join(self.root_dir, path))
        return abs_path.startswith(self.root_dir)

    def list_files(self, directory: str = ".") -> List[str]:
        """List files in a directory relative to the workspace root."""
        if not self._is_safe_path(directory):
            return ["Error: Access denied. Path outside workspace."]
        
        target_dir = os.path.join(self.root_dir, directory)
        try:
            return os.listdir(target_dir)
        except Exception as e:
            return [f"Error: {str(e)}"]

    def read_file(self, path: str) -> str:
        """Read a file relative to the workspace root."""
        if not self._is_safe_path(path):
            return "Error: Access denied. Path outside workspace."
        
        target_path = os.path.join(self.root_dir, path)
        try:
            with open(target_path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error: {str(e)}"

    def write_file(self, path: str, content: str) -> str:
        """Write content to a file relative to the workspace root."""
        if not self._is_safe_path(path):
            return "Error: Access denied. Path outside workspace."
        
        target_path = os.path.join(self.root_dir, path)
        try:
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, 'w') as f:
                f.write(content)
            return f"Success: Written to {path}"
        except Exception as e:
            return f"Error: {str(e)}"

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return the list of tools provided by this MCP."""
        return [
            {
                "name": "fs_list_files",
                "description": "List files in the Jarvis Workspace. Args: directory (default '.')",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "description": "Sub-directory to list"}
                    },
                    "required": []
                }
            },
            {
                "name": "fs_read_file",
                "description": "Read a file from the Jarvis Workspace. Args: path",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Relative path to file"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "fs_write_file",
                "description": "Write content to a file in the Jarvis Workspace. Args: path, content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Relative path to file"},
                        "content": {"type": "string", "description": "Content to write"}
                    },
                    "required": ["path", "content"]
                }
            }
        ]

    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Dispatch tool calls."""
        if tool_name == "fs_list_files":
            return self.list_files(arguments.get("directory", "."))
        elif tool_name == "fs_read_file":
            return self.read_file(arguments.get("path"))
        elif tool_name == "fs_write_file":
            return self.write_file(arguments.get("path"), arguments.get("content"))
        return None
