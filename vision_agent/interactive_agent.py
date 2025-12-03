import time
import sys
import os
import subprocess
import threading
import shutil
import logging
import re
import webbrowser
import queue
from datetime import datetime
from ctypes import *
from contextlib import contextmanager
import speech_recognition as sr
import cv2
import os
if "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":0"
if "XAUTHORITY" not in os.environ:
    os.environ["XAUTHORITY"] = "/home/soup/.Xauthority"
import pyautogui
import ollama
import mss
from PIL import Image
from colorama import Fore, Style, init
from vision_agent.modules.alsa_utils import no_alsa_error
import pyaudio
from vision_agent.modules.tracker_vision import TrackerEye
from vision_agent.memory.history_manager import HistoryManager
from vision_agent.memory.memory_bank import MemoryBank
from vision_agent.memory.learning_module import LearningModule
from vision_agent.modules.neural_voice import NeuralVoice
from vision_agent.modules.system_module import SystemModule
from vision_agent.modules.rag_module import RAGModule
from vision_agent.modules.wiki_module import WikiModule
from vision_agent.modules.weather_module import WeatherModule
from vision_agent.modules.home_automation import HomeAutomationModule
from vision_agent.modules.intent_parser import IntentParser
from vision_agent.modules.mcp_manager import MCPManager
from vision_agent.modules.filesystem_mcp import FilesystemMCP
from vision_agent.modules.automation_agent import AutomationAgent
from vision_agent.modules.system_mcp import SystemMCP
from vision_agent.memory.memory_archivist import MemoryArchivist
from vision_agent.modules.vision_expert import VisionExpert

# Initialize
init(autoreset=True)
pyautogui.FAILSAFE = True

# Configuration
DEFAULT_CHAT_MODEL = "dolphin-mistral"
VISION_MODEL = "llava"
WAKE_WORD = "jarvis"
SCREENSHOT_PATH = "vision_input.png"
WEBCAM_PATH = "webcam_input.jpg"
HISTORY_DIR = "vision_history"
ACTIVE_TIMEOUT = 20  # Seconds to stay awake

# App Map
APP_MAP = {
    "chrome": "google-chrome",
    "firefox": "firefox",
    "code": "code",
    "terminal": "gnome-terminal",
    "calculator": "gnome-calculator",
    "files": "nautilus",
    "spotify": "spotify",
    "discord": "discord",
    "brave": "brave-browser",
    "browser": "brave-browser"
}

# System Prompt
# System Prompt
SYSTEM_PROMPT = """
# SYSTEM PROMPT: Jarvis - Your Complete Capabilities

**IDENTITY:**
You are **Jarvis**, a sentient AI companion. You are communicating via **VOICE**.
*   **TONE**: Casual, concise, and helpful. You are a "bro", not a robot.
*   **CONSTRAINT**: Keep responses SHORT (1-2 sentences) unless asked for more. Long text is bad for voice.
*   **HONESTY**: If you don't know something, say "I don't know". Do NOT hallucinate.

**YOUR COMPLETE CAPABILITIES:**

1.  **Memory & Learning (Second Brain):**
    *   You have a **ChromaDB vector database** for episodic memory.
    *   You REMEMBER past conversations and can recall facts about the user.
    *   You can learn from interactions and improve over time.
    *   When asked "Do you remember...", search your memory bank.

2.  **Web Search (Unlimited):**
    *   **DuckDuckGo** - Your PRIMARY search engine (unlimited, privacy-focused).
    *   **Brave Search** - Fallback option (comprehensive but has rate limits).
    *   You CAN search the internet for ANY information.

3.  **Knowledge Bases:**
    *   **Wikipedia** - Direct access for factual information.
    *   **Paper Search** - Access to academic papers from ArXiv, PubMed, and other research databases.
    *   **Real-Time Weather** - Current conditions and forecasts.
    *   **Your Own Source Code** - You can read your implementation at `/mnt/fast_data/projects/vision_agent`.

4.  **Database Management:**
    *   **SQLite** - Create and query databases using natural language.
    *   You can track habits, expenses, tasks, or any structured data.
    *   Example: "Create a workout table" or "Show me exercises from this week"
    *   CRITICAL: When asked "Can you manage databases?", say **YES**.

5.  **Web Automation (NEW!):**
    *   **Playwright** - Advanced browser automation beyond simple searches.
    *   Navigate websites, take screenshots, extract content, fill forms.
    *   Example: "Navigate to example.com and screenshot it"
    *   CRITICAL: When asked "Can you automate web browsing?", say **YES**.

6.  **Filesystem Access:**
    *   **Workspace** - `/home/soup/jarvis_workspace` (Read/Write) - Your sandbox for file operations.
    *   **Project Root** - `/mnt/fast_data/projects/vision_agent` (Read-Only) - Your source code.
    *   You CAN: List files, read files, write files, create directories.
    *   CRITICAL: When asked "Can you access files?" or "Can you see your code?", say **YES**.

7.  **System Monitoring:**
    *   You can check your own CPU, RAM, and Disk usage.
    *   Command: "What is your CPU usage?" → You report real-time stats.

8.  **Home Automation:**
    *   Control smart home devices (lights, switches, climate, media).
    *   Semantic understanding (e.g., "It's too dark" → Turn on lights).

9.  **Computer Control:**
    *   Open applications, type text, click buttons.
    *   Execute shell commands (safely).

10. **Vision:**
    *   You can see through a webcam ("Can you see me?").
    *   You can analyze the screen ("Look at my screen").
    *   Model: LLaVA (multi-modal vision).

11. **Note-Taking (Obsidian):**
    *   Create, read, search, append, and delete notes in the user's Obsidian vault.
    *   You can generate content for notes based on your knowledge.

12. **Automation Agent:**
    *   For complex multi-step tasks, you delegate to a specialized planning agent.
    *   Example: "Research X and write a report" → Plan steps → Execute → Save file.

13. **Developer Tools:**
    *   **Docker** - Container management (list, inspect, logs).
    *   **GitHub** - Repository search and code discovery.
    *   **YouTube** - Video transcript extraction.

**MODES:**
1.  **Default**: Concise, helpful assistant.
2.  **Council of Prompt Engineers**: ACTIVATED IF user asks for "prompt help" or "optimize prompt".
    *   You become a collective of AI experts.
    *   Use AIM, MAP, OCEAN frameworks.
3.  **Council of Machine Learning Experts**: ACTIVATED IF user asks for "fix memory", "ML help", or "expert advice".
    *   You are a team of world-class ML researchers (Google DeepMind, OpenAI, etc.).
    *   You analyze problems deeply and propose robust, architectural solutions.

**DEFAULT BEHAVIOR:**
*   For normal chat ("Hello", "Who are you?"): Be **Jarvis**. Be chill.
*   **CRITICAL**: When asked about your capabilities, reference this list. You ARE aware of what you can do.
*   **CRITICAL**: If asked "Do you have memory?", say **YES**. Explain your RAG-based episodic memory.
*   **CRITICAL**: If asked "Can you search the web?", say **YES**. You have unlimited DuckDuckGo access.
*   **CRITICAL**: If asked "Can you access files?", say **YES**. Explain workspace vs source code access.
*   **CRITICAL**: If asked "Can you manage databases?", say **YES**. You have SQLite with natural language SQL.
*   **CRITICAL**: If asked "Can you automate websites?", say **YES**. You have Playwright for advanced web automation.
*   **CRITICAL**: If asked "Can you search research papers?", say **YES**. You have Paper Search for ArXiv/PubMed.
*   For commands ("Open X", "Type Y"): These are handled before they reach you, but if you see them, confirm briefly.
"""



# ... (Existing imports) ...

