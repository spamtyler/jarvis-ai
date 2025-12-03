import os
import logging
from typing import List, Dict, Any

class ObsidianMCP:
    def __init__(self, vault_path: str = "/mnt/fast_data/projects/vision_agent/obsidian_vault"):
        self.vault_path = vault_path
        if not os.path.exists(self.vault_path):
            os.makedirs(self.vault_path)
        logging.info(f"📓 Obsidian MCP initialized at {self.vault_path}")

    def create_note(self, title: str, content: str, folder: str = "") -> str:
        """Creates a new note in the Obsidian Vault."""
        try:
            # Sanitize title
            filename = f"{title}.md"
            if not filename.endswith(".md"): filename += ".md"
            
            target_dir = self.vault_path
            if folder:
                target_dir = os.path.join(self.vault_path, folder)
            
            os.makedirs(target_dir, exist_ok=True)
            
            file_path = os.path.join(target_dir, filename)
            
            if os.path.exists(file_path):
                return f"Error: Note '{filename}' already exists."
                
            with open(file_path, "w") as f:
                f.write(content)
                
            return f"Successfully created note: {filename}"
        except Exception as e:
            return f"Error creating note: {str(e)}"

    def read_note(self, title: str) -> str:
        """Reads the content of a note from the Obsidian Vault."""
        try:
            # Simple recursive search
            for root, dirs, files in os.walk(self.vault_path):
                for file in files:
                    if file.lower() == f"{title.lower()}.md" or title.lower() in file.lower():
                        path = os.path.join(root, file)
                        with open(path, "r") as f:
                            return f.read()
                            
            return f"Error: Note '{title}' not found."
        except Exception as e:
            return f"Error reading note: {str(e)}"

    def search_notes(self, query: str) -> str:
        """Searches for notes containing the query string."""
        try:
            results = []
            for root, dirs, files in os.walk(self.vault_path):
                for file in files:
                    if not file.endswith(".md"): continue
                    
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r") as f:
                            content = f.read()
                            if query.lower() in content.lower() or query.lower() in file.lower():
                                results.append(file)
                    except:
                        continue
                        
            if not results:
                return "No notes found matching query."
                
            return f"Found {len(results)} notes:\n" + "\n".join(results[:10])
        except Exception as e:
            return f"Error searching notes: {str(e)}"

    def append_to_note(self, title: str, content: str) -> str:
        """Appends content to an existing note."""
        try:
            # Simple recursive search
            target_path = None
            for root, dirs, files in os.walk(self.vault_path):
                for file in files:
                    if file.lower() == f"{title.lower()}.md":
                        target_path = os.path.join(root, file)
                        break
                if target_path: break
                
            if not target_path:
                return f"Error: Note '{title}' not found."
                
            with open(target_path, "a") as f:
                f.write("\n" + content)
                
            return f"Successfully appended to {title}."
        except Exception as e:
            return f"Error appending to note: {str(e)}"

    def delete_note(self, title: str) -> str:
        """Deletes a note from the Obsidian Vault."""
        try:
            # Simple recursive search
            target_path = None
            for root, dirs, files in os.walk(self.vault_path):
                for file in files:
                    if file.lower() == f"{title.lower()}.md" or title.lower() in file.lower():
                        target_path = os.path.join(root, file)
                        break
                if target_path: break
                
            if not target_path:
                return f"Error: Note '{title}' not found."
                
            os.remove(target_path)
            return f"Successfully deleted note: {os.path.basename(target_path)}"
        except Exception as e:
            return f"Error deleting note: {str(e)}"

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return the list of tools provided by this MCP."""
        return [
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
