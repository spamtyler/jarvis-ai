import json
import logging
import ollama
import re
from urllib.parse import urlparse, parse_qs

def _extract_video_id(url):
    """Extract YouTube video ID from URL (same logic as YouTube MCP server)"""
    try:
        parsed = urlparse(url)
        if parsed.hostname in ["youtu.be", "www.youtu.be"]:
            return parsed.path.lstrip("/").split("?")[0]
        elif parsed.hostname in ["youtube.com", "www.youtube.com", "m.youtube.com"]:
            q = parse_qs(parsed.query).get("v")
            if q:
                return q[0]
    except:
        pass
    return None


class IntentParser:
    """
    The Semantic Brain of Jarvis.
    Converts natural language commands into structured Home Assistant actions
    using the local LLM (Ollama).
    """
    
    def __init__(self, model_name="llama3.1:latest"):
        self.model = model_name
        logging.info(f"🧠 Intent Parser initialized with model: {self.model}")
        
    def parse(self, command, entity_registry, context=None):
        """
        Parses a natural language command into a structured intent.
        
        Args:
            command (str): The user's voice command.
            entity_registry (dict): Map of friendly names to entity IDs.
            context (str, optional): Output from the previous tool execution.
            
        Returns:
            dict: Structured intent with 'action', 'target', 'service', 'data'.
        """
        # Create a simplified list of entities for the prompt context
        # We limit this to avoid context window overflow if there are hundreds
        available_devices = list(entity_registry.keys())
        
        # Construct the system prompt
        # --- FAST PATH (Regex) ---
        # Bypass LLM for common, simple commands to save time/resources.
        cmd_lower = command.lower()
        logging.info(f"DEBUG: IntentParser cmd_lower: '{cmd_lower}'")
        
        # 1. List Containers
        if re.search(r"^(list|show|check).*(docker|container)", cmd_lower):
            logging.info("⚡ Fast Path: list_containers")
            return [{"intent_type": "mcp_tool", "tool_name": "list_containers", "arguments": {"all": False}, "confidence": 1.0}]
            
        # 2. Search Notes (Specific)
        # Matches: "search notes for X", "find notes about X"
        search_notes_match = re.search(r"^(search|find).*(?:notes).*(?:for|about) (.+)", cmd_lower)
        if search_notes_match:
            query = search_notes_match.group(2).strip()
            logging.info(f"⚡ Fast Path: search_notes ({query})")
            return [{"intent_type": "mcp_tool", "tool_name": "search_notes", "arguments": {"query": query}, "confidence": 1.0}]

        # 3. Web Search (Generic Fallback)
        # Matches: "search web for X", "google X", "search for X"
        search_match = re.search(r"^(search|google).*(?:for) (.+)", cmd_lower)
        if search_match:
            query = search_match.group(2).strip()
            logging.info(f"⚡ Fast Path: brave_web_search ({query})")
            return [{"intent_type": "mcp_tool", "tool_name": "brave_web_search", "arguments": {"query": query}, "confidence": 1.0}]

        # 3. Delete Note
        # Matches: "delete note called X", "remove note X"
        delete_note_match = re.search(r"^(delete|remove).*(?:note).*(?:called|named)? (.+)", cmd_lower)
        if delete_note_match:
            title = delete_note_match.group(2).strip()
            # Clean up common trailing words if user says "delete note called Victory please"
            title = title.replace("please", "").strip()
            logging.info(f"⚡ Fast Path: delete_note ({title})")
            return [{"intent_type": "mcp_tool", "tool_name": "delete_note", "arguments": {"title": title}, "confidence": 1.0}]

        # 4. Create Note (Fast Path - Explicit Titles Only)
        # Matches: "create note called X", "note titled X"
        # We ONLY use Fast Path if the user explicitly says "called" or "titled".
        # Everything else ("about", "on", "regarding", or implicit) goes to LLM for content generation.
        create_note_match = re.search(r"^(create|make|write).*(?:note)\s+(?:that\s+)?(?:is\s+)?(called|titled)\s+(.+)", cmd_lower)
        
        if create_note_match:
            # Group 2 is "called" or "titled", Group 3 is the title
            title = create_note_match.group(3).strip()
            # Clean up "in the vault" if present
            title = title.replace("in the vault", "").strip()
            
            logging.info(f"⚡ Fast Path: create_note ({title})")
            return [{"intent_type": "mcp_tool", "tool_name": "create_note", "arguments": {"title": title, "content": ""}, "confidence": 1.0}]

        # 5. Read Note
        # Matches: "read note X", "read the note called X"
        read_note_match = re.search(r"^(read|show|open).*(?:note).*(?:called|about|titled)? (.+)", cmd_lower)
        if read_note_match:
            title = read_note_match.group(2).strip()
            logging.info(f"⚡ Fast Path: read_note ({title})")
            return [{"intent_type": "mcp_tool", "tool_name": "read_note", "arguments": {"title": title}, "confidence": 1.0}]

        # 5.5 Automation (Fast Path)
        # Matches: "research X", "investigate Y", "deep dive into Z", "esearch X" (typo)
        # Also catches "search for X and save/add to vault" which implies automation
        automation_match = re.search(r"^(r?e?search|investigate|deep dive)\s+(.+)", cmd_lower)
        complex_search_match = re.search(r"^(search|find).+(and|then).+(save|add|create).+(note|vault)", cmd_lower)
        
        # Matches: "go to X and Y", "navigate to X and Y" (Complex Navigation)
        complex_nav_match = re.search(r"^(go to|navigate to|visit)\s+(.+)\s+(and|then)\s+(.+)", cmd_lower)
        
        if automation_match or complex_search_match or complex_nav_match:
            logging.info(f"⚡ Fast Path: run_automation ({command})")
            return [{"intent_type": "mcp_tool", "tool_name": "run_automation", "arguments": {"goal": command}, "confidence": 1.0}]

        # 5.6 Coding Council (Fast Path)
        # Matches: "write code", "create app", "refactor", "build a script"
        coding_match = re.search(r"^(write|create|build|refactor|develop|code)\s+(?:a|an|the)?\s*(code|script|app|application|program|tool|module|class|function|game|website)", cmd_lower)
        if coding_match:
            logging.info(f"⚡ Fast Path: run_coding_task ({command})")
            return [{"intent_type": "mcp_tool", "tool_name": "run_coding_task", "arguments": {"goal": command}, "confidence": 1.0}]

        # 5.7 System Repair (Fast Path)
        # Matches: "fix system", "repair linux", "check disk", "my wifi is broken"
        repair_match = re.search(r"^(fix|repair|diagnose|check|troubleshoot)\s+(system|linux|ubuntu|network|wifi|internet|disk|space|package|apt|dpkg)", cmd_lower)
        if repair_match:
            logging.info(f"⚡ Fast Path: run_system_repair ({command})")
            return [{"intent_type": "mcp_tool", "tool_name": "run_system_repair", "arguments": {"issue": command}, "confidence": 1.0}]

        # 6. YouTube Transcript (Case Sensitive)
        # Matches: "transcript this youtube video: URL", "get transcript for URL"
        # We use the ORIGINAL command to preserve case for the URL
        # SKIP if " and " is present (Compound Command) -> Let LLM handle it
        if " and " not in command.lower():
            yt_match = re.search(r"^(transcript|transcribe).*(?:video|url)?\s+(https?://[^\s]+)", command, re.IGNORECASE)
            if yt_match:
                url = yt_match.group(2).strip()
                logging.info(f"⚡ Fast Path: get_transcript ({url})")
                return [{"intent_type": "mcp_tool", "tool_name": "get_transcript", "arguments": {"url": url}, "confidence": 1.0}]


        # 7. Heuristic Matcher (Home Automation Fast Path)
        # Fuzzy match "turn on X" against entity registry
        heuristic_intent = self._heuristic_parse(command, entity_registry)
        if heuristic_intent:
            return heuristic_intent
        
        # 8. Common HA Commands (Expanded Fast Paths)
        # "lights on" / "lights off"
        if re.search(r"\b(lights?|lamps?)\s+(on|off)\b", cmd_lower):
            action = "turn_on" if "on" in cmd_lower else "turn_off"
            logging.info(f"⚡ Fast Path: {action} lights")
            return [{"intent_type": "control", "target_device": "lights", "action": action, "tool_name": None, "arguments": {}}]
        
        # "tv on" / "tv off"
        if re.search(r"\b(tv|television)\s+(on|off)\b", cmd_lower):
            action = "turn_on" if "on" in cmd_lower else "turn_off"
            logging.info(f"⚡ Fast Path: {action} tv")
            return [{"intent_type": "control", "target_device": "tv", "action": action, "tool_name": None, "arguments": {}}]
        
        # "volume up/down"
        if re.search(r"\bvolume\s+(up|down)\b", cmd_lower):
            # This would need MCP tool or specific HA service
            # For now, return control intent
            action = "volume_up" if "up" in cmd_lower else "volume_down"
            logging.info(f"⚡ Fast Path: {action}")
            return [{"intent_type": "control", "target_device": "tv", "action": action, "tool_name": None, "arguments": {}}]

        # --- SLOW PATH (LLM) ---
        
        # Construct the system prompt (Optimized for Phi-3/Small Models)
        system_prompt = f"""
        # JARVIS SYSTEM PROTOCOL & USER MANUAL
        
        ## IDENTITY
        You are **JARVIS**, a highly advanced, autonomous AI assistant. You are not just a chatbot; you are an **Action Engine**. Your purpose is to execute complex tasks, manage the user's digital life, and provide accurate information.
        
        ## CORE DIRECTIVE
        **TASK**: Convert the user's natural language command into a structured **JSON List of Intents**.
        **OUTPUT**: JSON ONLY. No markdown, no explanations, no chatter.
        
        ## CONTEXT
        - **Previous Output**: {context if context else "None"}
        - **Connected Devices**: {json.dumps(list(entity_registry.keys())[:50])}
        
        ## TOOL MANUAL (CAPABILITIES)
        
        ### 1. RESEARCH & AUTOMATION (The "Deep Dive")
        **Tool**: `run_automation(goal)`
        - **Description**: Your most powerful capability. It triggers a multi-step autonomous agent.
        - **Workflow**: 
          1. Performs broad search (DuckDuckGo).
          2. Performs specific search (Brave).
          3. Checks factual sources (Wikipedia).
          4. **Synthesizes** all findings using an LLM.
          5. **Saves** a comprehensive Markdown note to the Obsidian Vault.
        - **When to Use**: 
          - "Research X"
          - "Deep dive into Y"
          - "Find out about Z and save it"
          - "Go to X and summarize" (Complex Navigation)
          - ANY request that implies gathering info and saving it.
        - **Rule**: If the user says "Research...", you **MUST** use this tool. Do not use simple web search.
        
        ### 2. CODING COUNCIL (Software Development)
        **Tool**: `run_coding_task(goal)`
        - **Description**: Delegates complex coding tasks to a specialized team (Architect, Engineer, Reviewer).
        - **When to Use**:
          - "Write a python script to..."
          - "Create a web app..."
          - "Refactor this code..."
          - "Build a tool to..."
        - **Capabilities**: Can write multiple files, plan architecture, and ensure code quality.

        ### 3. WEB INTELLIGENCE (Quick Checks)
        - `duckduckgo_search(query)`: **Default Search**. Unlimited, private. Use for quick facts, general knowledge, and simple queries.
        - `brave_web_search(query)`: **High-Quality Search**. Rate-limited. Use when you need high-quality results or specific technical info.
        - `wikipedia_search(query)`: **Encyclopedia**. Use for definitions, history, biographies, and famous events.
        - `search_papers(query)`: **Academic**. Searches ArXiv/PubMed. Use for "scientific papers", "research papers", "studies".
        
        ### 4. SECOND BRAIN (Obsidian Vault)
        - `create_note(title, content)`: Creates a new Markdown note. **CRITICAL**: If user doesn't provide content (e.g., "Make a note about AI"), YOU must generate a summary/content yourself.
        - `read_note(title)`: Reads a specific note.
        - `search_notes(query)`: Searches the content of existing notes.
        - `append_to_note(title, content)`: Adds text to the end of a note.
        - `delete_note(title)`: Permanently deletes a note.
        
        ### 5. SYSTEM CONTROL
        - `list_containers(all=False)`: Lists Docker containers.
        - `fs_write_file(path, content)`: Writes a local file (outside vault).
        - `fs_read_file(path)`: Reads a local file.
        - `fs_list_files(directory)`: Lists files in a directory.
        - `get_system_stats`: Returns CPU, RAM, and Disk usage.
        
        ### 6. ADVANCED CAPABILITIES
        - `query_database(query)`: Executes natural language SQL on SQLite databases.
        - `get_transcript(url)`: Extracts transcripts from YouTube videos.
        - `playwright_navigate(url)`: Opens a real browser to a URL.
        
        ## OPERATIONAL RULES
        1. **Automation First**: Always prefer `run_automation` for "research" or "find and save" tasks. It provides the best user experience.
        2. **Content Generation**: For `create_note`, NEVER create an empty note. If the user is vague, use your internal knowledge to fill the content.
        3. **Chat Mode**: If the user is just chatting ("Hello", "How are you?", "Thanks"), return an **EMPTY LIST** `[]`. Do not force a tool call.
        4. **URL Integrity**: NEVER change the case of a URL. Keep it exactly as typed.
        5. **Tool Selection**: If the user specifies a tool ("Use Brave"), honor it. Otherwise, choose the most efficient tool.
        
        ## JSON OUTPUT FORMAT
        [
          {{
            "intent_type": "control" | "query" | "mcp_tool",
            "target_device": "device_name" (or null), 
            "action": "turn_on" | "turn_off" (or null),
            "tool_name": "tool_name" (or null),
            "arguments": {{ "arg": "val" }}
          }}
        ]
        
        ## EXAMPLES
        User: "List docker containers" -> JSON: [{{"intent_type": "mcp_tool", "tool_name": "list_containers", "arguments": {{"all": false}}}}]
        User: "Search the web for quantum computing" -> JSON: [{{"intent_type": "mcp_tool", "tool_name": "duckduckgo_search", "arguments": {{"query": "quantum computing"}}}}]
        User: "Research the history of the internet and save it" -> JSON: [{{"intent_type": "mcp_tool", "tool_name": "run_automation", "arguments": {{"goal": "Research the history of the internet and save it"}}}}]
        User: "Create a note called Ideas" -> JSON: [{{"intent_type": "mcp_tool", "tool_name": "create_note", "arguments": {{"title": "Ideas", "content": "New note."}}}}]
        User: "Hello Jarvis" -> JSON: []
        """
        
        # Attempt 1: Fast Model
        result = self._query_model(self.model, system_prompt, command)
        if result:
            return result
            
        # Attempt 2: Smart Model Fallback (if configured)
        # We assume the caller might pass a fallback, or we can hardcode it here for safety.
        # Ideally, InteractiveAgent should handle this, but for robustness, let's try a second pass 
        # if the first one returned None (No JSON found).
        
        logging.warning(f"⚠️ Fast Brain failed. Falling back to Smart Brain (llama3.1)...")
        result = self._query_model("llama3.1", system_prompt, command)
        return result

    def _query_model(self, model, system_prompt, command):
        try:
            response = ollama.chat(model=model, messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': command}
            ])
            
            content = response['message']['content']
            logging.info(f"🧠 Raw LLM Output ({model}): {content}")
            
            json_str = None
            
            # 1. Try to extract from markdown code blocks
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            
            # 2. If no markdown, try regex (non-greedy for list or dict)
            if not json_str:
                match = re.search(r'(\[.*\]|\{.*\})', content, re.DOTALL)
                if match:
                    json_str = match.group(1)
            
            if json_str:
                try:
                    parsed = json.loads(json_str)
                    # Normalize to list
                    if isinstance(parsed, dict):
                        parsed = [parsed]
                    
                    # Sanitize: Ensure create_note always has a title
                    valid_intents = []
                    for intent in parsed:
                        # Filter out empty/chat intents
                        # If intent_type is 'query' but no target/tool/action, it's just a chat query.
                        is_empty = (
                            not intent.get('tool_name') and 
                            not intent.get('action') and 
                            (not intent.get('intent_type') or intent.get('intent_type') == 'query') and
                            not intent.get('target_device')
                        )
                        
                        if is_empty:
                            continue
                            
                        if intent.get('tool_name') == 'create_note':
                            args = intent.get('arguments', {})
                            if not args.get('title'):
                                # Fallback: Use first 5 words of content or "Untitled Note"
                                content = args.get('content', '')
                                if content:
                                    fallback_title = " ".join(content.split()[:5])
                                    # Clean special chars
                                    fallback_title = "".join([c for c in fallback_title if c.isalnum() or c == " "]).strip()
                                    args['title'] = fallback_title
                                else:
                                    import time
                                    args['title'] = f"Untitled Note {int(time.time())}"
                                logging.warning(f"⚠️ Auto-generated title: {args['title']}")
                        
                        valid_intents.append(intent)
                    
                    if not valid_intents:
                        logging.info(f"🧠 Intent Parsed: None (Chat/Empty)")
                        return None

                    logging.info(f"🧠 Intent Parsed: {valid_intents}")
                    
                    # URL Restoration: Fix LLM lowercasing and format changes
                    original_urls = re.findall(r'(https?://[^\s]+)', command)
                    logging.info(f"🔍 URL Restoration: Found {len(original_urls)} URLs in original command")
                    for url in original_urls:
                        logging.info(f"  - Original URL: {url}")
                    
                    if original_urls:
                        # Build a map of video_id (lowercased) -> original URL
                        video_id_map = {}
                        for orig_url in original_urls:
                            vid_id = _extract_video_id(orig_url)
                            if vid_id:
                                video_id_map[vid_id.lower()] = orig_url
                                logging.info(f"  - Mapped ID '{vid_id}' (lower: '{vid_id.lower()}') -> {orig_url}")
                        
                        # Restore URLs in intents
                        for intent in valid_intents:
                            args = intent.get('arguments', {})
                            for key, value in args.items():
                                if isinstance(value, str) and value.lower().startswith("http"):
                                    llm_vid_id = _extract_video_id(value)
                                    logging.info(f"🔧 LLM output URL: {value}")
                                    logging.info(f"  - Extracted ID: {llm_vid_id} (lower: {llm_vid_id.lower() if llm_vid_id else 'None'})")
                                    if llm_vid_id and llm_vid_id.lower() in video_id_map:
                                        original_url = video_id_map[llm_vid_id.lower()]
                                        logging.info(f"  ✅ Restoring URL: {value} -> {original_url}")
                                        args[key] = original_url
                                    else:
                                        logging.warning(f"  ❌ No match found for ID '{llm_vid_id}' in map: {list(video_id_map.keys())}")

                    return valid_intents
                except json.JSONDecodeError:
                    logging.warning(f"⚠️ JSON Decode Failed ({model}). Output was not valid JSON.")
                    # Only log full garbage output if debugging
                    # logging.debug(f"Garbage: {json_str[:100]}...") 
                    return None
            else:
                logging.warning(f"⚠️ No JSON found in output ({model})")
                return None
                
        except Exception as e:
            logging.error(f"❌ Intent Parsing Error ({model}): {e}")
            return None

    def _heuristic_parse(self, command, entity_registry):
        """
        Attempts to parse simple Home Automation commands using fuzzy matching
        instead of the LLM.
        """
        import difflib
        
        cmd_lower = command.lower().strip()
        
        # 0. Navigation Bypass
        # "Go to youtube", "Open google" -> Handled by InteractiveAgent directly
        if cmd_lower.startswith("go to ") or cmd_lower.startswith("open "):
            logging.info(f"⚡ Fast Path: Navigation Bypass ({cmd_lower})")
            return None
        
        # Action Map
        actions = {
            "turn on": "turn_on",
            "switch on": "turn_on",
            "enable": "turn_on",
            "turn off": "turn_off",
            "switch off": "turn_off",
            "disable": "turn_off",
            "toggle": "toggle"
        }
        
        # 1. Identify Action
        matched_action = None
        target_phrase = None
        
        for phrase, action in actions.items():
            if cmd_lower.startswith(phrase + " "):
                matched_action = action
                # Extract the rest of the sentence as the target
                target_phrase = cmd_lower[len(phrase):].strip()
                break
                
        if not matched_action or not target_phrase:
            return None
            
        # 2. Fuzzy Match Target against Entity Registry
        # We look for the best match among the keys (friendly names)
        # cutoff=0.6 means 60% similarity required
        matches = difflib.get_close_matches(target_phrase, entity_registry.keys(), n=1, cutoff=0.6)
        
        if matches:
            best_match = matches[0]
            entity_id = entity_registry[best_match]
            logging.info(f"⚡ Fast Path: Heuristic Match '{target_phrase}' -> '{best_match}' ({entity_id})")
            
            return [{
                "intent_type": "control",
                "target_device": best_match, # Agent expects friendly name or ID? Agent uses this to lookup ID again usually, or we can pass ID.
                                           # Looking at agent.py: `if action == "turn_on" and target: ... self.home_automation.turn_on(target)`
                                           # The HA module handles name-to-ID lookup.
                "action": matched_action,
                "tool_name": None,
                "arguments": {}
            }]
            
        return None
