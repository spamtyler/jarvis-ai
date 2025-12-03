import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Add project root to path
sys.path.append("/home/soup/.gemini/antigravity/playground/orbital-eagle")

from vision_agent.interactive_agent import InteractiveAgent

def test_automation():
    print("🚀 Starting Test: Research Command")
    agent = InteractiveAgent()
    
    # Mock the speak method to avoid audio generation delay/errors
    agent.speak = lambda x: print(f"🤖 Jarvis (Mock): {x}")
    
    command = "Research quantum computing, summarize it, and save to my vault"
    print(f"⌨️ Input: '{command}'")
    
    agent.act(command)

if __name__ == "__main__":
    test_automation()