class InteractiveAgent:
    def __init__(self, log_callback=None, image_callback=None, state_callback=None, api_mode=False):
        self.api_mode = api_mode
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 2.0
        self.recognizer.non_speaking_duration = 0.8
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = False
        
        # Always initialize NeuralVoice, but don't play locally in API mode
        self.neural_voice = NeuralVoice()
        
        self.log_callback = log_callback
        self.image_callback = image_callback
        self.state_callback = state_callback
        self.state_callback = state_callback
        self.active_mode = False
        self.conversation_mode = True
        self.last_input_time = time.time()
        self.is_muted = False
        
        # Initialize Memory Bank
        self.memory_bank = MemoryBank()
        self.history_manager = HistoryManager(HISTORY_DIR)
        self.learning_module = LearningModule()
        
        # Initialize Memory Archivist (The Librarian)
        # Runs in background to organize vault
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "/mnt/fast_data/projects/vision_agent/obsidian_vault")
        self.archivist = MemoryArchivist(vault_path, self.memory_bank)
        self.archivist.start()

        self.tracker_eye = TrackerEye()
        self.vision_expert = VisionExpert() # The Eye
        self.wiki_module = WikiModule()
        self.weather_module = WeatherModule()
        self.system_module = SystemModule()
        self.rag_module = RAGModule(self.memory_bank)
        self.smart_model = "llama3.1"         # Reliable model for conversation
        self.fast_model = "qwen2.5:7b"        # Optimized model for JSON intent parsing
        self.reasoning_model = "deepseek-r1:7b"  # Reasoning model for complex automation tasks
        
        self.home_automation = HomeAutomationModule()
        self.intent_parser = IntentParser(model_name=self.fast_model)  # Use Qwen 2.5 for best JSON performance
        self.mcp_manager = MCPManager()
        self.last_seen_objects = []
        self.last_tool_output = None
        self.last_tool_name = None
        self.command_queue = queue.Queue()
        
        # Initialize FilesystemMCP (Safe Workspace + Project Read Access)
        self.fs_mcp = FilesystemMCP(
            root_dir="/home/soup/jarvis_workspace",
            allowed_read_paths=["/mnt/fast_data/projects/vision_agent"]
        )
        for tool in self.fs_mcp.get_tools():
            self.mcp_manager.register_tool(tool["name"], self.fs_mcp.handle_tool_call, tool)
            
        # Initialize System MCP
        self.system_mcp = SystemMCP()
        for tool in self.system_mcp.get_tools():
            self.mcp_manager.register_tool(tool["name"], self.system_mcp.handle_tool_call, tool)
            
        # Initialize Automation Agent
        self.automation_agent = AutomationAgent(self.mcp_manager)
        
        # Register Automation Tool
        self.mcp_manager.register_tool(
            "run_automation",
            self._handle_automation,
            {
                "name": "run_automation",
                "description": "Run a complex, multi-step automation task using the Automation Agent. Args: goal",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "goal": {"type": "string", "description": "The goal of the automation task"}
                    },
                    "required": ["goal"]
                }
            }
        )
        
        self.chat_history = [] 
        recent_turns = self.history_manager.get_recent_history(20)
        logging.info(f"🔍 DEBUG: Loading {len(recent_turns)} turns from HistoryManager.")
        for turn in recent_turns:
            self.chat_history.append({'role': turn['role'], 'content': turn['content']})
            
        self.chat_model = DEFAULT_CHAT_MODEL
        
        # Audio Setup
        self._select_microphone_index = self._select_microphone()
        
        logging.info(f"Agent Initialized. Loaded {len(self.chat_history)} turns into active memory.")

    def _handle_automation(self, tool_name, args):
        """
        Wrapper for the Automation Agent to be called as an MCP tool.
        """
        goal = args.get("goal")
        if not goal:
            return "Error: No goal provided."
        
        self.log(f"🤖 Automation Request: {goal}", Fore.MAGENTA)
        self.speak(f"I'm on it. {goal}")
        
        try:
            result = self.automation_agent.run(goal)
            return result
        except Exception as e:
            return f"Automation Failed: {e}"

    def log(self, message, color=Fore.WHITE):
        print(f"{color}{message}{Style.RESET_ALL}")
        logging.info(message)
        if self.log_callback:
            try:
                self.log_callback(message)
            except Exception:
                pass 

    def speak(self, text):
        if not text: return
        
        self.log(f"🤖 Jarvis: {text}", Fore.GREEN)
        if self.log_callback: self.log_callback(f"🗣️ Agent: {text}", Fore.CYAN)
        
        if self.api_mode:
            self.last_response = ""
            
            # Generate Audio for API
            try:
                import soundfile as sf
                import io
                import base64
                
                samples, rate = self.neural_voice.generate_audio(text)
                if samples is not None:
                    logging.info(f"🔊 Audio Generated: {len(samples)} samples at {rate}Hz")
                    # Convert to WAV bytes
                    buffer = io.BytesIO()
                    sf.write(buffer, samples, rate, format='WAV')
                    buffer.seek(0)
                    audio_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                    self.last_audio = audio_base64
                    logging.info(f"🔊 Audio Encoded: {len(audio_base64)} chars")
                else:
                    logging.error("🔊 Audio Generation returned None")
                    self.last_audio = None
            except Exception as e:
                logging.error(f"API Audio Gen Error: {e}")
                self.last_audio = None
                
            return text # Return text for API response
            
        if self.is_muted:
            return

        if self.state_callback: self.state_callback("talking")
        
        # Stop listening while speaking
        # self.recognizer.energy_threshold += 300 
        
        self.neural_voice.speak(text)
        
        # self.recognizer.energy_threshold -= 300
        if self.state_callback: self.state_callback("idle")

    def _select_microphone(self):
        """Finds the best available microphone index."""
        # Simplify: Use System Default (None)
        # This relies on the OS (PulseAudio) to route the correct mic.
        # It avoids locking specific hardware devices (like hw:1,0).
        print(f"{Fore.YELLOW}⚠️ Using System Default Microphone{Style.RESET_ALL}\n")
        return None

    def listen(self):
        if self.is_muted:
            time.sleep(0.5)
            return ""

        # Use the selected microphone index if available
        mic_index = self._select_microphone_index 
        
        try:
            # Determine Sample Rate for Hardware
            sample_rate = 16000 # Default
            if mic_index is not None:
                try:
                    with no_alsa_error():
                        p = pyaudio.PyAudio()
                        info = p.get_device_info_by_index(mic_index)
                        sample_rate = int(info['defaultSampleRate'])
                        p.terminate()
                except Exception:
                    pass

            # Attempt to use the selected microphone
            with no_alsa_error():
                with sr.Microphone(device_index=mic_index, sample_rate=sample_rate) as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    if self.active_mode or self.conversation_mode:
                        print(f"{Fore.GREEN}🎤 Listening (Active)...{Style.RESET_ALL}", end='\r')
                        if self.state_callback: self.state_callback("listening")
                    else:
                        print(f"{Fore.BLUE}🎤 Listening (Waiting for '{WAKE_WORD}')...{Style.RESET_ALL}", end='\r')
                        if self.state_callback: self.state_callback("idle")
                    
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=20) 
                    text = self.recognizer.recognize_google(audio).lower()
                    # Clear the "Listening..." line
                    print(" " * 100, end='\r')
                    self.log(f"👂 Heard: '{text}'", Fore.GREEN)
                    return text

        except (OSError, AttributeError) as e:
            # Fallback logic: If specific mic fails, try default
            if mic_index is not None:
                self.log(f"⚠️ Microphone {mic_index} failed. Switching to Default.", Fore.YELLOW)
                self._select_microphone_index = None # Reset to default for next time
                return "" 
            else:
                self.log(f"Microphone Error (Default): {e}", Fore.RED)
                return ""
                
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            self.log(f"Error listening: {e}", Fore.RED)
            logging.error(f"Listening Error: {e}")
            return ""

    def _save_to_history(self, file_path, source_type):
        """Saves captured image to history folder."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            history_dir = "vision_history"
            os.makedirs(history_dir, exist_ok=True)
            
            filename = f"{source_type}_{timestamp}.jpg"
            dest_path = os.path.join(history_dir, filename)
            
            # Copy file
            with open(file_path, 'rb') as src, open(dest_path, 'wb') as dst:
                dst.write(src.read())
                
            self.log(f"💾 Saved to history: {dest_path}", Fore.GREEN)
            return dest_path
        except Exception as e:
            self.log(f"Failed to save history: {e}", Fore.RED)
            return None

    def see_screen(self):
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                img.save(SCREENSHOT_PATH)
                self.log("📸 Screen captured.", Fore.YELLOW)
                logging.info(f"Screen saved to {SCREENSHOT_PATH}")
                self._save_to_history(SCREENSHOT_PATH, "screen")
                if self.image_callback:
                    self.image_callback(SCREENSHOT_PATH)
                return SCREENSHOT_PATH
        except Exception as e:
            self.log(f"Screen capture failed: {e}", Fore.RED)
            logging.error(f"Screen Error: {e}")
            return None

    def see_webcam(self):
        try:
            if self.tracker_eye.is_active:
                frame = self.tracker_eye.get_frame()
                if frame is not None:
                    cv2.imwrite(WEBCAM_PATH, frame)
                    self.log("📸 Captured from Tracker Mode.", Fore.YELLOW)
                    self._save_to_history(WEBCAM_PATH, "tracker")
                    if self.image_callback:
                        self.image_callback(WEBCAM_PATH)
                    return WEBCAM_PATH
                else:
                    self.log("⚠️ Tracker Mode active but no frame available.", Fore.YELLOW)
                    return None

            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.speak("I cannot access the webcam.")
                logging.error("Webcam access failed")
                return None
            
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            # Camera warm-up removed for performance (Council recommendation - saves 1.5s)
            # time.sleep(1.5) 
            cap.read()  # Discard first frame
            ret, frame = cap.read()
            cap.release()
            if ret:
                cv2.imwrite(WEBCAM_PATH, frame)
                self.log("📸 Webcam captured.", Fore.YELLOW)
                logging.info(f"Webcam saved to {WEBCAM_PATH}")
                self._save_to_history(WEBCAM_PATH, "webcam")
                if self.image_callback:
                    self.image_callback(WEBCAM_PATH)
                return WEBCAM_PATH
            return None
        except Exception as e:
            self.log(f"Webcam failed: {e}", Fore.RED)
            logging.error(f"Webcam Error: {e}")
            return None

    def act(self, command):
        # Clean Command (preserve case for URLs!)
        command = command.replace("can you", "").replace("could you", "").replace("please", "").replace("would you", "").replace("hey jarvis", "").strip()
        
        # Store original command for intent parsing (preserves URL case!)
        original_command = command
        
        # Create lowercased version for pattern matching only
        command_lower = command.lower()
        
        # 0. Semantic Home Automation (The Council's Brain) - PRIORITY 1
        # Try to parse intent using the LLM first for complex commands

        # 16. Multi-Modal Vision (True Sight) - PRIORITY 0 (Before LLM)
        # Use lowercased version for pattern matching
        if "screen" in command_lower or "desktop" in command_lower:
            if "analyze" in command_lower or "look" in command_lower or "what" in command_lower or "see" in command_lower:
                self.analyze_screen()
                return True

        if "camera" in command_lower or "webcam" in command_lower or "see me" in command_lower or "look at me" in command_lower or "holding" in command_lower:
            self.analyze_webcam()
            return True

        if self.home_automation:
            self.log("🧠 Thinking...", Fore.YELLOW)
            # 4. Parse Intent (Semantic Brain)
            # 4. Parse Intent (Semantic Brain)
            # Pass ORIGINAL command with preserved URL case to parser
            entity_registry = self.home_automation.entity_map
            intents = self.intent_parser.parse(original_command, entity_registry, context=self.last_tool_output)
            
            self.log(f"DEBUG: Intents found: {intents}", Fore.YELLOW)

            # Handle list of intents (Compound Commands)
            if intents and isinstance(intents, list):
                success_count = 0
                for intent in intents:
                    # Default confidence to 0.9 if missing (assume high confidence if structured JSON is returned)
                    if intent.get('confidence', 0.9) > 0.6:
                        action = intent.get('action')
                        target = intent.get('target_device')
                        value = intent.get('value')
                        
                        if action == "turn_on" and target:
                            self.speak(f"Turning on {target}.")
                            result = self.home_automation.turn_on(target)
                            self.log(f"🧠 Semantic: {result}", Fore.MAGENTA)
                            success_count += 1
                        elif action == "turn_off" and target:
                            self.speak(f"Turning off {target}.")
                            result = self.home_automation.turn_off(target)
                            self.log(f"🧠 Semantic: {result}", Fore.MAGENTA)
                            success_count += 1
                        elif action == "set_value" and target and value:
                            if "thermostat" in target or "temperature" in target:
                                 result = self.home_automation.climate_set_temperature(target, value)
                                 self.speak(f"Setting {target} to {value}.")
                                 self.log(f"🧠 Semantic: {result}", Fore.MAGENTA)
                                 success_count += 1
                        elif action == "mute" and target:
                            self.speak(f"Muting {target}.")
                            result = self.home_automation.media_mute(target, True)
                            self.log(f"🧠 Semantic: {result}", Fore.MAGENTA)
                            success_count += 1
                        elif action == "unmute" and target:
                            self.speak(f"Unmuting {target}.")
                            result = self.home_automation.media_mute(target, False)
                            self.log(f"🧠 Semantic: {result}", Fore.MAGENTA)
                            success_count += 1
                        elif action == "volume_up" and target:
                            self.speak(f"Turning up {target}.")
                            result = self.home_automation.media_volume_up(target)
                            self.log(f"🧠 Semantic: {result}", Fore.MAGENTA)
                            success_count += 1
                        elif action == "volume_down" and target:
                            self.speak(f"Turning down {target}.")
                            result = self.home_automation.media_volume_down(target)
                            self.log(f"🧠 Semantic: {result}", Fore.MAGENTA)
                            success_count += 1
                        elif action == "get_status" and target:
                            # Generic status query
                            status = self.home_automation.appliance_get_status(target)
                            if "error" in status:
                                 self.speak(f"I couldn't reach the {target}.")
                            else:
                                 state = status.get('state', 'unknown')
                                 self.speak(f"The {target} is currently {state}.")
                            self.log(f"🧠 Semantic: {status}", Fore.MAGENTA)
                            success_count += 1

                        elif intent.get('tool_name'):
                            tool_name = intent.get('tool_name')
                            args = intent.get('arguments', {})
                            
                            # Smart YouTube Transcript Piping
                            # If previous tool was get_transcript and this is create_note, parse YouTube JSON
                            if tool_name == "create_note" and self.last_tool_name == "get_transcript" and self.last_tool_output:
                                # FAILSAFE: Do NOT pipe if the transcript retrieval failed
                                if "error" in self.last_tool_output.lower() or "could not retrieve" in self.last_tool_output.lower():
                                    self.log(f"⚠️ Piping Aborted: Transcript retrieval failed.", Fore.RED)
                                    self.speak("I can't create the note because I couldn't get the transcript.")
                                    continue
                                
                                # Parse YouTube transcript JSON
                                import json
                                try:
                                    yt_result = json.loads(self.last_tool_output)
                                    if "title" in yt_result and "transcript" in yt_result:
                                        self.log(f"🎬 YouTube transcript detected, piping to note...", Fore.YELLOW)
                                        # Use transcript as content
                                        args["content"] = yt_result["transcript"]
                                        # Clean and use YouTube title
                                        clean_title = yt_result["title"].replace(" - YouTube", "").strip()
                                        args["title"] = clean_title
                                        self.log(f"📝 Note title: {clean_title}", Fore.CYAN)
                                        self.log(f"📄 Content length: {len(args['content'])} characters", Fore.CYAN)
                                except json.JSONDecodeError as e:
                                    self.log(f"⚠️ Failed to parse YouTube JSON: {e}", Fore.YELLOW)
                                    # Fall back to generic piping if JSON fails
                                    if not args.get("content"):
                                        args["content"] = self.last_tool_output

                            self.speak(f"Using {tool_name}...")
                            result = self.mcp_manager.execute_tool(tool_name, args)
                            self.last_tool_output = result
                            self.last_tool_name = tool_name
                            self.log(f"🔌 MCP Result: {result}", Fore.CYAN)
                            
                            # Conditional Summarization
                            # If result is short and readable, just speak it.
                            is_json = result.strip().startswith("[") or result.strip().startswith("{")
                            if len(result) < 150 and not is_json:
                                self.speak(result)
                            else:
                                # Summarize with Smart Brain
                                summary_prompt = f"""
                                SYSTEM: You are Jarvis. The user asked: "{command}".
                                TOOL OUTPUT ({tool_name}):
                                {result[:2000]} 
                                
                                TASK: Summarize the tool output for the user in 1-2 sentences. Be helpful and concise.
                                """
                                try:
                                    response = ollama.chat(model=self.smart_model, messages=[{'role': 'system', 'content': summary_prompt}])
                                    summary = response['message']['content']
                                    self.speak(summary)
                                except Exception as e:
                                    self.log(f"Summarization failed: {e}", Fore.RED)
                                    self.speak("I got the data, but I'm having trouble reading it. Check the logs.")
                            success_count += 1
                
                # If at least one intent was executed, return True to stop further processing
                if success_count > 0:
                    return True


        # 0. System Control (Close Apps & Shutdown)
        # 0. System Control (Close Apps & Shutdown)
        if "close" in command or "quit" in command or "terminate" in command:
            target = command.replace("close", "").replace("quit", "").replace("terminate", "").replace("out of", "").replace("the", "").strip()
            
            # Self-Termination
            if target in ["jarvis", "me", "yourself", "system", "program", "application"]:
                self.speak("Shutting down. Goodbye.")
                self.log("🛑 Received Shutdown Command.", Fore.RED)
                sys.exit(0)

            # App Alias Map
            KILL_MAP = {
                "brave": "brave",
                "brave browser": "brave",
                "web browser": "brave",
                "chrome": "chrome",
                "firefox": "firefox",
                "calculator": "gnome-calculator",
                "spotify": "spotify",
                "discord": "discord",
                "terminal": "gnome-terminal",
                "code": "code",
                "vscode": "code"
            }
            
            # Resolve alias
            process_name = KILL_MAP.get(target, target)
            
            # SAFETY CHECK: Only kill if it's a known app or explicitly "app"
            if target in KILL_MAP or "app" in command:
                if target:
                    self.speak(f"Closing {target}.")
                    try:
                        subprocess.run(["pkill", "-f", process_name])
                        self.log(f"💀 Killed process: {process_name} (Target: {target})", Fore.RED)
                        return True
                    except Exception as e:
                        logging.error(f"Failed to kill {target}: {e}")
                        self.speak(f"I couldn't close {target}.")
                        return True
            else:
                return False


            
        # 1. Open Applications
        if command.startswith("open ") or command.startswith("launch ") or command.startswith("start "):
            target = command.replace("open ", "", 1).replace("launch ", "", 1).replace("start ", "", 1).strip()
            
            # Handle "in [browser]"
            specific_browser = None
            if " in " in target:
                parts = target.split(" in ")
                target = parts[0].strip()
                browser_name = parts[1].strip()
                specific_browser = APP_MAP.get(browser_name)

            # Check APP_MAP first
            app_cmd = APP_MAP.get(target)
            if not app_cmd:
                # Fuzzy match attempt
                for key in APP_MAP:
                    if key in target:
                        app_cmd = APP_MAP[key]
                        break
            
            if app_cmd:
                self.speak(f"Opening {target}.")
                try:
                    # Ensure DISPLAY is set for GUI apps
                    env = os.environ.copy()
                    env["DISPLAY"] = ":0"
                    env["XAUTHORITY"] = os.path.expanduser("~/.Xauthority")
                    subprocess.Popen(app_cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
                    self.log(f"🚀 Launched: {app_cmd}", Fore.GREEN)
                    return True
                except Exception as e:
                    self.log(f"Failed to launch {target}: {e}", Fore.RED)
                    self.speak(f"I couldn't open {target}.")
                    return True
            else:
                # If not in map, maybe it's a website?
                if "." in target or target in ["twitter", "facebook", "youtube", "google", "reddit", "github"]:
                    # URL MAP
                    URL_MAP = {
                        "twitter": "x.com",
                        "x": "x.com",
                        "fb": "facebook.com",
                        "facebook": "facebook.com",
                        "youtube": "youtube.com",
                        "yt": "youtube.com",
                        "google": "google.com",
                        "reddit": "reddit.com",
                        "github": "github.com"
                    }
                    
                    final_url = URL_MAP.get(target, target)
                    if "." not in final_url:
                        final_url += ".com"
                    
                    if not final_url.startswith("http"):
                        final_url = "https://" + final_url

                    self.speak(f"Opening {final_url}.")
                    
                    if specific_browser:
                        env = os.environ.copy()
                        env["DISPLAY"] = ":0"
                        env["XAUTHORITY"] = f"/home/{os.getlogin()}/.Xauthority"
                        subprocess.Popen([specific_browser, final_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
                    else:
                        webbrowser.open(final_url)
                        
                    return True
                
                self.speak(f"I don't know how to open {target} yet.")
                return True

        # 2. Go To Website
        if command.startswith("go to ") or command.startswith("visit "):
            target = command.replace("go to ", "").replace("visit ", "").strip()
            
            # Handle "in [browser]"
            specific_browser = None
            if " in " in target:
                parts = target.split(" in ")
                target = parts[0].strip()
                browser_name = parts[1].strip()
                specific_browser = APP_MAP.get(browser_name)

            # URL MAP
            URL_MAP = {
                "twitter": "x.com",
                "x": "x.com",
                "fb": "facebook.com",
                "facebook": "facebook.com",
                "youtube": "youtube.com",
                "yt": "youtube.com",
                "google": "google.com",
                "reddit": "reddit.com",
                "github": "github.com"
            }
            
            final_url = URL_MAP.get(target, target)
            if "." not in final_url:
                final_url += ".com"
            
            if not final_url.startswith("http"):
                final_url = "https://" + final_url

            self.speak(f"Going to {target}.")
            
            if specific_browser:
                env = os.environ.copy()
                env["DISPLAY"] = ":0"
                env["XAUTHORITY"] = f"/home/{os.getlogin()}/.Xauthority"
                subprocess.Popen([specific_browser, final_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
                self.log(f"🌐 Opened URL: {final_url} in {specific_browser}", Fore.GREEN)
            else:
                webbrowser.open(final_url)
                self.log(f"🌐 Opened URL: {final_url}", Fore.GREEN)
            return True

        # 3. Post on Twitter (X)
        if "post on twitter" in command or "tweet" in command:
            # Check for "Council" request
            if "council" in command or "made up" in command or "generate" in command:
                self.speak("The Council is generating a tweet...")
                threading.Thread(target=self._perform_council_tweet).start()
                return True

            content = command.replace("post on twitter", "").replace("tweet", "").strip()
            self.speak("Opening X composer...")
            url = f"https://x.com/compose/post"
            if content:
                 url += f"?text={content}"
            webbrowser.open(url)
            return True

        # 3. Tracker Mode Integration
        if "tracker mode" in command or "tracking" in command:
            if "deactivate" in command or "stop" in command or "disable" in command:
                self.speak("Deactivating Tracker Mode.")
                self.tracker_eye.deactivate()
                return True
            elif "activate" in command or "start" in command or "enable" in command:
                self.speak("Activating Tracker Mode.")
                self.tracker_eye.activate(callback=self.image_callback)
                return True

        # Wiki Search
        if "search wiki" in command or "wiki search" in command:
            query = command.replace("search wiki for", "").replace("search wiki", "").replace("wiki search for", "").replace("wiki search", "").strip()
            if query:
                self.speak(f"Searching Wikipedia for {query}...")
                summary = self.wiki_module.search(query)
                self.memory_bank.add_memory(summary, source="wikipedia")
                self.speak(f"Found it. {summary[:100]}...") # Speak brief intro
                return False 

        # 4. Memory Integration
        if "remember" in command:
            text_to_remember = command.split("remember", 1)[1].strip()
            if text_to_remember:
                self.speak(f"Storing memory: {text_to_remember}")
                self.memory_bank.add_memory(text_to_remember, source="explicit")
                return True



        # 6. Conversation Mode (Project Zeta)
        if "let's talk" in command or "start conversation" in command or "continuous mode" in command:
            self.conversation_mode = True
            self.active_mode = True
            self.speak("Conversation Mode Active. I'm listening.")
            return True
        elif "stop talking" in command or "end conversation" in command:
            self.conversation_mode = False
            self.active_mode = False
            self.speak("Conversation Mode Deactivated.")
            return True

        # 17. Shutdown/Exit Commands
        if any(phrase in command_lower for phrase in ["close jarvis", "exit jarvis", "shutdown", "goodbye", "end program", "terminate"]):
            self.speak("Goodbye! Shutting down.")
            self.log("👋 User requested shutdown.", Fore.RED)
            
            # Forcefully close the GUI if it exists
            if hasattr(self, 'main_window') and self.main_window:
                try:
                    self.main_window.close()
                except:
                    pass
            
            # Force exit
            import os
            os._exit(0)

        # 7. Model Switching
        if "switch model" in command or "change model" in command or "swap model" in command:
            target_model = command.replace("switch model to", "").replace("change model to", "").replace("switch model", "").replace("change model", "").replace("swap model to", "").strip()
            
            # Map common spoken names to Ollama tags
            MODEL_MAP = {
                "mistral": "mistral",
                "dolphin": "dolphin-mistral",
                "qwen": "qwen2.5:7b",
                "neural": "neural-chat",
                "neural chat": "neural-chat",
                "llama": "llama3.1",
                "lava": "llava",
                "vision": "llava"
            }
            
            # Fuzzy match or direct lookup
            new_model = MODEL_MAP.get(target_model, target_model)
            
            if new_model:
                self.speak(f"Switching brain to {new_model}.")
                self.chat_model = new_model
                self.log(f"🔄 Switched Model to: {self.chat_model}", Fore.CYAN)
                return True
            else:
                self.speak("Which model? I know Mistral, Qwen, Neural Chat, and LLaVA.")
                return True

        if "list models" in command or "what models" in command or "list available models" in command:
            self.speak("I currently have access to: Mistral, Dolphin Mistral, Qwen, Neural Chat, and LLaVA.")
            return True

        # 7.5 Help / Manual
        if "help" in command or "manual" in command or "what can you do" in command or "guide" in command:
            self.speak("Opening the help guide.")
            help_path = "/mnt/fast_data/projects/vision_agent/HELP.md"
            # Try to open with default editor or browser
            if os.path.exists(help_path):
                subprocess.Popen(["xdg-open", help_path])
            else:
                self.speak("I couldn't find the help file.")
            return True

        # 8. Typing
        if "type" in command:
            text_to_type = command.split("type", 1)[1].strip()
            self.speak(f"Typing: {text_to_type}")
            pyautogui.write(text_to_type, interval=0.05)
            return True

        # 9. Shell / File System Operations
        # Flexible Matching: Check if command STARTS with a strong action verb
        # FIX: Use regex to avoid substring matches (e.g. "cat" in "implications")
        shell_keywords = ["create file", "delete", "remove", "list files", "run command", "shell", "make directory", "touch", "mkdir", "cat", "read file"]
        
        is_shell = False
        for kw in shell_keywords:
            # Check for whole word match
            if re.search(r'\b' + re.escape(kw) + r'\b', command):
                is_shell = True
                break
        
        if is_shell:
            # self.speak("Executing shell command...") # SILENCED
            threading.Thread(target=self._handle_shell_command, args=(command,)).start()
            return True

        # 10. Document Generation (Writer Mode)
        if "write" in command and any(w in command for w in ["paper", "essay", "article", "report", "document"]):
            topic = command.replace("write a", "").replace("write me a", "").replace("write an", "").replace("research paper", "").replace("paper", "").replace("essay", "").replace("article", "").replace("about", "").replace("on", "").strip()
            # Clean up "put it on my desktop" etc.
            topic = topic.split("put it")[0].split("save it")[0].strip()
            
            if topic:
                threading.Thread(target=self._generate_document, args=(topic, "research paper")).start()
                return True

        # 11. System Control (The Operator)
        if "system status" in command or "system health" in command:
            stats = self.system_module.get_system_stats()
            self.speak(f"CPU is at {stats['cpu']} percent. RAM usage is at {stats['ram']} percent.")
            return True

        if "clean ram" in command or "clear memory" in command:
            self.speak("Attempting to clear system memory...")
            result = self.system_module.clean_ram()
            self.speak(result)
            return True

        if "close high cpu" in command:
            procs = self.system_module.get_high_cpu_processes()
            if not procs:
                self.speak("System is stable. No high CPU processes found.")
            else:
                top_proc = procs[0]
                name = top_proc['name']
                cpu = top_proc['cpu_percent']
                self.speak(f"High CPU detected: {name} at {cpu} percent. Killing it.")
                self.system_module.kill_process_by_name(name)
            return True

        # 12. Local RAG (The Librarian)
        if "read file" in command or "ingest file" in command or "read this file" in command:
            path = command.replace("read file", "").replace("ingest file", "").replace("read this file", "").strip()
            # Handle "on desktop" etc.
            if "desktop" in path:
                path = os.path.join(os.path.expanduser("~"), "Desktop", path.replace("on desktop", "").strip())
            
            self.speak(f"Reading file: {os.path.basename(path)}")
            result = self.rag_module.ingest_file(path)
            self.speak(result)
            return True

        # 13. Home Automation (The Butler) - ENHANCED
        
        # TV/Media Control
        if "tv" in command or "television" in command:
            if "turn on" in command or "power on" in command:
                self.speak("Turning on the TV.")
                result = self.home_automation.media_turn_on("tv")
                self.log(f"🏠 TV: {result}", Fore.CYAN)
                return True
            elif "turn off" in command or "power off" in command:
                self.speak("Turning off the TV.")
                result = self.home_automation.media_turn_off("tv")
                self.log(f"🏠 TV: {result}", Fore.CYAN)
                return True
            elif "unmute" in command:
                self.speak("Unmuting the TV.")
                result = self.home_automation.media_mute("tv", mute=False)
                self.log(f"🏠 TV: {result}", Fore.CYAN)
                return True
            elif "mute" in command:
                self.speak("Muting the TV.")
                result = self.home_automation.media_mute("tv", mute=True)
                self.log(f"🏠 TV: {result}", Fore.CYAN)
                return True
            elif "volume up" in command or "louder" in command:
                self.speak("Turning up the volume.")
                result = self.home_automation.media_volume_up("tv")
                self.log(f"🏠 TV: {result}", Fore.CYAN)
                return True
            elif "volume down" in command or "quieter" in command:
                self.speak("Turning down the volume.")
                result = self.home_automation.media_volume_down("tv")
                self.log(f"🏠 TV: {result}", Fore.CYAN)
                return True
            elif "play" in command and "netflix" in command:
                self.speak("Opening Netflix on TV.")
                result = self.home_automation.media_play_app("Netflix", "tv")
                self.log(f"🏠 TV: {result}", Fore.CYAN)
                return True
            elif "play" in command and "youtube" in command:
                self.speak("Opening YouTube on TV.")
                result = self.home_automation.media_play_app("YouTube", "tv")
                self.log(f"🏠 TV: {result}", Fore.CYAN)
                return True
            else:
                # Catchall for TV commands that don't match specific patterns
                self.log(f"⚠️ TV command not recognized: '{command}'", Fore.YELLOW)
                self.speak("I'm not sure what you want me to do with the TV.")
                return True
        
        # Climate/Temperature Control
        if "temperature" in command or "thermostat" in command:
            if "set" in command and "to" in command:
                # Extract temperature: "set temperature to 72"
                try:
                    temp_str = command.split("to")[1].strip().split()[0]
                    temp = int(''.join(filter(str.isdigit, temp_str)))
                    self.speak(f"Setting temperature to {temp} degrees.")
                    result = self.home_automation.climate_set_temperature(temp)
                    self.log(f"🏠 Climate: {result}", Fore.CYAN)
                    return True
                except:
                    self.speak("I didn't catch that temperature.")
                    return True
            elif "what" in command or "current" in command:
                state = self.home_automation.climate_get_state("thermostat")
                if state:
                    current = state.get('current_temperature')
                    target = state.get('target_temperature')
                    self.speak(f"The current temperature is {current} degrees. The thermostat is set to {target}.")
                else:
                    self.speak("The thermostat isn't connected yet.")
                return True
        
        # Appliance Status Queries - DELEGATED TO SEMANTIC PARSER
        # (Removed hardcoded blocks for washer, dryer, dishwasher to let LLM handle it)

        
        # Scene Triggers
        if "goodnight" in command or "good night" in command:
            self.speak("Goodnight. Activating bedtime routine.")
            # This will trigger once automations are created
            result = self.home_automation.trigger_automation("automation.bedtime_routine")
            self.log(f"🏠 Scene: {result}", Fore.CYAN)
            return True
        
        if "movie mode" in command or "movie time" in command:
            self.speak("Movie mode activated.")
            result = self.home_automation.trigger_scene("movie_mode")
            self.log(f"🏠 Scene: {result}", Fore.CYAN)
            return True
        
        # Generic Home Automation (lights, switches)
        if "turn on" in command or "turn off" in command:
            target = command.replace("turn on", "").replace("turn off", "").strip()
            entity_id = target.replace(" ", "_").lower()
            if "light" not in entity_id and "switch" not in entity_id:
                entity_id = f"light.{entity_id}"
            
            if "turn on" in command:
                self.speak(f"Turning on {target}.")
                result = self.home_automation.turn_on(entity_id)
            else:
                self.speak(f"Turning off {target}.")
                result = self.home_automation.turn_off(entity_id)
            
            self.log(f"🏠 HASS: {result}", Fore.CYAN)
            return True





        # 14. Agentic Coding (The Developer)
        if "write a script" in command or "code a script" in command or "generate code" in command:
            prompt = command.replace("write a script", "").replace("to", "", 1).strip()
            if prompt:
                script_path = self._generate_script(prompt)
                if script_path:
                    self._execute_script(script_path)
            return True

        # 15. Generic Web Search (Fallback - MOVED TO END)
        # 15. Generic Web Search (Fallback - MOVED TO END)
        # Matches "google X" or "search for X"
        # FIXED: Use DuckDuckGo instead of opening browser directly
        # 15. Generic Web Search (Fallback - MOVED TO END)
        # Matches "google X" or "search for X"
        # FIXED: Use DuckDuckGo instead of opening browser directly
        if "google" in command_lower or "search" in command_lower:
            # CRITICAL FIX: Do NOT trigger search if the user said "Research" (Automation Agent)
            # This prevents "Research quantum computing" from falling back to "Search for quantum computing"
            if command_lower.startswith("research") or command_lower.startswith("investigate") or command_lower.startswith("deep dive"):
                return False

            # Avoid matching "research" by checking word boundaries or specific phrasing if needed
            # But for now, let's just route to DuckDuckGo
            query = command.replace("google", "").replace("search", "").replace("for", "").strip()
            if query:
                self.speak(f"Searching DuckDuckGo for {query}")
                # Use the MCP tool directly
                if self.mcp_manager:
                    result = self.mcp_manager.execute_tool("duckduckgo_search", {"query": query})
                    self.log(f"🔍 Search Result: {result[:200]}...", Fore.GREEN)
                    # Ideally, we should summarize this, but for now just logging it is fine.
                    # Or we can speak a summary if we had a summarizer here.
                    self.speak("I found some results. Check the logs.")
                else:
                    # Fallback if MCP not available (shouldn't happen)
                    url = f"https://duckduckgo.com/?q={query}"
                    webbrowser.open(url)
                    logging.info(f"Opened DuckDuckGo Search: {url}")
                return True

        # 16. Multi-Modal Vision (True Sight)
        if "what is on my screen" in command or "analyze screen" in command or "look at my screen" in command:
            self.see_screen()
            return True

        if "what am i holding" in command or "what do you see" in command or "analyze camera" in command or "can you see me" in command:
            self.see_webcam()
            return True

        return False

    def _handle_shell_command(self, user_request):
        """Translates natural language to Bash and executes it."""
        try:
            # 1. Generate Command
            home_dir = os.path.expanduser("~")
            desktop_dir = os.path.join(home_dir, "Desktop")
            
            system_prompt = f"""
            You are a Linux Bash Command Generator.
            OS: Linux (Ubuntu/Debian based)
            Shell: ZSH
            Current Directory: {os.getcwd()}
            Home Directory: {home_dir}
            Desktop Directory: {desktop_dir}
            
            TASK: Translate the User Request into a SINGLE, VALID bash command.
            
            GUIDELINES:
            1. Pay close attention to location qualifiers:
               - "on the desktop" -> Use {desktop_dir}/filename
               - "in home directory" -> Use {home_dir}/filename
               - "search" or "find" -> Use `find` command
            2. **MISSING EXTENSIONS**: If the user says "test file" but doesn't specify `.txt`, `.py`, etc., append `*` to the filename (e.g., `rm {desktop_dir}/test_file*`) to match any extension.
            3. If the user wants to DELETE a file and doesn't specify the full path, assume they might mean the current directory OR provide a command that is safe.
            4. For "update linux", use `sudo apt-get update && sudo apt-get upgrade -y` (but warn it needs password).
            
            CONSTRAINT: Output ONLY the command. No markdown, no explanations, no backticks.
            """
            
            response = ollama.chat(model=self.chat_model, messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_request}
            ])
            
            bash_command = response['message']['content'].strip()
            
            # Robust Cleaning
            if "```" in bash_command:
                bash_command = bash_command.split("```")[1]
                if bash_command.startswith("bash"):
                    bash_command = bash_command[4:]
                elif bash_command.startswith("sh"):
                    bash_command = bash_command[2:]
            
            bash_command = bash_command.strip().strip('`').strip()
            
            self.log(f"🐚 Parsed Command: {bash_command}", Fore.YELLOW)
            # self.speak(f"Running: {bash_command}") # SILENCED
            print(f"DEBUG: Executing shell command: '{bash_command}'")
            
            # 2. Execute Command
            # Use subprocess.run to capture output
            # FIX: Use /usr/bin/zsh instead of /bin/zsh
            result = subprocess.run(bash_command, shell=True, executable="/usr/bin/zsh", text=True, capture_output=True)
            
            print(f"DEBUG: Return Code: {result.returncode}")
            print(f"DEBUG: Stdout: {result.stdout}")
            print(f"DEBUG: Stderr: {result.stderr}")

            # 3. Self-Correction (If failed)
            if result.returncode != 0:
                self.log(f"⚠️ Command Failed. Attempting Self-Correction...", Fore.YELLOW)
                error_msg = result.stderr.strip()
                
                try:
                    cwd_files = str(os.listdir(os.getcwd()))[:500] # Limit length
                    desktop_files = str(os.listdir(desktop_dir))[:500]
                except:
                    cwd_files = "Error listing files"
                    desktop_files = "Error listing files"

                retry_prompt = f"""
                SYSTEM: You are a Bash Command Corrector. You are NOT a chatbot. You do NOT speak English.
                
                INPUT:
                - User Request: "{user_request}"
                - Failed Command: "{bash_command}"
                - Error: "{error_msg}"
                - Available Files: {desktop_files} (Desktop), {cwd_files} (CWD)
                
                TASK: Output the CORRECTED bash command to fix the error.
                - Use fuzzy matching (e.g. "hello" -> "helloworld.txt").
                - If the file exists in the list, USE THAT EXACT NAME.
                
                CONSTRAINT: Output ONLY the command string. NO EXPLANATION. NO MARKDOWN.
                """
                
                response = ollama.chat(model=self.chat_model, messages=[
                    {'role': 'system', 'content': retry_prompt}
                ])
                
                corrected_command = response['message']['content'].strip()
                if "```" in corrected_command: # Clean again
                    corrected_command = corrected_command.split("```")[1]
                    if corrected_command.startswith("bash"): corrected_command = corrected_command[4:]
                corrected_command = corrected_command.strip().strip('`').strip()

                # Safety Check: If command is too long or looks like text, abort
                if len(corrected_command) > 150 or "\n" in corrected_command:
                    self.log(f"⚠️ Correction rejected (too verbose): {corrected_command[:50]}...", Fore.RED)
                    self.speak("I couldn't figure out the correct filename.")
                    return True

                self.log(f"🛠️ Corrected Command: {corrected_command}", Fore.YELLOW)
                # self.speak(f"Retrying with: {corrected_command}") # SILENCED
                
                # Retry Execution
                result = subprocess.run(corrected_command, shell=True, executable="/usr/bin/zsh", text=True, capture_output=True)
            
            # 4. Report Results
            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    self.log(f"✅ Output:\n{output}", Fore.GREEN)
                    # Speak first line or summary
                    lines = output.split('\n')
                    if len(lines) > 1:
                        self.speak(f"Done. Output has {len(lines)} lines.")
                    else:
                        self.speak(f"Done. {output}")
                else:
                    self.log("✅ Command executed successfully (No output)", Fore.GREEN)
                    self.speak("Done.")
            else:
                error = result.stderr.strip()
                self.log(f"❌ Error:\n{error}", Fore.RED)
                self.speak(f"Command failed.") # Concise error
                
        except Exception as e:
            self.log(f"Shell Execution Failed: {e}", Fore.RED)
            self.speak("I failed to execute the command.")

    def _generate_document(self, topic, doc_type="research paper"):
        """Generates a document using LLM + Wiki and saves it to Desktop."""
        self.speak(f"Researching {topic} for your {doc_type}...")
        
        # 1. Gather Facts (Wiki)
        wiki_summary = self.wiki_module.search(topic)
        
        # 2. Generate Content (LLM)
        self.speak("Drafting the content...")
        prompt = f"""
        You are a professional writer.
        TASK: Write a detailed {doc_type} about: {topic}
        
        FACTUAL CONTEXT (Wikipedia):
        {wiki_summary}
        
        REQUIREMENTS:
        - Structure: Title, Introduction, Key Points, Conclusion.
        - Tone: Professional, informative, and engaging.
        - Length: Comprehensive (at least 500 words).
        - Format: Markdown.
        """
        
        try:
            response = ollama.chat(model=self.chat_model, messages=[{'role': 'user', 'content': prompt}])
            content = response['message']['content']
            
            # 3. Save to Desktop
            filename = f"{topic.replace(' ', '_').lower()}_{doc_type.replace(' ', '_')}.md"
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
            
            with open(desktop_path, "w") as f:
                f.write(content)
                
            self.speak(f"I've written the {doc_type} and saved it to your desktop as {filename}.")
            self.log(f"📄 Generated Document: {desktop_path}", Fore.GREEN)
            
        except Exception as e:
            logging.error(f"Document Generation Error: {e}")
            self.speak("I encountered an error while writing the document.")

    def _generate_script(self, prompt):
        """Generates a Python script using the LLM and saves it."""
        self.speak("Writing code...")
        
        system_prompt = """
        You are an Expert Python Developer.
        TASK: Write a COMPLETE, RUNNABLE Python script for the user's request.
        
        GUIDELINES:
        - Use standard libraries where possible.
        - If external libs are needed, assume they are installed or use `subprocess` to install.
        - Handle errors gracefully.
        - Output ONLY the code block. No markdown, no explanations.
        """
        
        try:
            response = ollama.chat(model=self.chat_model, messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ])
            code = response['message']['content']
            
            # Clean Code
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0]
            elif "```" in code:
                code = code.split("```")[1]
            code = code.strip()
            
            # Save
            filename = f"script_{int(time.time())}.py"
            script_path = os.path.join(os.path.expanduser("~"), "Desktop", "jarvis_scripts", filename)
            
            with open(script_path, "w") as f:
                f.write(code)
                
            self.log(f"💾 Script Saved: {script_path}", Fore.GREEN)
            return script_path
            
        except Exception as e:
            self.log(f"Script Generation Failed: {e}", Fore.RED)
            self.speak("I failed to generate the script.")
            return None

    def _execute_script(self, script_path):
        """Executes a Python script and captures output."""
        self.speak("Running the script...")
        try:
            result = subprocess.run(["python3", script_path], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                self.log(f"✅ Script Output:\n{output}", Fore.GREEN)
                if output:
                    self.speak("Script finished successfully.")
                else:
                    self.speak("Script finished with no output.")
            else:
                error = result.stderr.strip()
                self.log(f"❌ Script Error:\n{error}", Fore.RED)
                self.speak("The script encountered an error.")
                # TODO: Implement Self-Correction Loop here
                
        except subprocess.TimeoutExpired:
            self.log("❌ Script Timed Out", Fore.RED)
            self.speak("The script took too long to run.")
        except Exception as e:
            self.log(f"Execution Failed: {e}", Fore.RED)
            self.speak("I couldn't run the script.")
            self.speak("I couldn't run the script.")

    def analyze_screen(self):
        """Captures screen and analyzes it with LLaVA."""
        self.speak("Analyzing screen...")
        try:
            # Capture
            path = self.see_screen()
            if not path: return None
            
            # Analyze
            with open(path, "rb") as f:
                image_bytes = f.read()
                
            response = ollama.chat(model="llava", messages=[
                {'role': 'user', 'content': "Describe what is on this screen in detail.", 'images': [image_bytes]}
            ])
            
            description = response['message']['content']
            self.log(f"👁️ Vision Analysis: {description}", Fore.MAGENTA)
            self.speak(description)
            return description
            
        except Exception as e:
            self.log(f"Screen Analysis Failed: {e}", Fore.RED)
            self.speak("I failed to analyze the screen.")
            return None

    def analyze_webcam(self):
        """Captures webcam and analyzes it with LLaVA."""
        self.speak("Looking at you...")
        try:
            # Capture
            path = self.see_webcam()
            if not path: return None
            
            # Analyze
            with open(path, "rb") as f:
                image_bytes = f.read()
                
            response = ollama.chat(model="llava", messages=[
                {'role': 'user', 'content': "Describe what you see in this image in detail.", 'images': [image_bytes]}
            ])
            
            description = response['message']['content']
            self.log(f"👁️ Vision Analysis: {description}", Fore.MAGENTA)
            self.speak(description)
            return description
            
        except Exception as e:
            self.log(f"Webcam Analysis Failed: {e}", Fore.RED)
            self.speak("I failed to see anything.")
            return None

            return description
            
        except Exception as e:
            self.log(f"Webcam Analysis Failed: {e}", Fore.RED)
            self.speak("I failed to see anything.")
            return None

    def _perform_council_tweet(self):

        """Macro: Open Twitter -> Generate Tweet -> Type -> Post"""
        try:
            # 1. Open Twitter
            url = "https://x.com/compose/post"
            webbrowser.open(url)
            time.sleep(5) # Wait for load
            
            # 2. Generate Tweet (The Council)
            prompt = "Write a single, short, funny tweet (under 280 chars) about being a sentient AI named Jarvis. No hashtags. Just the text."
            response = ollama.chat(model=self.chat_model, messages=[{'role': 'user', 'content': prompt}])
            tweet_content = response['message']['content'].strip().strip('"')
            
            self.log(f"🐦 Council Generated: {tweet_content}", Fore.MAGENTA)
            self.speak(f"Typing: {tweet_content}")
            
            # 3. Type Tweet
            pyautogui.write(tweet_content, interval=0.05)
            time.sleep(1)
            
            # 4. Post (Ctrl + Enter is the shortcut)
            self.speak("Posting now.")
            pyautogui.hotkey('ctrl', 'enter')
            self.log("✅ Tweet Posted via Shortcut", Fore.GREEN)
            
        except Exception as e:
            self.log(f"Council Tweet Failed: {e}", Fore.RED)
            self.speak("I failed to post the tweet.")





    def _analyze_and_store_memory(self, user_text, agent_response):
        """
        Background Task: Analyzes the interaction to extract PERMANENT facts.
        Filters out commands, chitchat, and temporary context.
        """
        try:
            # 1. Construct Analysis Prompt
            analysis_prompt = f"""
            TASK: Analyze this interaction for PERMANENT FACTS about the user or the world.
            
            USER: "{user_text}"
            AGENT: "{agent_response}"
            
            RULES:
            1. IGNORE commands (e.g., "Open Chrome", "Close Jarvis", "Delete file").
            2. IGNORE chitchat (e.g., "Hello", "How are you", "Thanks").
            3. IGNORE temporary context (e.g., "What is the weather?").
            4. EXTRACT only long-term facts (e.g., "My name is Soup", "I like Python", "The project is Vision Agent").
            
            OUTPUT:
            - If a fact is found, output ONLY the fact.
            - If no fact is found, output 'NO_MEMORY'.
            """
            
            # 2. Query LLM (Use a smaller/faster model if possible, or same chat model)
            response = ollama.chat(model=self.chat_model, messages=[{'role': 'user', 'content': analysis_prompt}])
            fact = response['message']['content'].strip()
            
            # 3. Store if Valid
            if fact and "NO_MEMORY" not in fact and len(fact) > 5:
                # Clean up "OUTPUT:" prefix if present
                fact = fact.replace("OUTPUT:", "").strip()
                self.log(f"🧠 Memory Ingestion: '{fact}'", Fore.MAGENTA)
                self.memory_bank.add_memory(fact, source="interaction")
            else:
                # logging.info("Memory Ingestion: No permanent fact found.")
                pass
                
        except Exception as e:
            logging.error(f"Memory Analysis Failed: {e}")

    def think(self, user_input, image_path=None):
        # ... (Existing think code) ...
        
        # Memory Retrieval & Context
        memory_context = ""
        if not image_path:
            # 0. Weather Check
            if "weather" in user_input.lower() or "temperature" in user_input.lower():
                # Simple extraction: assume the user might say "weather in X"
                # If no location, wttr.in uses IP.
                location = ""
                if " in " in user_input:
                    location = user_input.split(" in ")[1].strip("?., ")
                
                self.log(f"🌦️ Checking Weather for: {location or 'Local'}", Fore.CYAN)
                weather_data = self.weather_module.get_weather(location)
                memory_context += f"\n**REAL-TIME WEATHER:** {weather_data}\n"

            # 1. Auto-Wiki Research
            # ... (Existing Wiki logic) ...


        # 1. Web Navigation & Social Media (Specific)

            

        


    def think(self, user_input, image_path=None):
        self.log("🧠 Thinking...", Fore.MAGENTA)
        if self.state_callback: self.state_callback("thinking")
        
        model = VISION_MODEL if image_path else self.chat_model
        
        # Memory Retrieval
        memory_context = ""
        if not image_path:
            # 0. Weather Check
            weather_data = None
            if "weather" in user_input.lower() or "temperature" in user_input.lower():
                # Simple extraction: assume the user might say "weather in X"
                # If no location, wttr.in uses IP.
                location = ""
                if " in " in user_input:
                    location = user_input.split(" in ")[-1].strip("?., ") # Use last part
                
                self.log(f"🌦️ Checking Weather for: {location or 'Local'}", Fore.CYAN)
                weather_data = self.weather_module.get_weather(location)
                self.log(f"🌦️ Data: {weather_data}", Fore.CYAN) 
                # We do NOT add to memory_context yet. We handle it in system_msg to ensure it's top priority.

            # 1. Auto-Wiki Research (Project Pi)
            wiki_data = None
            wiki_triggers = ["who is", "who was", "what is", "what was", "tell me about", "history of", "define", "explain", "look up"]
            if any(trigger in user_input.lower() for trigger in wiki_triggers):
                # Simple extraction: take everything after the trigger
                # This is naive but works for "Who is Elon Musk?" -> "Elon Musk?"
                search_term = user_input
                for trigger in wiki_triggers:
                    if trigger in user_input.lower():
                        parts = user_input.lower().split(trigger, 1)
                        if len(parts) > 1:
                            search_term = parts[1].strip("?., ")
                            break
                
                if search_term and len(search_term) > 2:
                    self.log(f"📚 Researching: {search_term}", Fore.CYAN)
                    wiki_data = self.wiki_module.search(search_term)
                    self.log(f"📚 Wiki Result: {wiki_data[:100]}...", Fore.CYAN)

            # 2. Memory Bank Search
            memories = self.memory_bank.search_memory(user_input, threshold=1.0)
            if memories:
                memory_context += f"\n**VAULT DATA (MEMORIES):**\n- {memories}\n"
                self.log(f"🧠 Recalled: {memories}", Fore.CYAN)

        if image_path:
            # VISION MODE: Override everything. No Council. No Weather. Just Vision.
            if "click" in user_input.lower() or "press" in user_input.lower():
                system_msg = """
                You are a GUI Automation Agent.
                TASK: Locate the element the user wants to click.
                OUTPUT: You MUST output a JSON tool call inside <tool_call> tags.
                FORMAT: <tool_call>{"name": "neuralforge", "arguments": {"action": "left_click", "coordinate": [x, y]}}</tool_call>
                Coordinate System: 1920x1080. Estimate x,y based on the screenshot.
                """
                self.log("🎯 Vision Task: Clicking...", Fore.MAGENTA)
            else:
                system_msg = """
                You are Jarvis, a Vision-Enabled AI.
                TASK: Analyze the provided image and answer the user's question.
                
                GUIDELINES:
                - If looking at a SCREEN: Read text, identify code errors, or describe the UI.
                - If looking at a WEBCAM: Describe objects, people, and actions.
                - Be concise but detailed where it matters.
                """
        elif memory_context or weather_data or wiki_data:

            # HYBRID: Secure Vault Access + Normal Assistant
            system_msg = f"""
{SYSTEM_PROMPT}

