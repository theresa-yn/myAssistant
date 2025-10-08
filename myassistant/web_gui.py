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
from .chatgpt_ai import ChatGPTAssistant


class WebAssistant:
    def __init__(self):
        self.app = FastAPI(title="MyAssistant Web", version="0.1.0")
        self.store = MemoryStore()
        self.chatgpt = ChatGPTAssistant()
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
                        margin: 50px 0 150px 0; /* More space below smiler */
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
                    
                    .language-selector {
                        margin: 15px 0;
                        text-align: center;
                    }
                    
                    .language-selector label {
                        color: rgba(255, 255, 255, 0.8);
                        font-size: 0.9rem;
                        margin-right: 10px;
                    }
                    
                    .language-selector select {
                        background: rgba(255, 255, 255, 0.1);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        border-radius: 8px;
                        color: white;
                        padding: 6px 12px;
                        font-size: 0.9rem;
                        cursor: pointer;
                    }
                    
                    .language-selector select:focus {
                        outline: none;
                        border-color: #4CAF50;
                        box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
                    }
                    
                    .text-input-container {
                        position: fixed;
                        bottom: 50px; /* Move back down to bottom */
                        left: 50%;
                        transform: translateX(-50%);
                        width: 90%;
                        max-width: 500px;
                        z-index: 1000;
                    }
                    
                    .text-input {
                        width: 100%;
                        height: 80px;
                        background: rgba(255, 255, 255, 0.1);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        border-radius: 15px;
                        color: white;
                        padding: 15px;
                        font-size: 16px;
                        resize: vertical;
                        backdrop-filter: blur(10px);
                        box-sizing: border-box;
                    }
                    
                    .text-input::placeholder {
                        color: rgba(255, 255, 255, 0.6);
                    }
                    
                    .text-input:focus {
                        outline: none;
                        border-color: #4CAF50;
                        box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
                    }
                    
                    .submit-btn {
                        width: 100%;
                        margin-top: 10px;
                        background: rgba(76, 175, 80, 0.8);
                        border: 1px solid rgba(76, 175, 80, 0.3);
                        border-radius: 10px;
                        color: white;
                        padding: 12px 20px;
                        font-size: 16px;
                        cursor: pointer;
                        transition: all 0.3s ease;
                    }
                    
                    .submit-btn:hover {
                        background: rgba(76, 175, 80, 1);
                        transform: translateY(-2px);
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
                    
                    <!-- Text input box for adding information -->
                    <div class="text-input-container">
                        <textarea id="textInput" class="text-input" placeholder="Type your information here..."></textarea>
                        <button id="submitText" class="submit-btn" onclick="submitText()">Add Information</button>
                    </div>
                    
                    <!-- Hidden elements for functionality -->
                    <div id="status" class="status" style="display: none;">Click to speak</div>
                    <div id="memoryCount" class="memory-count" style="display: none;">0 memories stored</div>
                    
                    <div class="language-selector" style="display: none;">
                        <label for="languageSelect">🌐 Language:</label>
                        <select id="languageSelect" onchange="changeLanguage()">
                            <option value="en-US" selected>🇺🇸 English</option>
                        </select>
                    </div>
                    
                    <button id="testSpeech" class="test-speech-btn" onclick="testSpeech()" style="display: none;">🔊 Test Speech</button>
                    <button id="testAIResponse" class="test-speech-btn" onclick="testAIResponse()" style="display: none;">🤖 Test AI Response</button>
                    <button id="testMemory" class="test-speech-btn" onclick="testMemory()" style="display: none; position: fixed; top: 10px; right: 10px; z-index: 1000;">🧠 Test Memory</button>
                    <button id="testChatGPT" class="test-speech-btn" onclick="testChatGPT()" style="display: block; position: fixed; top: 10px; right: 10px; z-index: 1000;">🤖 Test ChatGPT</button>
                    
                    <!-- AI response will show temporarily when speaking -->
                    <div id="aiResponse" class="ai-response" style="display: none;">
                        <h4>🤖 MyAssistant says:</h4>
                        <p></p>
                        <small style="color: rgba(255, 255, 255, 0.7); font-size: 0.8rem;">Click to dismiss</small>
                    </div>
                    
                    <!-- Recent memories will show temporarily -->
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
                        console.log('Received message:', data);
                        if (data.type === 'status') {
                            document.getElementById('status').textContent = data.message;
                        } else if (data.type === 'memory_stored') {
                            document.getElementById('status').textContent = 'Memory stored!';
                            document.getElementById('memoryCount').textContent = `${data.count} memories stored`;
                            
                            // Show AI response if available
                            if (data.ai_response) {
                                console.log('AI response received:', data.ai_response);
                                showAIResponse(data.ai_response);
                            } else {
                                console.log('No AI response in message');
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
                        console.log('Showing AI response:', response);
                        const aiResponseDiv = document.getElementById('aiResponse');
                        const responseText = aiResponseDiv.querySelector('p');
                        responseText.textContent = response;
                        aiResponseDiv.style.display = 'block';
                        
                        // Speak the AI response with proper language
                        const currentLang = document.getElementById('languageSelect').value;
                        console.log('Speaking AI response with language:', currentLang);
                        speakWithLanguage(response, currentLang);
                        
                        // Add click to dismiss functionality
                        aiResponseDiv.onclick = function() {
                            aiResponseDiv.style.display = 'none';
                        };
                        
                        // Hide after 8 seconds (shorter since it's the only visible feedback)
                        setTimeout(() => {
                            aiResponseDiv.style.display = 'none';
                        }, 8000);
                    }

                    function speakText(text) {
                        if ('speechSynthesis' in window) {
                            console.log('Attempting to speak:', text);
                            
                            // Stop any current speech
                            speechSynthesis.cancel();
                            
                            const utterance = new SpeechSynthesisUtterance(text);
                            utterance.rate = 0.8;   // Siri's speaking rate
                            utterance.pitch = 1.0;  // Siri's natural pitch
                            utterance.volume = 1.0; // Maximum volume
                            
                            // Wait for voices to load if needed
                            const speakWithVoice = () => {
                                const voices = speechSynthesis.getVoices();
                                console.log('Available voices:', voices.length);
                                
                                // Try to use Siri's voice specifically
                                const preferredVoices = [
                                    'Samantha',           // macOS Siri voice
                                    'Siri',              // Direct Siri voice
                                    'Samantha Enhanced', // Enhanced Siri voice
                                    'Karen',             // macOS female voice (Siri-like)
                                    'Victoria',          // macOS female voice (Siri-like)
                                    'Alex',              // macOS male voice
                                    'Google UK English Female',  // Chrome Siri-like
                                    'Microsoft Zira Desktop',    // Edge Siri-like
                                    'Microsoft Hazel Desktop',   // Edge Siri-like
                                    'Google US English Female',  // Chrome Siri-like
                                    'Female'             // Generic female
                                ];
                                
                                let selectedVoice = null;
                                for (const voiceName of preferredVoices) {
                                    selectedVoice = voices.find(voice => 
                                        voice.name.includes(voiceName)
                                    );
                                    if (selectedVoice) break;
                                }
                                
                                if (selectedVoice) {
                                    utterance.voice = selectedVoice;
                                    console.log('Using voice:', selectedVoice.name);
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
                            recognition.lang = 'en-US'; // English (US)

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
                        console.log('Testing Siri voice...');
                        speakWithLanguage("Hello! This is a test of the Siri voice. Can you hear me speaking like Siri?", 'en-US');
                    }

                    function testAIResponse() {
                        console.log('Testing AI response speech...');
                        const testResponse = "Hello! I'm MyAssistant. I've stored your information and I'm ready to answer questions!";
                        showAIResponse(testResponse);
                    }

                    function testMemory() {
                        console.log('Testing memory system...');
                        fetch('/memories/test')
                            .then(response => response.json())
                            .then(data => {
                                console.log('Memory test result:', data);
                                let message = `Memory Test Results:\n`;
                                message += `Status: ${data.status}\n`;
                                message += `Total Memories: ${data.total_memories}\n`;
                                if (data.recent_memories && data.recent_memories.length > 0) {
                                    message += `Recent: ${data.recent_memories[0].text}\n`;
                                }
                                showAIResponse(message);
                            })
                            .catch(error => {
                                console.error('Memory test error:', error);
                                showAIResponse('Memory test failed: ' + error.message);
                            });
                    }

                    function testChatGPT() {
                        console.log('Testing ChatGPT integration...');
                        fetch('/chatgpt/test', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                message: 'Hello! Can you help me remember things?'
                            })
                        })
                        .then(response => response.json())
                        .then(data => {
                            console.log('ChatGPT test result:', data);
                            if (data.status === 'success') {
                                showAIResponse(data.response);
                            } else {
                                showAIResponse('ChatGPT test failed: ' + data.response);
                            }
                        })
                        .catch(error => {
                            console.error('ChatGPT test error:', error);
                            showAIResponse('ChatGPT test failed: ' + error.message);
                        });
                    }

                    function submitText() {
                        const textInput = document.getElementById('textInput');
                        const text = textInput.value.trim();
                        
                        if (!text) {
                            showAIResponse('Please enter some text first!');
                            return;
                        }
                        
                        console.log('Submitting text:', text);
                        
                        // Send text via WebSocket (same as voice input)
                        if (ws && ws.readyState === WebSocket.OPEN) {
                            ws.send(JSON.stringify({
                                type: 'audio',
                                data: text
                            }));
                            
                            // Clear the input
                            textInput.value = '';
                            
                            // Show feedback
                            showAIResponse('Processing your text...');
                        } else {
                            showAIResponse('Connection error. Please try again.');
                        }
                    }

                    function changeLanguage() {
                        const selectedLang = document.getElementById('languageSelect').value;
                        console.log('Language changed to:', selectedLang);
                        
                        // Update speech recognition language
                        if (recognition) {
                            recognition.lang = selectedLang;
                        }
                        
                        // Update status text based on language
                        document.getElementById('status').textContent = 'Click to speak';
                    }

                    function speakWithLanguage(text, language) {
                        if ('speechSynthesis' in window) {
                            console.log('Speaking with language:', language);
                            
                            // Stop any current speech
                            speechSynthesis.cancel();
                            
                            const utterance = new SpeechSynthesisUtterance(text);
                            utterance.rate = 0.8;   // Siri's speaking rate
                            utterance.pitch = 1.0;  // Siri's natural pitch
                            utterance.volume = 1.0; // Maximum volume
                            utterance.lang = language; // Set language
                            
                            // Wait for voices to load if needed
                            const speakWithVoice = () => {
                                const voices = speechSynthesis.getVoices();
                                console.log('Available voices for', language, ':', voices.length);
                                
                                // Find voice for the specific language
                                const languageVoices = voices.filter(voice => 
                                    voice.lang.startsWith(language.split('-')[0])
                                );
                                
                                if (languageVoices.length > 0) {
                                    // Use the first available voice for the language
                                    utterance.voice = languageVoices[0];
                                    console.log('Using language-specific voice:', languageVoices[0].name);
                                } else {
                                    console.log('No language-specific voice found, using default');
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

                    // Initialize
                    connectWebSocket();
                    
                    // Load initial memory count
                    
                    // Allow Enter key to submit text
                    document.addEventListener('DOMContentLoaded', function() {
                        const textInput = document.getElementById('textInput');
                        if (textInput) {
                            textInput.addEventListener('keydown', function(event) {
                                if (event.key === 'Enter' && !event.shiftKey) {
                                    event.preventDefault();
                                    submitText();
                                }
                            });
                        }
                    });
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
        
        @self.app.post("/chatgpt/test")
        async def test_chatgpt(message: dict):
            """Test ChatGPT integration"""
            try:
                user_message = message.get("message", "Hello")
                response = self.chatgpt.get_response(user_message)
                return {"response": response, "status": "success"}
            except Exception as e:
                return {"response": f"Error: {str(e)}", "status": "error"}
        
        @self.app.get("/memories/test")
        async def test_memories():
            """Test endpoint to check if memories are working"""
            try:
                # Test storing a memory
                test_id = self.store.remember("Test memory from API")
                
                # Test retrieving memories
                memories = self.store.list_recent(limit=5)
                
                # Test searching memories
                search_results = self.store.ask("test", limit=3)
                
                return {
                    "status": "success",
                    "test_memory_id": test_id,
                    "total_memories": len(memories),
                    "recent_memories": [{"id": m.id, "text": m.text, "created_at": m.created_at} for m in memories[:3]],
                    "search_results": [{"id": m.id, "text": m.text, "score": score} for m, score in search_results]
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}

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
            print(f"Stored memory with ID: {memory_id}, Text: {audio_data}")
            
            # Get ChatGPT response
            try:
                ai_response = self.chatgpt.get_response(audio_data)
                print(f"ChatGPT response: {ai_response}")
            except Exception as e:
                print(f"ChatGPT response error: {e}")
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
