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
            recent_memories = self.memory_store.list_recent(limit=10)
            context = "\n".join([f"- {mem.text}" for mem in recent_memories])
            print(f"AI Context - Recent memories: {len(recent_memories)}")
            print(f"AI Context - User message: {user_message}")
            
            # Also search for relevant memories based on the user's question
            search_results = self.memory_store.ask(user_message, limit=5)
            if search_results:
                relevant_memories = "\n".join([f"- {mem.text} (relevance: {score:.2f})" for mem, score in search_results])
                context += f"\n\nRelevant memories for your question:\n{relevant_memories}"
                print(f"AI Context - Found {len(search_results)} relevant memories")
            
            # Create system prompt with reminder capabilities
            system_prompt = f"""You are MyAssistant, a helpful AI assistant with access to the user's personal memories and tasks. 

Available memories:
{context}

CRITICAL INSTRUCTIONS:
1. **ALWAYS answer questions based on the memories provided above**
2. **If the user asks about something, search through the memories and provide specific information**
3. **Be specific and reference exact details from the memories**
4. **If you find relevant information, say "Based on what you told me..." or "I remember you said..."**
5. **If no relevant memories are found, say "I don't have any information about that in my memory"**
6. **Be friendly and conversational**
7. **Keep responses concise but informative**

Examples of good responses:
- User: "What meetings do I have?" → "Based on what you told me, you have a meeting tomorrow at 3 PM with the marketing team."
- User: "What did I say about my project?" → "I remember you said you need to finish the project by Friday and it's about the new website design."
- User: "Tell me about my appointments" → "I don't have any information about appointments in my memory. You can tell me about them and I'll remember!"

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
                # Check for reminders when greeting
                reminders = self._get_relevant_reminders(user_message)
                base_response = "Xin chào! Tôi là MyAssistant. Tôi có thể giúp bạn ghi nhớ mọi thứ và trả lời câu hỏi!"
                return base_response + (" " + reminders if reminders else "")
            elif any(word in message_lower for word in ["bạn khỏe không", "thế nào", "sao"]):
                return "Tôi đang rất tốt! Tôi ở đây để giúp bạn ghi nhớ và tổ chức suy nghĩ."
            elif any(word in message_lower for word in ["cảm ơn", "thanks"]):
                return "Không có gì! Tôi rất vui được giúp bạn ghi nhớ và tổ chức suy nghĩ."
            elif any(word in message_lower for word in ["tạm biệt", "bye", "goodbye"]):
                return "Tạm biệt! Tôi sẽ luôn ở đây khi bạn cần ghi nhớ điều gì hoặc hỏi câu hỏi."
            elif any(word in message_lower for word in ["nhắc nhở", "remind", "nhớ", "quên"]):
                # Look for reminder-related memories
                memory_results = self.memory_store.ask(user_message, limit=5)
                if memory_results:
                    reminders = []
                    for memory, score in memory_results[:3]:
                        if any(keyword in memory.text.lower() for keyword in ["họp", "meeting", "cuộc hẹn", "appointment", "deadline", "hạn chót", "cần làm", "phải làm"]):
                            reminders.append(f"- {memory.text}")
                    if reminders:
                        return f"Đây là những điều tôi nhắc nhở bạn:\n" + "\n".join(reminders)
                return "Tôi sẽ giúp bạn nhắc nhở! Hãy cho tôi biết bạn cần nhắc nhở về điều gì."
            else:
                # Search through memories for relevant information and reminders
                memory_results = self.memory_store.ask(user_message, limit=3)
                if memory_results:
                    memory, score = memory_results[0]
                    reminders = self._get_relevant_reminders(user_message)
                    base_response = f"Tôi tìm thấy một số ký ức liên quan: {memory.text}. Bạn có muốn tôi tìm thêm thông tin không?"
                    return base_response + (" " + reminders if reminders else "")
                else:
                    return "Tôi đã lưu thông tin đó! Bạn có muốn biết điều gì cụ thể về ký ức của mình không?"
        else:
            # English responses
            if any(word in message_lower for word in ["hello", "hi", "hey"]):
                # Check for reminders when greeting
                reminders = self._get_relevant_reminders(user_message)
                base_response = "Hello! I'm MyAssistant. I can help you remember things and answer questions!"
                return base_response + (" " + reminders if reminders else "")
            elif any(word in message_lower for word in ["how are you", "how are you doing"]):
                return "I'm doing great! I'm here to help you remember and organize your thoughts."
            elif any(word in message_lower for word in ["what", "who", "when", "where", "why", "how"]):
                # Search for relevant memories when user asks questions
                memory_results = self.memory_store.ask(user_message, limit=3)
                if memory_results:
                    memory, score = memory_results[0]
                    return f"Based on what you told me: {memory.text}"
                else:
                    return "I don't have any information about that in my memory. You can tell me about it and I'll remember!"
            elif any(word in message_lower for word in ["remember", "remind", "recall"]):
                # Look for reminder-related memories
                memory_results = self.memory_store.ask(user_message, limit=5)
                if memory_results:
                    reminders = []
                    for memory, score in memory_results[:3]:
                        if any(keyword in memory.text.lower() for keyword in ["meeting", "appointment", "deadline", "need to", "have to", "should", "must", "call", "email", "finish", "complete"]):
                            reminders.append(f"- {memory.text}")
                    if reminders:
                        return f"Here are some things I can remind you about:\n" + "\n".join(reminders)
                return "I can help you remember things! I store everything you tell me, and you can search through your memories anytime."
            elif any(word in message_lower for word in ["thank", "thanks"]):
                return "You're welcome! I'm happy to help you remember and organize your thoughts."
            elif any(word in message_lower for word in ["goodbye", "bye", "see you"]):
                return "Goodbye! I'll be here whenever you need to remember something or ask a question."
            else:
                # Search through memories for relevant information and reminders
                memory_results = self.memory_store.ask(user_message, limit=3)
                if memory_results:
                    memory, score = memory_results[0]
                    return f"Based on what you told me: {memory.text}"
                else:
                    return "I've stored that information! Is there anything specific you'd like to know about your memories?"
    
    def _get_relevant_reminders(self, user_message: str) -> str:
        """
        Get relevant reminders based on user's memories
        """
        try:
            # Search for task-related memories
            memory_results = self.memory_store.ask(user_message, limit=10)
            
            # Keywords that indicate tasks or reminders
            task_keywords = [
                "meeting", "appointment", "deadline", "need to", "have to", "should", "must",
                "call", "email", "finish", "complete", "submit", "due", "tomorrow", "next week",
                "họp", "cuộc hẹn", "hạn chót", "cần làm", "phải làm", "gọi", "gửi email",
                "hoàn thành", "nộp", "ngày mai", "tuần sau"
            ]
            
            reminders = []
            for memory, score in memory_results[:5]:  # Check top 5 most relevant
                memory_lower = memory.text.lower()
                if any(keyword in memory_lower for keyword in task_keywords):
                    reminders.append(f"By the way, you mentioned: {memory.text}")
            
            if reminders:
                return "\n".join(reminders[:3])  # Return top 3 reminders
            return ""
            
        except Exception as e:
            print(f"Error getting reminders: {e}")
            return ""

    def is_available(self) -> bool:
        """Check if AI is available"""
        return self.client is not None
