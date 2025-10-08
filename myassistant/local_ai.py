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
        
        # Check if it's a question - PRIORITY: answer from memories
        if self._is_question(message_lower):
            answer = self._answer_question(user_message, memory_store)
            # If we got a proper answer from memories, return it
            if "Based on what you told me" in answer or "I found this related information" in answer:
                return answer
            # If no memory answer, don't repeat the question
        
        # Check if it's a statement (storing information)
        if self._is_statement(message_lower):
            return self._handle_statement(user_message)
        
        # For unclear messages, try to find relevant memories first
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
        # Clean the question for better matching
        question_clean = re.sub(r'[^\w\s]', ' ', question.lower())
        question_words = set(re.findall(r'\b\w+\b', question_clean))
        
        # Remove common question words to focus on content
        question_words.discard('what')
        question_words.discard('who')
        question_words.discard('when')
        question_words.discard('where')
        question_words.discard('why')
        question_words.discard('how')
        question_words.discard('which')
        question_words.discard('whose')
        question_words.discard('is')
        question_words.discard('are')
        question_words.discard('do')
        question_words.discard('does')
        question_words.discard('can')
        question_words.discard('could')
        question_words.discard('would')
        question_words.discard('will')
        
        # Search recent memories for word matches
        try:
            recent_memories = memory_store.list_recent(limit=10)
            if recent_memories:
                best_match = None
                best_score = 0
                
                for memory in recent_memories:
                    memory_clean = re.sub(r'[^\w\s]', ' ', memory.text.lower())
                    memory_words = set(re.findall(r'\b\w+\b', memory_clean))
                    
                    # Calculate match score
                    common_words = question_words.intersection(memory_words)
                    score = len(common_words)
                    
                    if score > best_score:
                        best_score = score
                        best_match = memory
                
                # If we found a good match, return it
                if best_match and best_score > 0:
                    return f"Based on what you told me: {best_match.text}"
                
                # If no good match, try FTS5 search as fallback
                try:
                    memory_results = memory_store.ask(question, limit=3)
                    if memory_results:
                        memory, score = memory_results[0]
                        return f"Based on what you told me: {memory.text}"
                except Exception as e:
                    print(f"FTS5 search error: {e}")
                
                # Last resort: return most recent memory if it seems relevant
                if recent_memories:
                    return f"Based on what you told me: {recent_memories[0].text}"
        except Exception as e:
            print(f"Memory search error: {e}")
        
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
        # Try to find any relevant memories using word matching
        try:
            recent_memories = memory_store.list_recent(limit=5)
            if recent_memories:
                # Clean the message for better matching
                message_clean = re.sub(r'[^\w\s]', ' ', message.lower())
                message_words = set(re.findall(r'\b\w+\b', message_clean))
                
                # Remove common words
                message_words.discard('the')
                message_words.discard('a')
                message_words.discard('an')
                message_words.discard('and')
                message_words.discard('or')
                message_words.discard('but')
                message_words.discard('in')
                message_words.discard('on')
                message_words.discard('at')
                message_words.discard('to')
                message_words.discard('for')
                message_words.discard('of')
                message_words.discard('with')
                message_words.discard('by')
                
                # Find best matching memory
                best_match = None
                best_score = 0
                
                for memory in recent_memories:
                    memory_clean = re.sub(r'[^\w\s]', ' ', memory.text.lower())
                    memory_words = set(re.findall(r'\b\w+\b', memory_clean))
                    
                    common_words = message_words.intersection(memory_words)
                    score = len(common_words)
                    
                    if score > best_score:
                        best_score = score
                        best_match = memory
                
                if best_match and best_score > 0:
                    return f"I found this related information: {best_match.text}. Is this what you're looking for?"
                
                # If no good match, just mention we have memories
                return f"I have {len(recent_memories)} memories stored. Could you be more specific about what you're looking for?"
        except Exception as e:
            print(f"Default response error: {e}")
        
        return "I'm here to help! You can tell me information to remember, or ask me questions about what you've shared."
    
    def is_available(self) -> bool:
        """Local AI is always available"""
        return True
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("Conversation history cleared")
