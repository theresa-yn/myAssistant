"""
Simple ChatGPT Integration for MyAssistant
"""
import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class ChatGPTAssistant:
    def __init__(self):
        self.client: Optional[OpenAI] = None
        self.conversation_history = []
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
            print("ChatGPT client initialized successfully")
        else:
            print("OPENAI_API_KEY not found. Please set your API key in .env file")
    
    def get_response(self, user_message: str) -> str:
        """
        Get response from ChatGPT
        """
        if not self.client:
            return "I'm sorry, but I need an OpenAI API key to work. Please set OPENAI_API_KEY in your .env file."
        
        try:
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Create system message for context
            system_message = {
                "role": "system", 
                "content": """You are MyAssistant, a helpful AI assistant. You can help users remember things, answer questions, and assist with various tasks. Be friendly, helpful, and conversational like ChatGPT. Keep responses concise but informative."""
            }
            
            # Prepare messages for ChatGPT
            messages = [system_message] + self.conversation_history[-10:]  # Keep last 10 messages for context
            
            # Get response from ChatGPT
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Using GPT-3.5 for cost efficiency
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            
            # Extract response
            ai_response = response.choices[0].message.content.strip()
            
            # Add AI response to conversation history
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            # Keep conversation history manageable (last 20 messages)
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return ai_response
            
        except Exception as e:
            print(f"ChatGPT API error: {e}")
            return "I'm sorry, I'm having trouble connecting right now. Please try again in a moment."
    
    def add_memory(self, memory_text: str):
        """
        Add a memory to the conversation context
        """
        memory_message = f"Please remember this information: {memory_text}"
        self.conversation_history.append({"role": "user", "content": memory_message})
        
        # Get acknowledgment from ChatGPT
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are MyAssistant. Acknowledge that you've received and will remember the information."},
                    {"role": "user", "content": memory_message}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            acknowledgment = response.choices[0].message.content.strip()
            self.conversation_history.append({"role": "assistant", "content": acknowledgment})
            return acknowledgment
            
        except Exception as e:
            print(f"Error adding memory: {e}")
            return "I've noted that information for you."
    
    def is_available(self) -> bool:
        """Check if ChatGPT is available"""
        return self.client is not None
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("Conversation history cleared")
