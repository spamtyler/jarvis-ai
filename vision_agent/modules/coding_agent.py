import logging
import ollama
import json
import re
from typing import Dict, Any, List

class CodingAgent:
    def __init__(self, mcp_manager):
        self.mcp_manager = mcp_manager
        self.model = "llama3.1"  # Can switch to deepseek-r1:7b for reasoning
        self.max_steps = 10

    def run_coding_task(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        Executes a complex coding task using the Council of Agents.
        Args:
            goal (str): The coding objective (e.g., "Create a snake game").
        """
        goal = args.get("goal", "")
        if not goal:
            return "Error: No goal provided for coding task."

        logging.info(f"👨‍💻 Coding Council Assembled: {goal}")
        
        # 1. The Architect (Planning)
        plan = self._consult_architect(goal)
        logging.info(f"📐 Architect's Plan:\n{plan}")
        
        # 2. The Engineer (Implementation)
        code_files = self._consult_engineer(goal, plan)
        
        # 3. The Reviewer (QA & Refinement)
        # For now, we'll just execute the file creation, but in the future, 
        # the Reviewer could critique and request changes before writing.
        
        results = []
        for filename, content in code_files.items():
            logging.info(f"🛠️ Engineer writing: {filename}")
            # Use FilesystemMCP directly via manager
            # We need to find the internal tool or use the manager's execute_tool
            # Since we are inside the agent, we can call the manager.
            
            # Write file
            result = self.mcp_manager.execute_tool("fs_write_file", {"path": filename, "content": content})
            results.append(f"File {filename}: {result}")
            
        return f"Coding Task Completed.\n\nPlan:\n{plan}\n\nResults:\n" + "\n".join(results)

    def _consult_architect(self, goal: str) -> str:
        """The Architect creates a high-level technical plan."""
        prompt = f"""
        You are THE ARCHITECT, a senior software system designer.
        Your goal: Design a robust, scalable, and secure solution for the user's request.
        
        USER REQUEST: "{goal}"
        
        INSTRUCTIONS:
        1. **Analyze**: Understand the requirements and constraints.
        2. **Design**: Create a step-by-step implementation plan.
        3. **Structure**: Define the exact file structure.
        4. **Stack**: Recommend the best libraries and algorithms.
        
        OUTPUT FORMAT:
        - **Plan**: Detailed steps.
        - **Files**: List of files to create.
        - **Rationale**: Why this approach?
        
        Keep it technically precise and concise.
        """
        response = ollama.chat(model=self.model, messages=[{'role': 'user', 'content': prompt}])
        return response['message']['content']

    def _consult_engineer(self, goal: str, plan: str) -> Dict[str, str]:
        """The Engineer writes the actual code based on the plan."""
        prompt = f"""
        You are THE ENGINEER, a world-class software developer.
        Your goal: Write the code to implement the Architect's plan.
        
        USER REQUEST: "{goal}"
        ARCHITECT'S PLAN:
        {plan}
        
        INSTRUCTIONS:
        1. **Clean Code**: Follow PEP 8 (Python) or best practices for the language.
        2. **Error Handling**: Include try/except blocks and logging.
        3. **Completeness**: Write the FULL code. No placeholders like `# TODO`.
        4. **Output**: Return a JSON object mapping filenames to content.
        
        EXAMPLE OUTPUT FORMAT:
        {{
            "main.py": "print('Hello World')",
            "utils.py": "def add(a, b): return a + b"
        }}
        
        IMPORTANT: Return ONLY the valid JSON object. Do not add markdown formatting like ```json.
        """
        response = ollama.chat(model=self.model, messages=[{'role': 'user', 'content': prompt}])
        content = response['message']['content']
        
        # Clean up markdown if present
        content = re.sub(r"```json\s*", "", content)
        content = re.sub(r"```\s*", "", content)
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logging.error("❌ Engineer failed to produce valid JSON. Attempting fallback parsing.")
            # Fallback: Try to extract JSON blob
            match = re.search(r"(\{.*\})", content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass
            return {}

