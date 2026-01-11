"""
FastAPI WebSocket Server for Azure OpenAI Realtime API
Provides text and audio chat via WebSocket connections
"""

import os
import asyncio
import base64
from datetime import datetime
from typing import List, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Realtime Chat API")

# Enable CORS for React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Azure OpenAI config
ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-realtime")
CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-5.1")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:5173").split(",")

# In-memory chat history storage
chat_history: List[Dict] = []

def get_openai_client():
    """Create OpenAI client with Azure credentials."""
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
    base_url = ENDPOINT.replace("https://", "wss://").rstrip("/") + "/openai/v1"
    return AsyncOpenAI(websocket_base_url=base_url, api_key=token_provider())


def get_chat_client():
    """Create OpenAI client for chat completions."""
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
    base_url = ENDPOINT.rstrip("/") + "/openai/deployments/" + CHAT_DEPLOYMENT
    return AsyncOpenAI(
        base_url=base_url,
        api_key=token_provider(),
        default_query={"api-version": "2024-08-01-preview"}
    )

@app.websocket("/ws/text")
async def text_chat(websocket: WebSocket):
    """WebSocket endpoint for text chat."""
    await websocket.accept()
    is_open = True
    
    async def safe_send(data):
        """Safely send data only if WebSocket is open."""
        nonlocal is_open
        if is_open:
            try:
                await websocket.send_json(data)
            except Exception:
                is_open = False
    
    try:
        client = get_openai_client()
        
        async with client.realtime.connect(model=DEPLOYMENT) as connection:
            # Configure for text mode
            await connection.session.update(session={
                "type": "realtime",
                "instructions": "You are a helpful assistant. Be concise.",
                "output_modalities": ["text"]
            })
            
            await safe_send({"type": "connected"})
            
            # Handle incoming messages
            async def handle_client_messages():
                nonlocal is_open
                try:
                    while is_open:
                        data = await websocket.receive_json()
                        if data["type"] == "message":
                            await connection.conversation.item.create(
                                item={"type": "message", "role": "user", 
                                      "content": [{"type": "input_text", "text": data["text"]}]}
                            )
                            await connection.response.create()
                except WebSocketDisconnect:
                    is_open = False
                except Exception as e:
                    is_open = False
                    print(f"Error in handle_client_messages: {e}")
            
            # Handle AI responses
            async def handle_ai_responses():
                try:
                    async for event in connection:
                        if not is_open:
                            break
                        if event.type == "response.output_text.delta":
                            await safe_send({"type": "text_delta", "delta": event.delta})
                        elif event.type == "response.done":
                            await safe_send({"type": "response_done"})
                except WebSocketDisconnect:
                    pass
                except Exception as e:
                    print(f"Error in handle_ai_responses: {e}")
            
            await asyncio.gather(handle_client_messages(), handle_ai_responses())
            
    except Exception as e:
        print(f"Error in text_chat: {e}")
        if is_open:
            try:
                await websocket.send_json({"type": "error", "message": str(e)})
            except:
                pass
    finally:
        is_open = False
        try:
            await websocket.close()
        except:
            pass


