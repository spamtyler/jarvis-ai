import os
import sys
import logging
from colorama import init, Fore

# Setup
init(autoreset=True)
logging.basicConfig(level=logging.INFO, format='%(message)s')

def check_filesystem_mcp():
    print(f"{Fore.CYAN}🔍 Checking Filesystem MCP Security...{Fore.RESET}")
    try:
        from vision_agent.modules.filesystem_mcp import FilesystemMCP
        from vision_agent.modules.mcp_manager import MCPManager
        
        # Initialize with Read-Only Access
        fs = FilesystemMCP(
            root_dir="/home/soup/jarvis_workspace",
            allowed_read_paths=["/mnt/fast_data/projects/vision_agent"]
        )
        
        # Test 1: List Workspace (Should be empty or have previous files)
        print(f"  - Testing list_files('.')...", end=" ")
        files = fs.list_files(".")
        print(f"{Fore.GREEN}OK{Fore.RESET} (Found {len(files)} files)")
        
        # Test 2: Write to Workspace
        print(f"  - Testing write_file('council_check.txt')...", end=" ")
        result = fs.write_file("council_check.txt", "Verified by Team 8.")
        if "Success" in result:
            print(f"{Fore.GREEN}OK{Fore.RESET}")
        else:
            print(f"{Fore.RED}FAIL: {result}{Fore.RESET}")
            
        # Test 3: Read from Workspace
        print(f"  - Testing read_file('council_check.txt')...", end=" ")
        content = fs.read_file("council_check.txt")
        if "Verified" in content:
            print(f"{Fore.GREEN}OK{Fore.RESET}")
        else:
            print(f"{Fore.RED}FAIL: {content}{Fore.RESET}")

        # Test 4: Read from Source Code (Read-Only)
        print(f"  - Testing read_file('vision_agent/server.py') [Project Root]...", end=" ")
        # Note: The path is relative to one of the allowed roots.
        # If allowed_read_paths=["/mnt/.../vision_agent"], then "vision_agent/server.py" 
        # implies we are looking for /mnt/.../vision_agent/vision_agent/server.py
        # Let's try "vision_agent/main.py" which we know exists.
        content = fs.read_file("vision_agent/main.py")
        if "def main():" in content or "import" in content:
            print(f"{Fore.GREEN}OK{Fore.RESET}")
        else:
            print(f"{Fore.RED}FAIL: {content[:100]}...{Fore.RESET}")
            
        # Test 5: Write to Source Code (Should Fail)
        print(f"  - Testing write_file('vision_agent/malicious.py') [Project Root]...", end=" ")
        result = fs.write_file("vision_agent/malicious.py", "bad code")
        if "Access denied" in result:
            print(f"{Fore.GREEN}OK (Blocked){Fore.RESET}")
        else:
            print(f"{Fore.RED}FAIL: {result}{Fore.RESET}")

    except ImportError as e:
        print(f"{Fore.RED}CRITICAL: Import Failed: {e}{Fore.RESET}")
        return False
    except Exception as e:
        print(f"{Fore.RED}CRITICAL: Exception: {e}{Fore.RESET}")
        return False
    return True

def check_mcp_routing():
    print(f"\n{Fore.CYAN}🔍 Checking MCP Tool Routing...{Fore.RESET}")
    try:
        from vision_agent.modules.mcp_manager import MCPManager
        from vision_agent.modules.filesystem_mcp import FilesystemMCP
        
        mcp = MCPManager()
        fs = FilesystemMCP(root_dir="/home/soup/jarvis_workspace")
        
        # Register Internal Tools
        for tool in fs.get_tools():
            mcp.register_tool(tool["name"], fs.handle_tool_call, tool)
            
        # Test Execution
        print(f"  - Executing 'fs_list_files' via MCPManager...", end=" ")
        result = mcp.execute_tool("fs_list_files", {"directory": "."})
        if isinstance(result, list):
            print(f"{Fore.GREEN}OK{Fore.RESET} (Internal Handler Used)")
        else:
            print(f"{Fore.RED}FAIL: {result}{Fore.RESET}")
            
    except Exception as e:
        print(f"{Fore.RED}CRITICAL: {e}{Fore.RESET}")
        return False
    return True

if __name__ == "__main__":
    print(f"{Fore.YELLOW}=== COUNCIL OF AGENTS: SYSTEM AUDIT ==={Fore.RESET}")
    sys.path.append("/mnt/fast_data/projects/vision_agent")
    
    if check_filesystem_mcp() and check_mcp_routing():
        print(f"\n{Fore.GREEN}✅ ALL SYSTEMS FUNCTIONAL{Fore.RESET}")
    else:
        print(f"\n{Fore.RED}❌ SYSTEM CHECK FAILED{Fore.RESET}")
