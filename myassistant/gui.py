from __future__ import annotations

import json
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Optional

import speech_recognition as sr
import pyttsx3
from pydantic import BaseModel

from .memory_store import MemoryStore


class MemoryDisplay(BaseModel):
    id: int
    text: str
    language: str
    tags: list[str]
    source: str
    created_at: str
    score: Optional[float] = None


class MyAssistantGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MyAssistant - Personal Memory Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize components
        self.store = MemoryStore()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        
        # Configure TTS
        self.tts_engine.setProperty('rate', 150)
        voices = self.tts_engine.getProperty('voices')
        if voices:
            self.tts_engine.setProperty('voice', voices[0].id)
        
        # GUI state
        self.is_listening = False
        self.current_mode = "remember"  # "remember" or "ask"
        
        self.setup_ui()
        self.setup_microphone()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Mode selection
        mode_frame = ttk.LabelFrame(main_frame, text="Mode", padding="5")
        mode_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.mode_var = tk.StringVar(value="remember")
        ttk.Radiobutton(mode_frame, text="Remember", variable=self.mode_var, 
                       value="remember", command=self.on_mode_change).grid(row=0, column=0, padx=5)
        ttk.Radiobutton(mode_frame, text="Ask", variable=self.mode_var, 
                       value="ask", command=self.on_mode_change).grid(row=0, column=1, padx=5)
        
        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Input", padding="5")
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)
        
        # Text input
        self.text_input = tk.Text(input_frame, height=3, wrap=tk.WORD, font=('Arial', 11))
        self.text_input.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Buttons frame
        buttons_frame = ttk.Frame(input_frame)
        buttons_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E))
        buttons_frame.columnconfigure(1, weight=1)
        
        # Voice input button
        self.voice_button = ttk.Button(buttons_frame, text="🎤 Start Voice Input", 
                                      command=self.toggle_voice_input)
        self.voice_button.grid(row=0, column=0, padx=(0, 5))
        
        # Send button
        self.send_button = ttk.Button(buttons_frame, text="Send", command=self.send_input)
        self.send_button.grid(row=0, column=2, padx=(5, 0))
        
        # Status label
        self.status_label = ttk.Label(buttons_frame, text="Ready", foreground="green")
        self.status_label.grid(row=0, column=1, padx=10)
        
        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="5")
        results_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Results text area
        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, 
                                                     font=('Arial', 10), state=tk.DISABLED)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure text tags for formatting
        self.results_text.tag_configure("header", font=('Arial', 12, 'bold'), foreground='#2c3e50')
        self.results_text.tag_configure("memory", font=('Arial', 10), foreground='#34495e')
        self.results_text.tag_configure("metadata", font=('Arial', 9), foreground='#7f8c8d')
        self.results_text.tag_configure("score", font=('Arial', 9, 'italic'), foreground='#e74c3c')
        
        # Bind Enter key to send
        self.text_input.bind('<Control-Return>', lambda e: self.send_input())
        
    def setup_microphone(self):
        """Setup microphone and adjust for ambient noise"""
        def adjust_microphone():
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        
        # Run in background thread
        threading.Thread(target=adjust_microphone, daemon=True).start()
        
    def on_mode_change(self):
        """Handle mode change"""
        self.current_mode = self.mode_var.get()
        if self.current_mode == "remember":
            self.send_button.config(text="Remember")
        else:
            self.send_button.config(text="Ask")
            
    def toggle_voice_input(self):
        """Toggle voice input on/off"""
        if self.is_listening:
            self.stop_voice_input()
        else:
            self.start_voice_input()
            
    def start_voice_input(self):
        """Start voice input in background thread"""
        self.is_listening = True
        self.voice_button.config(text="🛑 Stop Listening", state=tk.DISABLED)
        self.status_label.config(text="Listening...", foreground="orange")
        
        def listen():
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                # Recognize speech
                text = self.recognizer.recognize_google(audio)
                
                # Update UI in main thread
                self.root.after(0, lambda: self.on_voice_result(text))
                
            except sr.WaitTimeoutError:
                self.root.after(0, lambda: self.on_voice_error("No speech detected"))
            except sr.UnknownValueError:
                self.root.after(0, lambda: self.on_voice_error("Could not understand speech"))
            except sr.RequestError as e:
                self.root.after(0, lambda: self.on_voice_error(f"Speech service error: {e}"))
            except Exception as e:
                self.root.after(0, lambda: self.on_voice_error(f"Unexpected error: {e}"))
                
        threading.Thread(target=listen, daemon=True).start()
        
    def stop_voice_input(self):
        """Stop voice input"""
        self.is_listening = False
        self.voice_button.config(text="🎤 Start Voice Input", state=tk.NORMAL)
        self.status_label.config(text="Ready", foreground="green")
        
    def on_voice_result(self, text: str):
        """Handle successful voice recognition"""
        self.text_input.delete(1.0, tk.END)
        self.text_input.insert(1.0, text)
        self.stop_voice_input()
        self.status_label.config(text="Voice input received", foreground="green")
        
    def on_voice_error(self, error_msg: str):
        """Handle voice recognition error"""
        self.stop_voice_input()
        self.status_label.config(text=error_msg, foreground="red")
        messagebox.showerror("Voice Input Error", error_msg)
        
    def send_input(self):
        """Process the input based on current mode"""
        text = self.text_input.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("Empty Input", "Please enter some text or use voice input.")
            return
            
        if self.current_mode == "remember":
            self.remember_memory(text)
        else:
            self.ask_memory(text)
            
    def remember_memory(self, text: str):
        """Store a new memory"""
        try:
            self.status_label.config(text="Storing memory...", foreground="orange")
            memory_id = self.store.remember(text)
            
            # Clear input
            self.text_input.delete(1.0, tk.END)
            
            # Show success
            self.status_label.config(text="Memory stored successfully", foreground="green")
            self.display_remember_result(memory_id, text)
            
            # Speak confirmation
            self.speak(f"Memory stored: {text[:50]}...")
            
        except Exception as e:
            self.status_label.config(text="Error storing memory", foreground="red")
            messagebox.showerror("Error", f"Failed to store memory: {e}")
            
    def ask_memory(self, query: str):
        """Search memories"""
        try:
            self.status_label.config(text="Searching...", foreground="orange")
            results = self.store.ask(query, limit=10)
            
            self.status_label.config(text="Search completed", foreground="green")
            self.display_search_results(query, results)
            
            # Speak results
            if results:
                self.speak(f"Found {len(results)} memories")
            else:
                self.speak("No memories found")
                
        except Exception as e:
            self.status_label.config(text="Error searching", foreground="red")
            messagebox.showerror("Error", f"Failed to search memories: {e}")
            
    def display_remember_result(self, memory_id: int, text: str):
        """Display memory storage result"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        
        self.results_text.insert(tk.END, "Memory Stored Successfully\n", "header")
        self.results_text.insert(tk.END, f"ID: {memory_id}\n", "metadata")
        self.results_text.insert(tk.END, f"Text: {text}\n", "memory")
        self.results_text.insert(tk.END, f"Time: {self.get_current_time()}\n\n", "metadata")
        
        self.results_text.config(state=tk.DISABLED)
        
    def display_search_results(self, query: str, results: list):
        """Display search results"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        
        self.results_text.insert(tk.END, f"Search Results for: '{query}'\n", "header")
        self.results_text.insert(tk.END, f"Found {len(results)} memories\n\n", "metadata")
        
        if not results:
            self.results_text.insert(tk.END, "No memories found matching your query.\n", "memory")
        else:
            for i, (memory, score) in enumerate(results, 1):
                self.results_text.insert(tk.END, f"{i}. ", "header")
                self.results_text.insert(tk.END, f"Score: {score:.2f}\n", "score")
                self.results_text.insert(tk.END, f"Text: {memory.text}\n", "memory")
                self.results_text.insert(tk.END, f"Language: {memory.language}\n", "metadata")
                if memory.tags.strip():
                    self.results_text.insert(tk.END, f"Tags: {memory.tags}\n", "metadata")
                if memory.source.strip():
                    self.results_text.insert(tk.END, f"Source: {memory.source}\n", "metadata")
                self.results_text.insert(tk.END, f"Created: {memory.created_at}\n\n", "metadata")
        
        self.results_text.config(state=tk.DISABLED)
        
    def speak(self, text: str):
        """Convert text to speech"""
        def speak_thread():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"TTS Error: {e}")
                
        threading.Thread(target=speak_thread, daemon=True).start()
        
    def get_current_time(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


def main():
    """Main entry point for GUI application"""
    app = MyAssistantGUI()
    app.run()


if __name__ == "__main__":
    main()
