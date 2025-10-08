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
    
    def get_response(self, user_message: str, memory_store=None) -> str:
        """
        Get response from ChatGPT using stored memories
        """
        if not self.client:
            return "I'm sorry, but I need an OpenAI API key to work. Please set OPENAI_API_KEY in your .env file."
        
        try:
            # Get relevant memories for context
            memory_context = ""
            if memory_store:
                # Search for relevant memories based on the user's question
                memory_results = memory_store.ask(user_message, limit=5)
                if memory_results:
                    memory_context = "Here are relevant memories from the user:\n"
                    for memory, score in memory_results:
                        memory_context += f"- {memory.text}\n"
                else:
                    # If no specific matches, get recent memories
                    recent_memories = memory_store.list_recent(limit=3)
                    if recent_memories:
                        memory_context = "Here are recent memories from the user:\n"
                        for memory in recent_memories:
                            memory_context += f"- {memory.text}\n"
            
            # Create system message with memory context
            system_content = """You are MyAssistant, a helpful AI assistant with access to the user's personal memories.

CRITICAL INSTRUCTIONS:
1. ALWAYS answer questions based on the memories provided below
2. If the user asks a question, look through the memories to find the answer
3. If you find relevant information in the memories, respond with: "Based on what you told me: [exact information from memory]"
4. If you don't find relevant information in the memories, say: "I don't have that information in my memory"
5. Do NOT repeat the user's question back to them
6. Be helpful and conversational, but always base your answers on the stored memories
7. Keep responses concise and direct

""" + (memory_context if memory_context else "No memories available yet.")

            system_message = {
                "role": "system", 
                "content": system_content
            }
            
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Prepare messages for ChatGPT
            messages = [system_message] + self.conversation_history[-5:]  # Keep last 5 messages for context
            
            # Get response from ChatGPT
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Using GPT-3.5 for cost efficiency
                messages=messages,
                max_tokens=200,
                temperature=0.3  # Lower temperature for more consistent, memory-based responses
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
