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
                    
                    .test-speech-btn {
                        background: rgba(255, 193, 7, 0.2);
                        border: 1px solid rgba(255, 193, 7, 0.3);
                        border-radius: 20px;
                        padding: 8px 16px;
                        color: #FFC107;
                        font-size: 0.9rem;
                        cursor: pointer;
                        margin: 10px 0;
                        transition: all 0.3s ease;
                    }
                    
                    .test-speech-btn:hover {
                        background: rgba(255, 193, 7, 0.3);
                        transform: translateY(-1px);
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
                    <button id="testSpeech" class="test-speech-btn" onclick="testSpeech()">🔊 Test Speech</button>
                    
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
                    let recognition;
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
                        
                        // Speak the AI response
                        speakText(response);
                        
                        // Add click to dismiss functionality
                        aiResponseDiv.onclick = function() {
                            aiResponseDiv.style.display = 'none';
                        };
                        
                        // Hide after 30 seconds (increased from 10)
                        setTimeout(() => {
                            aiResponseDiv.style.display = 'none';
                        }, 30000);
                    }

                    function speakText(text) {
                        if ('speechSynthesis' in window) {
                            console.log('Attempting to speak:', text);
                            
                            // Stop any current speech
                            speechSynthesis.cancel();
                            
                            const utterance = new SpeechSynthesisUtterance(text);
                            utterance.rate = 0.9;
                            utterance.pitch = 1;
                            utterance.volume = 0.8;
                            
                            // Wait for voices to load if needed
                            const speakWithVoice = () => {
                                const voices = speechSynthesis.getVoices();
                                console.log('Available voices:', voices.length);
                                
                                // Try to use a female voice if available
                                const femaleVoice = voices.find(voice => 
                                    voice.name.includes('Female') || 
                                    voice.name.includes('Samantha') || 
                                    voice.name.includes('Karen') ||
                                    voice.name.includes('Victoria') ||
                                    voice.name.includes('Google UK English Female') ||
                                    voice.name.includes('Microsoft Zira Desktop')
                                );
                                
                                if (femaleVoice) {
                                    utterance.voice = femaleVoice;
                                    console.log('Using voice:', femaleVoice.name);
                                } else {
                                    console.log('Using default voice');
                                }
                                
                                utterance.onstart = () => console.log('Speech started');
                                utterance.onend = () => console.log('Speech ended');
                                utterance.onerror = (event) => console.error('Speech error:', event.error);
                                
                                speechSynthesis.speak(utterance);
                            };
                            
                            // If voices are already loaded, speak immediately
                            if (speechSynthesis.getVoices().length > 0) {
                                speakWithVoice();
                            } else {
                                // Wait for voices to load
                                speechSynthesis.onvoiceschanged = speakWithVoice;
                            }
                        } else {
                            console.error('Speech synthesis not supported');
                        }
                    }

                    async function toggleRecording() {
                        if (!isRecording) {
                            await startRecording();
                        } else {
                            stopRecording();
                        }
                    }

                    function initSpeechRecognition() {
                        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                            recognition = new SpeechRecognition();
                            
                            recognition.continuous = false;
                            recognition.interimResults = false;
                            recognition.lang = 'en-US';

                            recognition.onstart = function() {
                                console.log('Speech recognition started');
                                isRecording = true;
                                const button = document.getElementById('micButton');
                                button.classList.add('listening');
                                document.getElementById('status').textContent = 'Listening...';
                            };

                            recognition.onresult = function(event) {
                                const transcript = event.results[0][0].transcript;
                                console.log('Speech recognized:', transcript);
                                sendTranscript(transcript);
                            };

                            recognition.onerror = function(event) {
                                console.error('Speech recognition error:', event.error);
                                document.getElementById('status').textContent = 'Error: ' + event.error;
                                stopRecording();
                            };

                            recognition.onend = function() {
                                console.log('Speech recognition ended');
                                stopRecording();
                            };
                        } else {
                            console.error('Speech recognition not supported');
                            document.getElementById('status').textContent = 'Speech recognition not supported in this browser';
                        }
                    }

                    function startRecording() {
                        if (!recognition) {
                            initSpeechRecognition();
                        }
                        
                        if (recognition && !isRecording) {
                            try {
                                recognition.start();
                            } catch (error) {
                                console.error('Error starting speech recognition:', error);
                                document.getElementById('status').textContent = 'Error starting speech recognition';
                            }
                        }
                    }

                    function stopRecording() {
                        if (recognition && isRecording) {
                            recognition.stop();
                            isRecording = false;
                            
                            const button = document.getElementById('micButton');
                            button.classList.remove('listening');
                            // Keep the video playing, just remove the listening effect
                            
                            document.getElementById('status').textContent = 'Processing...';
                        }
                    }

                    function sendTranscript(transcript) {
                        if (ws && ws.readyState === WebSocket.OPEN) {
                            ws.send(JSON.stringify({
                                type: 'audio',
                                data: transcript
                            }));
                        }
                    }

                    function testSpeech() {
                        console.log('Testing speech synthesis...');
                        speakText("Hello! This is a test of the speech synthesis. Can you hear me?");
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
            # Look for the video file in multiple possible locations
            possible_paths = [
                "smiler.mp4",
                "./smiler.mp4",
                "/app/smiler.mp4",
                os.path.join(os.getcwd(), "smiler.mp4")
            ]
            
            for video_path in possible_paths:
                if os.path.exists(video_path):
                    return FileResponse(video_path, media_type="video/mp4")
            
            # If not found, return a 404 with debug info
            from fastapi import HTTPException
            current_dir = os.getcwd()
            files_in_dir = os.listdir(current_dir) if os.path.exists(current_dir) else []
            raise HTTPException(
                status_code=404, 
                detail=f"smiler.mp4 not found. Current dir: {current_dir}, Files: {files_in_dir[:10]}"
            )

    async def handle_audio_message(self, websocket: WebSocket, audio_data: str):
        """Handle audio data from the client"""
        try:
            await websocket.send_text(json.dumps({
                "type": "status",
                "message": "Processing speech..."
            }))
            
            # The audio_data should now contain the actual transcribed text
            # from the Web Speech API on the client side
            if not audio_data or audio_data.strip() == "":
                audio_data = "I didn't catch that, could you try again?"
            
            # Store the actual transcribed text
            memory_id = self.store.remember(audio_data)
            
            # Get AI response (with error handling)
            try:
                ai_response = self.ai_system.get_response(audio_data, "en")
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