@app.websocket("/ws/audio")
async def audio_chat(websocket: WebSocket):
    """WebSocket endpoint for audio chat."""
    await websocket.accept()
    client = get_openai_client()
    is_open = True
    
    async def safe_send(data):
        """Safely send data only if WebSocket is open."""
        nonlocal is_open
        if is_open:
            try:
                await websocket.send_json(data)
            except Exception:
                is_open = False
    
    try:
        async with client.realtime.connect(model=DEPLOYMENT) as connection:
            # Configure for audio mode
            await connection.session.update(session={
                "type": "realtime",
                "instructions": "You are a helpful assistant. Keep responses brief.",
                "output_modalities": ["audio"],
                "audio": {
                    "input": {
                        "transcription": {"model": "whisper-1"},
                        "format": {"type": "audio/pcm", "rate": 24000},
                        "turn_detection": {
                            "type": "server_vad",
                            "threshold": 0.5,
                            "prefix_padding_ms": 300,
                            "silence_duration_ms": 500,
                            "create_response": True
                        }
                    },
                    "output": {
                        "voice": "alloy",
                        "format": {"type": "audio/pcm", "rate": 24000}
                    }
                }
            })
            
            await safe_send({"type": "connected"})
            
            # Handle incoming audio
            async def handle_client_audio():
                nonlocal is_open
                try:
                    while is_open:
                        data = await websocket.receive_json()
                        if data["type"] == "audio":
                            await connection.input_audio_buffer.append(audio=data["audio"])
                except WebSocketDisconnect:
                    is_open = False
            
            # Handle AI responses
            async def handle_ai_audio():
                nonlocal is_open
                try:
                    async for event in connection:
                        if not is_open:
                            break
                        if event.type == "response.audio.delta":
                            await safe_send({"type": "audio_delta", "delta": event.delta})
                        elif event.type == "conversation.item.input_audio_transcription.completed":
                            await safe_send({"type": "user_transcript", "text": event.transcript})
                        elif event.type == "response.output_audio_transcript.delta":
                            await safe_send({"type": "assistant_transcript_delta", "delta": event.delta})
                        elif event.type == "input_audio_buffer.speech_started":
                            await safe_send({"type": "speech_started"})
                        elif event.type == "response.done":
                            await safe_send({"type": "response_done"})
                except WebSocketDisconnect:
                    is_open = False
            
            await asyncio.gather(handle_client_audio(), handle_ai_audio())
            
    except WebSocketDisconnect:
        pass
    finally:
        is_open = False


@app.get("/")
async def root():
    return {"status": "ok", "message": "Realtime Chat API"}


@app.get("/chat-history")
async def get_chat_history():
    """Get all chat sessions."""
    return {"history": chat_history}


@app.post("/generate-caption")
async def generate_caption(data: Dict):
    """Generate a short caption for chat messages using GPT."""
    messages = data.get("messages", [])
    if not messages:
        return {"caption": "New Chat"}
    
    # Extract user messages for context
    user_messages = [m for m in messages if m.get("role") == "user"]
    context = "\n".join([m.get("content", "")[:100] for m in user_messages[:3]])  # First 3 user messages
    
    try:
        client = get_chat_client()
        response = await client.chat.completions.create(
            model="gpt-4o",  # Model name doesn't matter for Azure, deployment is in URL
            messages=[
                {"role": "system", "content": "Generate a very short (3-5 words) title summarizing this conversation. No quotes, no punctuation at the end."},
                {"role": "user", "content": f"Conversation:\n{context}"}
            ],
            max_completion_tokens=20,
            temperature=0.7
        )
        caption = response.choices[0].message.content.strip()
        return {"caption": caption}
    except Exception as e:
        print(f"Error generating caption: {e}")
        # Fallback to first message
        first_message = user_messages[0].get("content", "New Chat") if user_messages else "New Chat"
        return {"caption": first_message[:30] + ("..." if len(first_message) > 30 else "")}


@app.post("/chat-history")
async def add_chat_session(session: Dict):
    """Add a new chat session to history."""
    chat_session = {
        "id": len(chat_history) + 1,
        "summary": session.get("summary", "New Chat"),
        "timestamp": datetime.now().isoformat(),
        "messages": session.get("messages", [])
    }
    chat_history.append(chat_session)
    return {"id": chat_session["id"], "message": "Chat session added"}


@app.put("/chat-history/{session_id}")
async def update_chat_session(session_id: int, session: Dict):
    """Update an existing chat session."""
    global chat_history
    for chat in chat_history:
        if chat["id"] == session_id:
            chat["summary"] = session.get("summary", chat["summary"])
            chat["messages"] = session.get("messages", chat["messages"])
            chat["timestamp"] = datetime.now().isoformat()
            return {"id": session_id, "message": "Chat session updated"}
    return {"error": "Chat session not found"}


@app.delete("/chat-history/{session_id}")
async def delete_chat_session(session_id: int):
    """Delete a chat session."""
    global chat_history
    chat_history = [s for s in chat_history if s["id"] != session_id]
    return {"message": "Chat session deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
