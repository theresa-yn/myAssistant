from __future__ import annotations

import json
import asyncio
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

from .memory_store import MemoryStore
from .ai_response import AIResponseSystem


class WebAssistant:
    def __init__(self):
        self.app = FastAPI(title="MyAssistant Web", version="0.1.0")
        self.store = MemoryStore()
        self.ai_system = AIResponseSystem(self.store)
        self.active_connections: list[WebSocket] = []
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def get_homepage():
            return """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>MyAssistant - Voice Memory</title>
                <style>
                    * {
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }
                    
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                    }
                    
                    .container {
                        text-align: center;
                        background: rgba(255, 255, 255, 0.1);
                        backdrop-filter: blur(10px);
                        border-radius: 20px;
                        padding: 40px;
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        max-width: 400px;
                        width: 90%;
                    }
                    
                    h1 {
                        font-size: 2.5rem;
                        margin-bottom: 20px;
                        font-weight: 300;
                    }
                    
                    .mic-button {
                        width: 120px;
                        height: 120px;
                        border-radius: 50%;
                        border: none;
                        background: transparent;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        margin: 30px 0;
                        box-shadow: 0 4px 20px rgba(76, 175, 80, 0.3);
                        overflow: hidden;
                        position: relative;
                    }
                    
                    .video-icon {
                        width: 100%;
                        height: 100%;
                        object-fit: cover;
                        border-radius: 50%;
                        clip-path: circle(50%);
                    }
                    
                    .mic-button:hover {
                        transform: scale(1.05);
                        box-shadow: 0 6px 25px rgba(76, 175, 80, 0.4);
                    }
                    
                    .mic-button.listening {
                        animation: pulse 1.5s infinite;
                        /* Keep the same green glow, no red effect */
                    }
                    
                    @keyframes pulse {
                        0% { transform: scale(1); }
                        50% { transform: scale(1.1); }
                        100% { transform: scale(1); }
                    }
                    
                    .status {
                        font-size: 1.2rem;
                        margin: 20px 0;
                        min-height: 30px;
                    }
                    
                    .memory-count {
                        font-size: 1rem;
                        opacity: 0.8;
                        margin-top: 20px;
                    }
                    
                    .recent-memories {
                        margin-top: 30px;
                        text-align: left;
                        max-height: 200px;
                        overflow-y: auto;
                    }
                    
                    .memory-item {
                        background: rgba(255, 255, 255, 0.1);
                        padding: 10px;
                        margin: 5px 0;
                        border-radius: 8px;
                        font-size: 0.9rem;
                    }
                    
                    .memory-time {
                        font-size: 0.8rem;
                        opacity: 0.7;
                        margin-top: 5px;
                    }
                    
                    .ai-response {
                        background: rgba(76, 175, 80, 0.2);
                        border: 1px solid rgba(76, 175, 80, 0.3);
                        border-radius: 15px;
                        padding: 15px;
                        margin: 20px 0;
                        text-align: left;
                        backdrop-filter: blur(10px);
                        cursor: pointer;
                        transition: all 0.3s ease;
                    }
                    
                    .ai-response:hover {
                        background: rgba(76, 175, 80, 0.3);
                        transform: translateY(-2px);
                    }
                    
                    .ai-response h4 {
                        color: #4CAF50;
                        margin: 0 0 10px 0;
                        font-size: 1rem;
                    }
                    
                    .ai-response p {
                        color: white;
                        margin: 0;
                        line-height: 1.4;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <button id="micButton" class="mic-button" onclick="toggleRecording()">
                        <video id="smilerVideo" class="video-icon" autoplay muted loop>
                            <source src="smiler.mp4" type="video/mp4">
                            😊
                        </video>
                    </button>
                    <div id="status" class="status">Click to speak</div>
                    <div id="memoryCount" class="memory-count">0 memories stored</div>
                    
                    <div id="aiResponse" class="ai-response" style="display: none;">
                        <h4>🤖 MyAssistant says:</h4>
                        <p></p>
                        <small style="color: rgba(255, 255, 255, 0.7); font-size: 0.8rem;">Click to dismiss</small>
                    </div>
                    
                    <div id="recentMemories" class="recent-memories" style="display: none;">
                        <h3>Recent Memories:</h3>
                        <div id="memoriesList"></div>
                    </div>
                </div>

                <script>
                    let isRecording = false;
                    let mediaRecorder;
                    let audioChunks = [];
                    let ws;

                    // Connect to WebSocket
                    function connectWebSocket() {
                        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                        ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
                        
                        ws.onopen = function() {
                            console.log('Connected to MyAssistant');
                        };
                        
                        ws.onmessage = function(event) {
                            const data = JSON.parse(event.data);
                            handleMessage(data);
                        };
                        
                        ws.onclose = function() {
                            console.log('Disconnected from MyAssistant');
                            setTimeout(connectWebSocket, 3000);
                        };
                    }

                    function handleMessage(data) {
                        if (data.type === 'status') {
                            document.getElementById('status').textContent = data.message;
                        } else if (data.type === 'memory_stored') {
                            document.getElementById('status').textContent = 'Memory stored!';
                            document.getElementById('memoryCount').textContent = `${data.count} memories stored`;
                            
                            // Show AI response if available
                            if (data.ai_response) {
                                showAIResponse(data.ai_response);
                            }
                            
                            showRecentMemories(data.recent);
                        } else if (data.type === 'error') {
                            document.getElementById('status').textContent = data.message;
                        }
                    }

                    function showRecentMemories(memories) {
                        const container = document.getElementById('recentMemories');
                        const list = document.getElementById('memoriesList');
                        
                        if (memories && memories.length > 0) {
                            container.style.display = 'block';
                            list.innerHTML = memories.slice(0, 3).map(memory => `
                                <div class="memory-item">
                                    ${memory.text}
                                    <div class="memory-time">${new Date(memory.created_at).toLocaleString()}</div>
                                </div>
                            `).join('');
                        }
                    }
                    
                    function showAIResponse(response) {
                        const aiResponseDiv = document.getElementById('aiResponse');
                        const responseText = aiResponseDiv.querySelector('p');
                        responseText.textContent = response;
                        aiResponseDiv.style.display = 'block';
                        
                        // Add click to dismiss functionality
                        aiResponseDiv.onclick = function() {
                            aiResponseDiv.style.display = 'none';
                        };
                        
                        // Hide after 30 seconds (increased from 10)
                        setTimeout(() => {
                            aiResponseDiv.style.display = 'none';
                        }, 30000);
                    }

                    async function toggleRecording() {
                        if (!isRecording) {
                            await startRecording();
                        } else {
                            stopRecording();
                        }
                    }

                    async function startRecording() {
                        try {
                            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                            mediaRecorder = new MediaRecorder(stream);
                            audioChunks = [];

                            mediaRecorder.ondataavailable = function(event) {
                                audioChunks.push(event.data);
                            };

                            mediaRecorder.onstop = function() {
                                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                                sendAudio(audioBlob);
                                stream.getTracks().forEach(track => track.stop());
                            };

                            mediaRecorder.start();
                            isRecording = true;
                            
                            const button = document.getElementById('micButton');
                            button.classList.add('listening');
                            // Keep the video playing, just change the visual effect
                            
                            document.getElementById('status').textContent = 'Listening...';
                            
                        } catch (error) {
                            console.error('Error accessing microphone:', error);
                            document.getElementById('status').textContent = 'Microphone access denied';
                        }
                    }

                    function stopRecording() {
                        if (mediaRecorder && isRecording) {
                            mediaRecorder.stop();
                            isRecording = false;
                            
                            const button = document.getElementById('micButton');
                            button.classList.remove('listening');
                            // Keep the video playing, just remove the listening effect
                            
                            document.getElementById('status').textContent = 'Processing...';
                        }
                    }

                    function sendAudio(audioBlob) {
                        if (ws && ws.readyState === WebSocket.OPEN) {
                            const reader = new FileReader();
                            reader.onload = function() {
                                const base64Audio = reader.result.split(',')[1];
                                ws.send(JSON.stringify({
                                    type: 'audio',
                                    data: base64Audio
                                }));
                            };
                            reader.readAsDataURL(audioBlob);
                        }
                    }

                    // Initialize
                    connectWebSocket();
                    
                    // Load initial memory count
                    fetch('/memories/count')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('memoryCount').textContent = `${data.count} memories stored`;
                        });
                </script>
            </body>
            </html>
            """

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "audio":
                        # For now, we'll simulate speech recognition
                        # In a real implementation, you'd send this to a speech service
                        await self.handle_audio_message(websocket, message["data"])
                        
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)

        @self.app.get("/memories/count")
        async def get_memory_count():
            memories = self.store.list_recent(limit=1000)
            return {"count": len(memories)}

        @self.app.get("/memories/recent")
        async def get_recent_memories():
            memories = self.store.list_recent(limit=10)
            return [
                {
                    "id": m.id,
                    "text": m.text,
                    "language": m.language,
                    "created_at": m.created_at
                }
                for m in memories
            ]

        @self.app.get("/smiler.mp4")
        async def get_smiler_video():
            # Look for the video file in the current directory
            video_path = "smiler.mp4"
            if os.path.exists(video_path):
                return FileResponse(video_path, media_type="video/mp4")
            else:
                # Return a 404 if file doesn't exist
                return {"error": "smiler.mp4 not found"}

    async def handle_audio_message(self, websocket: WebSocket, audio_data: str):
        """Handle audio data from the client"""
        try:
            # For demo purposes, we'll simulate speech recognition
            # In a real implementation, you'd process the audio_data here
            await websocket.send_text(json.dumps({
                "type": "status",
                "message": "Processing speech..."
            }))
            
            # Simulate processing time
            await asyncio.sleep(1)
            
            # For demo, we'll create a sample memory
            # In reality, you'd use speech recognition on the audio_data
            sample_text = "Sample memory from voice input"
            memory_id = self.store.remember(sample_text)
            
            # Get AI response (with error handling)
            try:
                ai_response = self.ai_system.get_response(sample_text, "en")
            except Exception as e:
                print(f"AI response error: {e}")
                ai_response = "I've stored that information! Thanks for sharing with me."
            
            # Get updated count and recent memories
            memories = self.store.list_recent(limit=10)
            recent_memories = [
                {
                    "id": m.id,
                    "text": m.text,
                    "language": m.language,
                    "created_at": m.created_at
                }
                for m in memories[:3]
            ]
            
            await websocket.send_text(json.dumps({
                "type": "memory_stored",
                "message": "Memory stored successfully!",
                "count": len(memories),
                "recent": recent_memories,
                "ai_response": ai_response
            }))
            
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Error processing audio: {str(e)}"
            }))

    def run(self, host: str = "0.0.0.0", port: int = None):
        """Run the web application"""
        if port is None:
            port = int(os.environ.get("PORT", 8001))
        uvicorn.run(self.app, host=host, port=port)


def main():
    """Main entry point for web GUI application"""
    app = WebAssistant()
    app.run()


if __name__ == "__main__":
    main()
