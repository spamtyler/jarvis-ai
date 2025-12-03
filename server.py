from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import Jarvis
from interactive_agent import InteractiveAgent

# Setup Logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agent in API Mode (No Voice/Vision Hardware Hooks)
print("Initializing Jarvis in API Mode...")
agent = InteractiveAgent(api_mode=True)
print("Jarvis Online.")

# Models
class ChatRequest(BaseModel):
    message: str

from fastapi.concurrency import run_in_threadpool

@app.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message
    print(f"📱 Mobile User: {user_message}")
    
    response_text = ""
    
    # Run synchronous agent methods in a threadpool to avoid blocking the event loop
    try:
        print(f"📋 Attempting act() with command: '{user_message}'")
        # act() is blocking, run in thread
        act_result = await run_in_threadpool(agent.act, user_message)
        print(f"📋 act() returned: {act_result}")
        
        if act_result:
            if hasattr(agent, 'last_response') and agent.last_response:
                response_text = agent.last_response
                print(f"📋 Using last_response: '{response_text[:50]}...'")
            else:
                response_text = "Command executed."
        else:
            print("📋 act() returned False, using think()")
            # think() is blocking, run in thread
            response_text = await run_in_threadpool(agent.think, user_message)
    except Exception as e:
        print(f"❌ ERROR in act(): {e}")
        import traceback
        traceback.print_exc()
        response_text = await run_in_threadpool(agent.think, user_message)
    
    
    # Capture Audio
    audio_data = None
    if hasattr(agent, 'last_audio'):
        audio_data = agent.last_audio
        if audio_data:
            print(f"🎤 Audio Data Captured: {len(audio_data)} chars")
        else:
            print("🎤 Audio Data is None/Empty")
        agent.last_audio = None # Clear it
    else:
        print("🎤 No last_audio attribute found on agent")
        
    return {"response": response_text, "audio": audio_data}

# Serve Static Files (Mobile UI)
os.makedirs("mobile", exist_ok=True)
app.mount("/", StaticFiles(directory="mobile", html=True), name="mobile")

if __name__ == "__main__":
    # Use HTTPS to allow Microphone access on mobile
    uvicorn.run(app, host="0.0.0.0", port=8000, ssl_keyfile="key.pem", ssl_certfile="cert.pem")
