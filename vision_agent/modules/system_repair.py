import logging
import ollama
import subprocess
import json
from typing import Dict, Any, List

class SystemRepairAgent:
    def __init__(self, mcp_manager):
        self.mcp_manager = mcp_manager
        self.model = "deepseek-r1:7b" # Reasoning model for diagnosis
        
    def run_repair(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        Diagnoses and proposes fixes for system issues.
        Args:
            issue (str): The user's description of the problem.
        """
        issue = args.get("issue", "")
        if not issue:
            return "Error: No issue description provided."
            
        logging.info(f"🛠️ System Repair Agent started: {issue}")
        print(f"🛠️ System Repair Agent: Diagnosing '{issue}'...")

        # 1. Gather Context (Safe Read-Only Commands)
        context = self._gather_context(issue)
        
        # 2. Diagnose & Plan
        plan = self._diagnose_and_plan(issue, context)
        
        # 3. User Confirmation (CRITICAL SAFETY STEP)
        # Since we are in a tool call, we can't interactively ask the user easily *mid-tool* 
        # without breaking the flow or using a special callback.
        # For now, we will RETURN the plan and ask the user to confirm by running a specific command 
        # OR we can just return the plan and say "To execute this, say 'Run command X'".
        # BUT, the user wants "Self Healing".
        # A better approach for "Self Healing" with safety:
        # Return the plan and the EXACT commands to run.
        
        return f"### 🩺 Diagnosis & Repair Plan\n\n{plan}\n\n**⚠️ SAFETY CHECK**: Review the commands above. If you agree, say 'Run command...'"

    def _gather_context(self, issue: str) -> str:
        """Runs safe diagnostic commands based on keywords."""
        context = []
        
        # Always check basic stats
        try:
            uptime = subprocess.check_output("uptime", shell=True).decode()
            context.append(f"Uptime: {uptime.strip()}")
        except: pass

        if "disk" in issue or "space" in issue:
            try:
                df = subprocess.check_output("df -h", shell=True).decode()
                context.append(f"Disk Usage:\n{df}")
            except: pass
            
        if "network" in issue or "internet" in issue or "wifi" in issue:
            try:
                ip = subprocess.check_output("ip a", shell=True).decode()
                ping = subprocess.check_output("ping -c 1 8.8.8.8", shell=True).decode()
                context.append(f"Network:\n{ip}\nPing:\n{ping}")
            except Exception as e:
                context.append(f"Network Error: {str(e)}")

        if "package" in issue or "install" in issue or "apt" in issue:
            # Check for dpkg locks or broken installs
            try:
                dpkg = subprocess.check_output("sudo fuser -v /var/lib/dpkg/lock-frontend", shell=True).decode()
                context.append(f"DPKG Lock:\n{dpkg}")
            except: 
                context.append("No DPKG lock found (Good).")
                
        return "\n---\n".join(context)

    def _diagnose_and_plan(self, issue: str, context: str) -> str:
        prompt = f"""
        You are THE SURGEON, a Linux System Expert.
        
        USER ISSUE: "{issue}"
        SYSTEM CONTEXT:
        {context}
        
        TASK:
        1. Analyze the issue and context.
        2. Propose a SAFE, step-by-step repair plan.
        3. Provide the EXACT terminal commands to fix it.
        
        WARNING:
        - Be extremely careful with `sudo`.
        - Do NOT suggest `rm -rf /`.
        - Explain WHY each step is needed.
        
        OUTPUT FORMAT:
        Markdown. Use code blocks for commands.
        """
        response = ollama.chat(model=self.model, messages=[{'role': 'user', 'content': prompt}])
        return response['message']['content']
