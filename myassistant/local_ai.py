"""
Local AI System - No external API required
Uses simple pattern matching and memory search to answer questions
"""
import re
from typing import List, Tuple
from myassistant.memory_store import MemoryStore

class LocalAI:
    def __init__(self):
        self.conversation_history = []
        print("Local AI system initialized - no external API required!")
    
    def get_response(self, user_message: str, memory_store: MemoryStore = None) -> str:
        """
        Get response using local pattern matching and memory search
        """
        if not memory_store:
            return "I'm ready to help! Please provide some information first."
        
        # Add to conversation history
        self.conversation_history.append({"user": user_message})
        
        # Clean the message
        message_lower = user_message.lower().strip()
        
        # Check if it's a greeting
        if self._is_greeting(message_lower):
            return self._handle_greeting()
        
        # Check if it's a question
        if self._is_question(message_lower):
            return self._answer_question(user_message, memory_store)
        
        # Check if it's a statement (storing information)
        if self._is_statement(message_lower):
            return self._handle_statement(user_message)
        
        # Default response
        return self._default_response(user_message, memory_store)
    
    def _is_greeting(self, message: str) -> bool:
        """Check if message is a greeting"""
        greetings = [
            "hello", "hi", "hey", "good morning", "good afternoon", 
            "good evening", "how are you", "what's up", "greetings"
        ]
        return any(greeting in message for greeting in greetings)
    
    def _is_question(self, message: str) -> bool:
        """Check if message is a question"""
        question_words = ["what", "who", "when", "where", "why", "how", "which", "whose"]
        return message.endswith("?") or any(word in message for word in question_words)
    
    def _is_statement(self, message: str) -> bool:
        """Check if message is a statement (information to store)"""
        statement_indicators = [
            "my", "i have", "i am", "i like", "i need", "i want", 
            "remember", "note", "save", "store"
        ]
        return any(indicator in message for indicator in statement_indicators)
    
    def _handle_greeting(self) -> str:
        """Handle greeting messages"""
        responses = [
            "Hello! I'm MyAssistant. I'm here to help you remember things and answer questions!",
            "Hi there! How can I help you today?",
            "Hello! I'm ready to assist you with your memories and questions.",
            "Hey! What would you like to remember or ask about today?"
        ]
        return responses[len(self.conversation_history) % len(responses)]
    
    def _answer_question(self, question: str, memory_store: MemoryStore) -> str:
        """Answer questions using stored memories"""
        try:
            # Search for relevant memories
            memory_results = memory_store.ask(question, limit=5)
            
            if memory_results:
                # Found relevant memories
                memory, score = memory_results[0]
                return f"Based on what you told me: {memory.text}"
        except Exception as e:
            print(f"Memory search error: {e}")
        
        # Search recent memories if no specific matches or if search failed
        try:
            recent_memories = memory_store.list_recent(limit=5)
            if recent_memories:
                # Try to find partial matches
                question_words = set(re.findall(r'\b\w+\b', question.lower()))
                
                for memory in recent_memories:
                    memory_words = set(re.findall(r'\b\w+\b', memory.text.lower()))
                    if question_words.intersection(memory_words):
                        return f"Based on what you told me: {memory.text}"
                
                # If no word matches, return the most recent memory
                return f"Based on what you told me: {recent_memories[0].text}"
        except Exception as e:
            print(f"Recent memory search error: {e}")
        
        # No relevant information found
        return "I don't have that information in my memory. Could you tell me about it?"
    
    def _handle_statement(self, statement: str) -> str:
        """Handle statements (information being stored)"""
        responses = [
            "Got it! I've stored that information for you.",
            "Thanks! I'll remember that.",
            "Perfect! I've saved that information.",
            "I've noted that down for you.",
            "Great! I'll keep that in mind."
        ]
        return responses[len(self.conversation_history) % len(responses)]
    
    def _default_response(self, message: str, memory_store: MemoryStore) -> str:
        """Default response for unclear messages"""
        try:
            # Try to find any relevant memories
            memory_results = memory_store.ask(message, limit=1)
            
            if memory_results:
                memory, score = memory_results[0]
                return f"I found this related information: {memory.text}. Is this what you're looking for?"
        except Exception as e:
            print(f"Default response memory search error: {e}")
        
        # Get recent memories for context
        try:
            recent_memories = memory_store.list_recent(limit=2)
            if recent_memories:
                return f"I'm not sure what you mean. I have {len(recent_memories)} recent memories. Could you be more specific?"
        except Exception as e:
            print(f"Default response recent memory error: {e}")
        
        return "I'm here to help! You can tell me information to remember, or ask me questions about what you've shared."
    
    def is_available(self) -> bool:
        """Local AI is always available"""
        return True
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("Conversation history cleared")
