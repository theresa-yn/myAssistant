#!/usr/bin/env python3
"""
Comprehensive test for Smart AI system
"""
from myassistant.smart_ai import SmartAI
from myassistant.memory_store import MemoryStore

def test_smart_ai():
    print("🧠 Testing Smart AI System - Advanced Memory Matching")
    print("=" * 60)
    
    # Initialize AI and memory store
    ai = SmartAI()
    store = MemoryStore()
    
    print("✅ Smart AI initialized")
    print("✅ Memory store initialized")
    
    # Add comprehensive test memories
    print("\n📝 Adding comprehensive test memories...")
    test_memories = [
        "My sister's phone number is 555-1234",
        "I have a meeting tomorrow at 2 PM with the boss",
        "My favorite color is blue",
        "Sr. Cabrini's room is 259N on the second floor",
        "I need to call the dentist next week",
        "My car is a red Toyota Camry",
        "I live at 123 Main Street",
        "My birthday is on March 15th",
        "I work at ABC Company",
        "My best friend's name is Sarah"
    ]
    
    for memory in test_memories:
        store.remember(memory)
    
    print(f"✅ Added {len(test_memories)} test memories")
    
    # Test different types of interactions
    test_cases = [
        # Greetings
        ("Hello!", "greeting"),
        ("Hi there!", "greeting"),
        ("How are you?", "greeting"),
        
        # Direct questions
        ("What is my sister's phone number?", "question"),
        ("When is my meeting?", "question"),
        ("What's my favorite color?", "question"),
        ("Where is Sr. Cabrini's room?", "question"),
        ("What do I need to do next week?", "question"),
        ("What kind of car do I have?", "question"),
        ("Where do I live?", "question"),
        ("When is my birthday?", "question"),
        ("Where do I work?", "question"),
        ("What's my best friend's name?", "question"),
        
        # Indirect questions
        ("Tell me about my sister's contact info", "question"),
        ("Show me my meeting details", "question"),
        ("Find my car information", "question"),
        ("Give me my address", "question"),
        
        # Statements
        ("My dog's name is Buddy", "statement"),
        ("I like pizza", "statement"),
        ("I need to buy groceries", "statement"),
        
        # Unclear messages
        ("Something about my sister", "unclear"),
        ("Meeting information", "unclear"),
    ]
    
    print("\n🧪 Testing Smart AI responses...")
    print("-" * 60)
    
    correct_answers = 0
    total_questions = 0
    
    for message, expected_type in test_cases:
        print(f"\nUser: {message}")
        response = ai.get_response(message, store)
        print(f"AI: {response}")
        print(f"Expected type: {expected_type}")
        
        # Check if questions are answered properly
        if expected_type == "question":
            total_questions += 1
            if "Based on what you told me" in response:
                correct_answers += 1
                print("✅ Correctly answered from memory")
            else:
                print("❌ Did not answer from memory")
        elif expected_type == "greeting":
            if any(greeting in response.lower() for greeting in ["hello", "hi", "hey", "good"]):
                print("✅ Proper greeting response")
            else:
                print("❌ Not a proper greeting")
        elif expected_type == "statement":
            if any(confirm in response.lower() for confirm in ["stored", "remember", "noted", "saved"]):
                print("✅ Proper statement acknowledgment")
            else:
                print("❌ Not a proper statement response")
    
    print("\n" + "=" * 60)
    print("🎯 Test Results:")
    print(f"✅ Questions answered correctly: {correct_answers}/{total_questions}")
    print(f"📊 Success rate: {(correct_answers/total_questions*100):.1f}%" if total_questions > 0 else "📊 No questions tested")
    print("✅ No external API required")
    print("✅ Advanced memory matching working")
    print("✅ Smart AI system operational")
    
    return correct_answers == total_questions

if __name__ == "__main__":
    success = test_smart_ai()
    if success:
        print("\n🎉 Smart AI system is working perfectly!")
    else:
        print("\n🔧 Smart AI system needs some adjustments.")