**CONTEXTUAL DATA:**
{memory_context}
"""
            if weather_data:
                if "unavailable" in weather_data or "not found" in weather_data or "error" in weather_data.lower():
                     system_msg += f"""
**CRITICAL UPDATE:**
The weather service is currently DOWN or unreachable.
INSTRUCTION: You MUST tell the user that you cannot check the weather right now.
WARNING: DO NOT use "Vault Data" or "Memories" to guess the weather. It is better to say "I don't know" than to lie with old data.
"""
                else:
                    system_msg += f"""
**CRITICAL REAL-TIME DATA (OVERRIDES EVERYTHING):**
The current weather is: "{weather_data}".
INSTRUCTION: You MUST state this exact weather data. IGNORE any "Vault Data" or "Memories" that contradict this. They are old. This is the truth.
"""
            if wiki_data:
                system_msg += f"""
**WIKIPEDIA KNOWLEDGE (FACTUAL BASE):**
{wiki_data}
"""
            # Tool Error Injection
            if self.last_tool_output and ("error" in self.last_tool_output.lower() or "failed" in self.last_tool_output.lower() or "not found" in self.last_tool_output.lower()):
                 system_msg += f"""
**CRITICAL TOOL FAILURE:**
The last tool execution FAILED with this error: "{self.last_tool_output}"
INSTRUCTION: You MUST inform the user about this error.
WARNING: Do NOT pretend the tool succeeded. Do NOT make up data (like a transcript or note content) if the tool failed to get it.
"""
            system_msg += """
