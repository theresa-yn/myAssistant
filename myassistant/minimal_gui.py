from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox
import speech_recognition as sr
import pyttsx3
from datetime import datetime

from .memory_store import MemoryStore


class MinimalAssistant:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MyAssistant")
        self.root.geometry("300x300")
        self.root.configure(bg='#2c3e50')
        self.root.resizable(False, False)
        
        # Center the window
        self.center_window()
        
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
        self.setup_ui()
        self.setup_microphone()
        
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="MyAssistant", 
            font=('Arial', 18, 'bold'),
            fg='#ecf0f1',
            bg='#2c3e50'
        )
        title_label.pack(pady=(0, 20))
        
        # Microphone button (main icon)
        self.mic_button = tk.Button(
            main_frame,
            text="🎤",
            font=('Arial', 48),
            bg='#3498db',
            fg='white',
            activebackground='#2980b9',
            activeforeground='white',
            relief='flat',
            border=0,
            width=4,
            height=2,
            command=self.toggle_voice_input
        )
        self.mic_button.pack(pady=20)
        
        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Click to speak",
            font=('Arial', 12),
            fg='#bdc3c7',
            bg='#2c3e50'
        )
        self.status_label.pack(pady=(10, 0))
        
        # Memory count label
        self.count_label = tk.Label(
            main_frame,
            text="",
            font=('Arial', 10),
            fg='#95a5a6',
            bg='#2c3e50'
        )
        self.count_label.pack(pady=(5, 0))
        
        # Update memory count
        self.update_memory_count()
        
    def setup_microphone(self):
        """Setup microphone and adjust for ambient noise"""
        def adjust_microphone():
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        
        # Run in background thread
        threading.Thread(target=adjust_microphone, daemon=True).start()
        
    def update_memory_count(self):
        """Update the memory count display"""
        try:
            recent_memories = self.store.list_recent(limit=1000)  # Get all
            count = len(recent_memories)
            self.count_label.config(text=f"{count} memories stored")
        except:
            self.count_label.config(text="0 memories stored")
            
    def toggle_voice_input(self):
        """Toggle voice input on/off"""
        if self.is_listening:
            self.stop_voice_input()
        else:
            self.start_voice_input()
            
    def start_voice_input(self):
        """Start voice input in background thread"""
        self.is_listening = True
        self.mic_button.config(
            text="🛑", 
            bg='#e74c3c',
            activebackground='#c0392b'
        )
        self.status_label.config(text="Listening...", fg='#e74c3c')
        
        def listen():
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                
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
        self.mic_button.config(
            text="🎤", 
            bg='#3498db',
            activebackground='#2980b9'
        )
        self.status_label.config(text="Click to speak", fg='#bdc3c7')
        
    def on_voice_result(self, text: str):
        """Handle successful voice recognition"""
        self.stop_voice_input()
        self.status_label.config(text="Storing memory...", fg='#f39c12')
        
        # Store the memory
        try:
            memory_id = self.store.remember(text)
            self.status_label.config(text="Memory stored!", fg='#27ae60')
            self.update_memory_count()
            
            # Speak confirmation
            self.speak(f"Remembered: {text[:30]}...")
            
            # Reset status after 2 seconds
            self.root.after(2000, lambda: self.status_label.config(text="Click to speak", fg='#bdc3c7'))
            
        except Exception as e:
            self.status_label.config(text="Error storing memory", fg='#e74c3c')
            messagebox.showerror("Error", f"Failed to store memory: {e}")
            self.root.after(2000, lambda: self.status_label.config(text="Click to speak", fg='#bdc3c7'))
        
    def on_voice_error(self, error_msg: str):
        """Handle voice recognition error"""
        self.stop_voice_input()
        self.status_label.config(text=error_msg, fg='#e74c3c')
        
        # Reset status after 3 seconds
        self.root.after(3000, lambda: self.status_label.config(text="Click to speak", fg='#bdc3c7'))
        
    def speak(self, text: str):
        """Convert text to speech"""
        def speak_thread():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"TTS Error: {e}")
                
        threading.Thread(target=speak_thread, daemon=True).start()
        
    def run(self):
        """Start the GUI application"""
        # Make window stay on top
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
        
        self.root.mainloop()


def main():
    """Main entry point for minimal GUI application"""
    app = MinimalAssistant()
    app.run()


if __name__ == "__main__":
    main()
