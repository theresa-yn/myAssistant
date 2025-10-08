"""
Smart Local AI System - Advanced memory-based responses
No external APIs required - works completely offline
"""
import re
from typing import List, Tuple, Dict
from myassistant.memory_store import MemoryStore

class SmartAI:
    def __init__(self):
        self.conversation_history = []
        print("Smart AI system initialized - advanced memory matching!")
    
    def get_response(self, user_message: str, memory_store: MemoryStore = None) -> str:
        """
        Get intelligent response using advanced memory matching
        """
        if not memory_store:
            return "I'm ready to help! Please provide some information first."
        
        # Add to conversation history
        self.conversation_history.append({"user": user_message})
        
        # Clean and analyze the message
        message_lower = user_message.lower().strip()
        
        # Determine message type and get appropriate response
        message_type = self._analyze_message_type(message_lower)
        
        if message_type == "greeting":
            return self._handle_greeting()
        elif message_type == "question":
            return self._answer_question_intelligently(user_message, memory_store)
        elif message_type == "statement":
            return self._handle_statement(user_message)
        else:
            return self._handle_unclear_message(user_message, memory_store)
    
    def _analyze_message_type(self, message: str) -> str:
        """Analyze message to determine type"""
        # Greeting patterns
        greeting_patterns = [
            r'\b(hello|hi|hey|good morning|good afternoon|good evening)\b',
            r'\b(how are you|what\'s up|greetings)\b'
        ]
        
        for pattern in greeting_patterns:
            if re.search(pattern, message):
                return "greeting"
        
        # Question patterns
        question_words = ['what', 'who', 'when', 'where', 'why', 'how', 'which', 'whose']
        question_indicators = ['?', 'tell me', 'show me', 'give me', 'find', 'search']
        
        if any(word in message for word in question_words) or any(indicator in message for indicator in question_indicators):
            return "question"
        
        # Statement patterns
        statement_indicators = [
            'my', 'i have', 'i am', 'i like', 'i need', 'i want', 'i remember',
            'remember', 'note', 'save', 'store', 'write down'
        ]
        
        if any(indicator in message for indicator in statement_indicators):
            return "statement"
        
        return "unclear"
    
    def _handle_greeting(self) -> str:
        """Handle greeting messages"""
        greetings = [
            "Hello! I'm MyAssistant. I'm here to help you remember things and answer questions!",
            "Hi there! How can I help you today?",
            "Hello! I'm ready to assist you with your memories and questions.",
            "Hey! What would you like to remember or ask about today?",
            "Good to see you! I'm here to help with your information and questions."
        ]
        return greetings[len(self.conversation_history) % len(greetings)]
    
    def _answer_question_intelligently(self, question: str, memory_store: MemoryStore) -> str:
        """Intelligently answer questions using advanced memory matching"""
        # Extract key terms from the question
        key_terms = self._extract_key_terms(question)
        
        # Get all memories
        try:
            all_memories = memory_store.list_recent(limit=50)  # Get more memories for better matching
        except Exception as e:
            print(f"Error getting memories: {e}")
            return "I'm having trouble accessing my memories right now."
        
        if not all_memories:
            return "I don't have any information stored yet. Please tell me something to remember!"
        
        # Find the best matching memory
        best_match = self._find_best_memory_match(question, key_terms, all_memories)
        
        if best_match:
            return f"Based on what you told me: {best_match.text}"
        
        # If no good match, try to provide helpful context
        return self._provide_helpful_context(all_memories, question)
    
    def _extract_key_terms(self, question: str) -> List[str]:
        """Extract important terms from the question"""
        # Clean the question
        clean_question = re.sub(r'[^\w\s]', ' ', question.lower())
        words = re.findall(r'\b\w+\b', clean_question)
        
        # Remove common words that don't help with matching
        stop_words = {
            'what', 'who', 'when', 'where', 'why', 'how', 'which', 'whose',
            'is', 'are', 'was', 'were', 'do', 'does', 'did', 'can', 'could',
            'would', 'will', 'should', 'the', 'a', 'an', 'and', 'or', 'but',
            'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up',
            'down', 'out', 'off', 'over', 'under', 'again', 'further', 'then',
            'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
            'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some',
            'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
            'too', 'very', 'just', 'now'
        }
        
        # Keep only meaningful words
        key_terms = [word for word in words if word not in stop_words and len(word) > 2]
        return key_terms
    
    def _find_best_memory_match(self, question: str, key_terms: List[str], memories: List) -> object:
        """Find the best matching memory using advanced scoring"""
        best_match = None
        best_score = 0
        
        for memory in memories:
            score = self._calculate_match_score(question, key_terms, memory.text)
            if score > best_score:
                best_score = score
                best_match = memory
        
        # Only return a match if it has a reasonable score
        if best_score >= 1:  # At least one meaningful word match
            return best_match
        
        return None
    
    def _calculate_match_score(self, question: str, key_terms: List[str], memory_text: str) -> int:
        """Calculate how well a memory matches the question"""
        memory_lower = memory_text.lower()
        question_lower = question.lower()
        
        score = 0
        
        # Direct word matches (highest priority)
        for term in key_terms:
            if term in memory_lower:
                score += 3  # High score for direct matches
        
        # Partial word matches
        for term in key_terms:
            if len(term) > 3:  # Only for longer terms
                for word in memory_lower.split():
                    if term in word or word in term:
                        score += 1
        
        # Question-specific matching
        if 'phone' in question_lower and ('phone' in memory_lower or 'number' in memory_lower):
            score += 5
        if 'room' in question_lower and 'room' in memory_lower:
            score += 5
        if 'meeting' in question_lower and 'meeting' in memory_lower:
            score += 5
        if 'color' in question_lower and 'color' in memory_lower:
            score += 5
        if 'name' in question_lower and ('name' in memory_lower or 'called' in memory_lower):
            score += 5
        
        # Boost score for recent memories
        # (This is a simple approximation - in reality, we'd need to track timestamps)
        score += 1  # Small boost for all memories
        
        return score
    
    def _provide_helpful_context(self, memories: List, question: str) -> str:
        """Provide helpful context when no direct match is found"""
        if len(memories) == 1:
            return f"I have one memory stored: '{memories[0].text}'. Is this what you're looking for?"
        elif len(memories) <= 3:
            memory_list = [f"'{mem.text}'" for mem in memories[:3]]
            return f"I have {len(memories)} memories: {', '.join(memory_list)}. Which one are you asking about?"
        else:
            recent_memories = [f"'{mem.text}'" for mem in memories[:3]]
            return f"I have {len(memories)} memories stored. Here are the most recent ones: {', '.join(recent_memories)}. Could you be more specific about what you're looking for?"
    
    def _handle_statement(self, statement: str) -> str:
        """Handle statements (information being stored)"""
        responses = [
            "Got it! I've stored that information for you.",
            "Thanks! I'll remember that.",
            "Perfect! I've saved that information.",
            "I've noted that down for you.",
            "Great! I'll keep that in mind.",
            "Excellent! I've stored that in my memory.",
            "Understood! I'll remember that information."
        ]
        return responses[len(self.conversation_history) % len(responses)]
    
    def _handle_unclear_message(self, message: str, memory_store: MemoryStore) -> str:
        """Handle unclear messages by trying to find relevant information"""
        # Try to find any relevant memories
        key_terms = self._extract_key_terms(message)
        
        try:
            all_memories = memory_store.list_recent(limit=20)
            if all_memories:
                best_match = self._find_best_memory_match(message, key_terms, all_memories)
                if best_match:
                    return f"I found this related information: {best_match.text}. Is this what you're looking for?"
                
                # If no good match, provide general help
                return f"I have {len(all_memories)} memories stored. You can ask me questions about them or tell me new information to remember."
        except Exception as e:
            print(f"Error in unclear message handling: {e}")
        
        return "I'm here to help! You can tell me information to remember, or ask me questions about what you've shared."
    
    def is_available(self) -> bool:
        """Smart AI is always available"""
        return True
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("Conversation history cleared")