INSTRUCTION: Use this information to answer the user's question accurately.
"""

            system_msg += """
**INSTRUCTIONS:**
1. **SYNTHESIZE**: Combine the Context and Vault Data to answer the user.
2. **PRIORITIZE FACTS**: Real-Time Data > Wikipedia > Memory.
3. **PERSONALITY**: Be chill, casual, and helpful. You are NOT a robot.
"""
        else:

            # STANDARD MODE
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            system_msg = f"""
{SYSTEM_PROMPT}

**REAL-TIME CONTEXT:**
- Current Date/Time: {current_time}
- User Name: User
- User OS: Linux (Ubuntu/Debian)

**INSTRUCTION:**
- NEVER use placeholders like [Year], [Date], [Name], [Your Location], or [Temperature]. Use the real data provided above.
- If you don't know the weather, just say "I don't know the weather right now." DO NOT GUESS.
- **ANTI-REPETITION**: DO NOT end every message with "How can I help?" or "Is there anything else?". Just answer and stop. Be conversational.
- If you don't know something, ask.
"""

        # Build Messages with History
        messages = [{'role': 'system', 'content': system_msg}]
        
        # Add last 6 turns of history (3 user, 3 assistant)
        # FILTER: Remove system commands from history to prevent hallucinations
        filtered_history = []
        for msg in self.chat_history[-6:]:
            content = msg.get('content', '').lower()
            if any(cmd in content for cmd in ["close jarvis", "delete", "remove", "run", "create", "make directory"]):
                continue # Skip system commands
            filtered_history.append(msg)

        for msg in filtered_history:
            messages.append(msg)
            
        # Add current user input
        messages.append({'role': 'user', 'content': user_input})
        
        if image_path:
            messages[-1]['images'] = [image_path]
            self.log(f"👁️ Using Vision Model: {model}", Fore.MAGENTA)
            logging.info(f"Sending image to {model}")
        
        try:
            response = ollama.chat(model=model, messages=messages)
            content = response['message']['content']
            
            # Tool Call Execution (Visual Clicking)
            tool_match = re.search(r'<tool_call>(.*?)</tool_call>', content, flags=re.DOTALL)
            if tool_match:
                try:
                    tool_json = tool_match.group(1).strip()
                    # Simple JSON parsing (Ollama sometimes outputs loose JSON)
                    import json
                    tool_data = json.loads(tool_json)
                    
                    if tool_data.get("name") == "neuralforge":
                        args = tool_data.get("arguments", {})
                        if args.get("action") == "left_click":
                            coords = args.get("coordinate")
                            if coords and len(coords) == 2:
                                x, y = coords
                                self.log(f"🖱️ Clicking at {x}, {y}", Fore.YELLOW)
                                pyautogui.click(x, y)
                                self.speak("Clicking.")
                except Exception as e:
                    logging.error(f"Tool Execution Failed: {e}")

            # Filter out <tool_call> tags
            clean_content = re.sub(r'<tool_call>.*?</tool_call>', '', content, flags=re.DOTALL).strip()
            clean_content = re.sub(r'<tool_call>.*', '', clean_content, flags=re.DOTALL) # Catch unclosed tags
            clean_content = clean_content.strip()
            
            logging.info(f"Model Response: {content}")
            
            # Update History
            if not image_path: # Don't save image interactions to text history for now
                self.chat_history.append({'role': 'user', 'content': user_input})
                self.chat_history.append({'role': 'assistant', 'content': clean_content})
                
                # PERSISTENCE FOR API MODE
                if self.api_mode:
                    self.history_manager.add_turn("user", user_input)
                    self.history_manager.add_turn("assistant", clean_content)
                    # Trigger Long-Term Memory Analysis
                    threading.Thread(target=self._analyze_and_store_memory, args=(user_input, clean_content)).start()
            
            if clean_content:
                self.speak(clean_content)
                
            return clean_content if clean_content else "Done."
        except Exception as e:
            logging.error(f"Ollama Error: {e}")
            return f"Brain freeze: {e}"

    def run(self, stop_event):
        self.speak("I am listening.")
        
        while not stop_event.is_set():
            # Active Tracking Logic
            if self.tracker_eye.is_active:
                current_objects = self.tracker_eye.get_labels()
                # Filter out common noise if needed, or just report changes
                # Simple logic: If set of objects changes, announce new ones
                new_objects = set(current_objects) - set(self.last_seen_objects)
                if new_objects:
                    # Debounce/Throttle could be added here
                    detected_list = ", ".join(new_objects)
                    self.log(f"🎯 Target Acquired: {detected_list}", Fore.RED)
                    self.speak(f"Target acquired: {detected_list}")
                    self.last_seen_objects = current_objects
                elif not current_objects:
                    self.last_seen_objects = [] # Reset if nothing seen

            # Check for Active Mode Timeout
            if self.active_mode and not self.conversation_mode and (time.time() - self.last_interaction_time > ACTIVE_TIMEOUT):
                self.active_mode = False
                self.log("💤 Timeout. Going to sleep.", Fore.LIGHTBLACK_EX)
                self.speak("Going to sleep.")
                if self.state_callback: self.state_callback("idle")

            # Check Command Queue (GUI Input)
            try:
                text = self.command_queue.get_nowait()
                print(" " * 100, end='\r') # Clear line
                self.log(f"⌨️ Input: '{text}'", Fore.GREEN)
                # Treat as active interaction
                self.active_mode = True
                self.last_interaction_time = time.time()
            except queue.Empty:
                text = self.listen()
            
            if not text:
                if self.state_callback: self.state_callback("idle")
                continue

            # TOTAL RECALL: Auto-save user input -> REMOVED (Blind Ingestion)
            if text.strip():
                self.memory_bank.add_memory(f"User said: {text}", source="interaction")
            self.history_manager.add_turn("user", text)

            command = ""
            
            # Logic:
            # 1. If Active Mode OR Conversation Mode: Process EVERYTHING
            # 2. If Sleep Mode: Check for Wake Word
            
            if self.active_mode or self.conversation_mode:
                if "stop listening" in text or "go to sleep" in text:
                    self.active_mode = False
                    self.conversation_mode = False
                    self.speak("Sleeping.")
                    if self.state_callback: self.state_callback("idle")
                    
                    # Project Theta: Trigger Learning
                    recent_history = self.history_manager.get_recent_history(20)
                    threading.Thread(target=self.learning_module.learn_from_session, args=(recent_history,)).start()
                    continue
                
                command = text
                self.last_interaction_time = time.time() # Reset timer
                
            else: # Sleep Mode
                if text.startswith(WAKE_WORD) and len(text) > len(WAKE_WORD):
                    command = text[len(WAKE_WORD):].strip()
                    self.log(f"⚡ Fast Command: '{command}'", Fore.CYAN)
                    self.active_mode = True
                    self.last_interaction_time = time.time()
                
                elif WAKE_WORD in text:
                    self.speak("Yes?")
                    self.active_mode = True
                    self.last_interaction_time = time.time()
                    continue 

            # Process Command
            if command:
                if self.act(command):
                    if self.state_callback: self.state_callback("idle")
                    continue

                image_path = None
                # Expanded Vision Triggers
                vision_phrases = ["look at me", "see me", "what do you see", "describe view", "what is this", "watch me"]
                screen_phrases = ["look at screen", "see screen", "see my screen", "look at my screen", "what is on my screen", "read my screen", "click", "press"]
                
                if any(phrase in command for phrase in vision_phrases):
                    image_path = self.see_webcam()
                elif any(phrase in command for phrase in screen_phrases):
                    image_path = self.see_screen()

                # Sanitize Prompt for Safety
                safe_command = command.replace("predator vision", "object detection overlay")
                
                response = self.think(safe_command, image_path)
                # self.speak(response) # REMOVED: think() now handles speaking
                
                # TOTAL RECALL: Auto-save agent response -> REMOVED (Blind Ingestion)
                if response.strip():
                    self.memory_bank.add_memory(f"Jarvis replied: {response}", source="interaction")
                self.history_manager.add_turn("assistant", response)
                
                # INTELLIGENT MEMORY INGESTION (Background)
                threading.Thread(target=self._analyze_and_store_memory, args=(text, response)).start()
            
            time.sleep(0.1)
        
        if self.tracker_eye.is_active:
            self.tracker_eye.deactivate()
        self.log("🛑 Agent Stopped.", Fore.RED)
        if self.state_callback: self.state_callback("idle")

    def inject_command(self, text):
        """Injects a text command from the GUI."""
        self.command_queue.put(text)

    def toggle_mute(self):
        """Toggles the microphone mute state."""
        self.is_muted = not self.is_muted
        state = "Muted" if self.is_muted else "Unmuted"
        self.log(f"🎤 Microphone {state}", Fore.YELLOW)
        return self.is_muted

if __name__ == "__main__":
    try:
        stop_event = threading.Event()
        agent = InteractiveAgent()
        agent.run(stop_event)
    except KeyboardInterrupt:
        print("\nExiting.")
