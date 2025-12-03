import logging
import json
import ollama
from typing import List, Dict, Any

class AutomationAgent:
    def __init__(self, mcp_manager):
        self.mcp_manager = mcp_manager
        self.model = "deepseek-r1:7b"  # Use DeepSeek-R1 for superior reasoning/planning
        self.max_steps = 10

    def run(self, goal: str) -> str:
        """
        Execute a multi-step automation task.
        """
        logging.info(f"🤖 Automation Agent started: {goal}")
        
        history = []
        
        for step_num in range(self.max_steps):
            # 1. Plan / Decide Next Step
            prompt = self._build_prompt(goal, history)
            response = ollama.chat(model=self.model, messages=[{'role': 'user', 'content': prompt}])
            content = response['message']['content']
            
            # 2. Parse Tool Call
            tool_call = self._parse_tool_call(content)
            
            if not tool_call:
                # If no tool call, maybe we are done?
                if "DONE" in content:
                    return content.split("DONE")[-1].strip()
                logging.warning(f"🤖 Automation Agent could not parse tool call: {content}")
                history.append(f"Step {step_num}: Failed to parse tool call. Response: {content}")
                continue
                
            tool_name = tool_call['tool_name']
            args = tool_call['arguments']
            
            logging.info(f"🤖 Automation Step {step_num}: Calling {tool_name}({args})")
            
            # 3. Execute Tool
            try:
                result = self.mcp_manager.execute_tool(tool_name, args)
                history.append(f"Step {step_num}: Called {tool_name} -> Result: {result}")
            except Exception as e:
                history.append(f"Step {step_num}: Called {tool_name} -> Error: {str(e)}")
                
            # Check if goal is met (heuristic or LLM check)
            # For now, we rely on the LLM to output "DONE" in the next turn.

        return "Automation Task Completed (Max Steps Reached)."

    def _build_prompt(self, goal: str, history: List[str]) -> str:
        tools_desc = json.dumps([t['name'] for t in self.mcp_manager.list_tools()])
        history_str = "\n".join(history)
        
        return f"""
        You are an Autonomous Automation Agent.
        GOAL: {goal}
        
        AVAILABLE TOOLS: {tools_desc}
        
        HISTORY:
        {history_str}
        
        INSTRUCTIONS:
        1. Decide the next step to achieve the goal.
        2. Output a JSON object for the tool you want to call.
        3. If you have achieved the goal, output "DONE: [Summary of what you did]".
        
        FORMAT:
        {{
            "tool_name": "name",
            "arguments": {{ "arg": "value" }}
        }}
        
        Output JSON ONLY (or DONE message).
        """

    def _parse_tool_call(self, content: str) -> Dict[str, Any]:
        try:
            # Try to find JSON block
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Find first { and last }
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                json_str = content[start:end+1]
                return json.loads(json_str)
        except Exception as e:
            pass
        return None
