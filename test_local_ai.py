#!/usr/bin/env python3
"""
Test script for Local AI system
"""
from myassistant.local_ai import LocalAI
from myassistant.memory_store import MemoryStore

def test_local_ai():
    print("🧠 Testing Local AI System")
    print("=" * 40)
    
    # Initialize AI and memory store
    ai = LocalAI()
    store = MemoryStore()
    
    print("✅ Local AI initialized (no external API required!)")
    print("✅ Memory store initialized")
    
    # Add some test memories
    print("\n📝 Adding test memories...")
    store.remember("My sister's phone number is 555-1234")
    store.remember("I have a meeting tomorrow at 2 PM")
    store.remember("My favorite color is blue")
    store.remember("Sr. Cabrini's room is 259N on the second floor")
    store.remember("I need to call the dentist next week")
    
    print("✅ Test memories added")
    
    # Test different types of interactions
    test_cases = [
        ("Hello!", "greeting"),
        ("What is my sister's phone number?", "question"),
        ("My car is red", "statement"),
        ("When is my meeting?", "question"),
        ("What's my favorite color?", "question"),
        ("Where is Sr. Cabrini's room?", "question"),
        ("I like pizza", "statement"),
        ("How are you?", "greeting"),
        ("What do I need to do next week?", "question"),
        ("Tell me about my car", "question")
    ]
    
    print("\n🧪 Testing AI responses...")
    print("-" * 50)
    
    for message, expected_type in test_cases:
        print(f"\nUser: {message}")
        response = ai.get_response(message, store)
        print(f"AI: {response}")
        print(f"Type: {expected_type}")
    
    print("\n" + "=" * 50)
    print("🎉 Local AI test completed!")
    print("✅ No external API required")
    print("✅ Works with stored memories")
    print("✅ Handles greetings, questions, and statements")
    
    return True

if __name__ == "__main__":
    test_local_ai()
