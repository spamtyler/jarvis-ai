import logging
import json
import ollama
from typing import List, Dict, Any

class AutomationAgent:
    def __init__(self, mcp_manager):
        self.mcp_manager = mcp_manager
        self.model = "llama3.1"  # Revert to Smart Brain (Simpler, more grounded)
        self.max_steps = 7  # Increased to 7 to accommodate 3 searches + synthesis + save

    def run(self, goal: str) -> str:
        """
        Execute a multi-step automation task.
        """
        logging.info(f"🤖 Automation Agent started: {goal}")
        print(f"🤖 Automation Agent started: {goal}")
        
        history = []
        
        for step_num in range(self.max_steps):
            print(f"⏳ Step {step_num + 1}/{self.max_steps}: Thinking...")
            # 1. Plan / Decide Next Step
            prompt = self._build_prompt(goal, history)
            response = ollama.chat(model=self.model, messages=[{'role': 'user', 'content': prompt}])
            content = response['message']['content']
            
            # 2. Parse Tool Call
            tool_call = self._parse_tool_call(content)
            
            if not tool_call:
                # If no tool call, maybe we are done?
                if "DONE" in content:
                    result = content.split("DONE")[-1].strip()
                    print(f"✅ Automation Complete: {result}")
                    return result
                logging.warning(f"🤖 Automation Agent could not parse tool call: {content}")
                history.append(f"Step {step_num}: Failed to parse tool call. Response: {content}")
                continue
                
            tool_name = tool_call['tool_name']
            args = tool_call['arguments']
            
            logging.info(f"🤖 Automation Step {step_num}: Calling {tool_name}({args})")
            print(f"🛠️ Executing: {tool_name}...")
            
            
            # 3. Execute Tool
            try:
                result = self.mcp_manager.execute_tool(tool_name, args)
                # Truncate result in history to prevent context overflow, but keep enough for reasoning
                # INCREASED to 3000 to ensure search results aren't cut off too early
                truncated_result = result[:3000] + "..." if len(result) > 3000 else result
                history.append(f"Step {step_num}: Called {tool_name} -> Result: {truncated_result}")
                
                # HEURISTIC: If we just created a note successfully, we are likely done.
                if tool_name == "create_note" and "Successfully created note" in result:
                    print(f"✅ Auto-detect: Note created. Finishing task.")
                    return f"Task Completed. {result}"
                    
            except Exception as e:
                history.append(f"Step {step_num}: Called {tool_name} -> Error: {str(e)}")
                
            # Check if goal is met (heuristic or LLM check)
            # For now, we rely on the LLM to output "DONE" in the next turn.

        last_step = history[-1] if history else "No steps executed."
        return f"Automation Task Completed (Max Steps Reached). Last Action: {last_step}"

    def _build_prompt(self, goal: str, history: List[str]) -> str:
        # Get all tools first
        all_tools = self.mcp_manager.list_tools()
        
        # Check history for completed steps
        has_ddg = any("duckduckgo_search" in h for h in history)
        has_brave = any("brave_web_search" in h for h in history)
        has_wiki = any("wikipedia_search" in h for h in history)
        has_synthesis = any("synthesize_content" in h for h in history)
        
        # TOOL MASKING: Filter out tools that have already been used successfully
        # This forces the agent to move forward and prevents loops.
        available_tools = []
        for tool in all_tools:
            name = tool['name']
            if name == "duckduckgo_search" and has_ddg: continue
            if name == "brave_web_search" and has_brave: continue
            if name == "wikipedia_search" and has_wiki: continue
            if name == "synthesize_content" and has_synthesis: continue
            available_tools.append(tool)
            
        tools_desc = json.dumps(available_tools, indent=2)
        history_str = "\n".join(history)
        
        # Dynamic Instructions based on state
        state_instruction = ""
        
        if not has_ddg:
            state_instruction = "STATE: STEP 1 (RESEARCH). You MUST start by using 'duckduckgo_search' to find initial information."
        elif not has_brave:
            state_instruction = "STATE: STEP 2 (RESEARCH). You MUST now use 'brave_web_search' to find additional perspectives."
        elif not has_wiki:
            state_instruction = "STATE: STEP 3 (FACT CHECK). You MUST now use 'wikipedia_search' to verify facts."
        elif not has_synthesis:
            state_instruction = "STATE: STEP 4 (SYNTHESIZE). You have enough info. You MUST now use 'synthesize_content' to summarize."
        else:
            state_instruction = "STATE: STEP 5 (SAVE). You MUST now use 'create_note' to save the synthesized content. Do NOT search again."
            
        # Anti-Loop Enforcement
        if len(history) > 4:
            state_instruction += " WARNING: You are taking too many steps. FINISH NOW."

        prompt = f"""
        You are the **Automation Agent**, a specialized research planner.
        
        GOAL: "{goal}"
        
        TOOLS AVAILABLE:
        {tools_desc}
        
        HISTORY:
        {history_str}
        
        {state_instruction}
        
        
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
                
                # FIX: Sanitize JSON string to handle unescaped newlines in values
                # This regex looks for newlines that are NOT followed by a quote or closing brace/bracket, roughly
                # A safer approach for simple LLM output is to replace literal newlines inside strings with \n
                # But doing that with regex is tricky.
                # Simpler approach: Use strict=False if possible, but json.loads doesn't support it fully.
                # Let's try to escape control characters.
                
                try:
                    return json.loads(json_str, strict=False)
                except json.JSONDecodeError:
                    # Fallback: Try to escape newlines in string values
                    # This is a heuristic: replace newlines with \n if they look like they are inside a string
                    import re
                    # Replace literal newlines with \n
                    sanitized_str = re.sub(r'\n', '\\n', json_str)
                    return json.loads(sanitized_str, strict=False)
                    
        except Exception as e:
            logging.warning(f"JSON Parse Error: {e}")
            pass
        return None
