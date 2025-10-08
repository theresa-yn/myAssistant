"""
AI Response System for MyAssistant
"""
import os
import json
from typing import Optional
from openai import OpenAI
from .memory_store import MemoryStore


class AIResponseSystem:
    def __init__(self, memory_store: MemoryStore):
        self.memory_store = memory_store
        self.client = None
        
        # Try to initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
    
    def get_response(self, user_message: str, language: str = "en") -> str:
        """
        Get AI response to user message
        """
        # Auto-detect language if not specified
        if language == "en":
            language = self._detect_language(user_message)
        
        if not self.client:
            return self._fallback_response(user_message, language)
        
        try:
            # Get recent memories for context
            recent_memories = self.memory_store.list_recent(limit=5)
            context = "\n".join([f"- {mem.text}" for mem in recent_memories])
            
            # Create system prompt
            system_prompt = f"""You are MyAssistant, a helpful AI assistant with access to the user's personal memories. 

Recent memories:
{context}

You should:
1. Be friendly and helpful
2. Reference relevant memories when appropriate
3. Answer questions based on stored information
4. Keep responses concise and conversational
5. Respond in {language} if possible

User message: {user_message}"""

            # Get AI response
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"AI response error: {e}")
            return self._fallback_response(user_message, language)
    
    def _detect_language(self, text: str) -> str:
        """
        Simple language detection based on common Vietnamese words
        """
        vietnamese_words = [
            "xin chào", "chào", "tôi", "bạn", "của", "và", "là", "có", "không", "được",
            "này", "đó", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín", "mười",
            "ngày", "tháng", "năm", "giờ", "phút", "giây", "hôm nay", "ngày mai", "hôm qua",
            "cảm ơn", "xin lỗi", "tạm biệt", "chúc mừng", "vui", "buồn", "yêu", "thích"
        ]
        
        text_lower = text.lower()
        vietnamese_count = sum(1 for word in vietnamese_words if word in text_lower)
        
        # If more than 1 Vietnamese word is found, consider it Vietnamese
        if vietnamese_count > 1:
            return "vi"
        else:
            return "en"
    
    def _fallback_response(self, user_message: str, language: str) -> str:
        """
        Fallback responses when AI is not available
        """
        message_lower = user_message.lower()
        
        if language == "vi":
            # Vietnamese responses
            if any(word in message_lower for word in ["xin chào", "chào", "hello", "hi"]):
                return "Xin chào! Tôi là MyAssistant. Tôi có thể giúp bạn ghi nhớ mọi thứ và trả lời câu hỏi!"
            elif any(word in message_lower for word in ["bạn khỏe không", "thế nào", "sao"]):
                return "Tôi đang rất tốt! Tôi ở đây để giúp bạn ghi nhớ và tổ chức suy nghĩ."
            elif any(word in message_lower for word in ["cảm ơn", "thanks"]):
                return "Không có gì! Tôi rất vui được giúp bạn ghi nhớ và tổ chức suy nghĩ."
            elif any(word in message_lower for word in ["tạm biệt", "bye", "goodbye"]):
                return "Tạm biệt! Tôi sẽ luôn ở đây khi bạn cần ghi nhớ điều gì hoặc hỏi câu hỏi."
            else:
                # Search through memories for relevant information
                memory_results = self.memory_store.ask(user_message, limit=3)
                if memory_results:
                    memory, score = memory_results[0]
                    return f"Tôi tìm thấy một số ký ức liên quan: {memory.text}. Bạn có muốn tôi tìm thêm thông tin không?"
                else:
                    return "Tôi đã lưu thông tin đó! Bạn có muốn biết điều gì cụ thể về ký ức của mình không?"
        else:
            # English responses
            if any(word in message_lower for word in ["hello", "hi", "hey"]):
                return "Hello! I'm MyAssistant. I can help you remember things and answer questions!"
            elif any(word in message_lower for word in ["how are you", "how are you doing"]):
                return "I'm doing great! I'm here to help you remember and organize your thoughts."
            elif any(word in message_lower for word in ["what", "who", "when", "where", "why", "how"]):
                return "That's a great question! I can help you find information from your memories. Try asking me about something you've told me before."
            elif any(word in message_lower for word in ["remember", "remind", "recall"]):
                return "I can help you remember things! I store everything you tell me, and you can search through your memories anytime."
            elif any(word in message_lower for word in ["thank", "thanks"]):
                return "You're welcome! I'm happy to help you remember and organize your thoughts."
            elif any(word in message_lower for word in ["goodbye", "bye", "see you"]):
                return "Goodbye! I'll be here whenever you need to remember something or ask a question."
            else:
                # Search through memories for relevant information
                memory_results = self.memory_store.ask(user_message, limit=3)
                if memory_results:
                    memory, score = memory_results[0]
                    return f"I found some related memories: {memory.text}. Would you like me to search for more information?"
                else:
                    return "I've stored that information! Is there anything specific you'd like to know about your memories?"
    
    def is_available(self) -> bool:
        """Check if AI is available"""
        return self.client is not None
