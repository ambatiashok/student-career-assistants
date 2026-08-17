"""
AI Assistant Function Test
Tests the intelligent_assistant_chat function with various scenarios
"""

from ai_service import intelligent_assistant_chat, detect_intent_and_mode
import json

print("=" * 80)
print("AI ASSISTANT FUNCTIONALITY TEST")
print("=" * 80)
print()

# Mock user context (similar to what the app provides)
mock_user_context = {
    "name": "Test Student",
    "branch": "Computer Science",
    "year": "3rd Year",
    "career_goal": "Software Engineer",
    "skills": "Python, JavaScript, React",
    "performance": {
        "avg_test_score": 75.5,
        "total_tests": 8,
        "avg_interview_score": 68.0,
        "completed_interviews": 3,
        "avg_gd_score": 72.0,
        "total_gd_sessions": 5,
        "avg_resume_score": 80.0,
        "total_resumes": 2,
        "total_roadmaps": 1
    }
}

# Test scenarios
test_scenarios = [
    {
        "name": "Career Planning Query",
        "message": "What skills should I learn to become a software engineer?",
        "mode": "career"
    },
    {
        "name": "Interview Preparation",
        "message": "How can I improve my interview performance?",
        "mode": "interview"
    },
    {
        "name": "Resume Help",
        "message": "What should I add to my resume for a software engineer role?",
        "mode": "resume"
    },
    {
        "name": "General Question",
        "message": "How am I doing overall?",
        "mode": "general"
    },
    {
        "name": "Auto-detect Mode Test",
        "message": "I want to prepare for technical interviews",
        "mode": None  # Will auto-detect
    }
]

print("Testing AI Assistant with various queries...\n")
print("-" * 80)

results = []

for i, scenario in enumerate(test_scenarios, 1):
    print(f"\nTest {i}: {scenario['name']}")
    print(f"Message: {scenario['message']}")
    
    # Auto-detect mode if not specified
    if scenario['mode'] is None:
        detected_mode = detect_intent_and_mode(scenario['message'])
        print(f"Detected Mode: {detected_mode}")
        mode_to_use = detected_mode
    else:
        mode_to_use = scenario['mode']
        print(f"Mode: {mode_to_use}")
    
    try:
        # Call the assistant function
        response = intelligent_assistant_chat(
            user_message=scenario['message'],
            user_context=mock_user_context,
            mode=mode_to_use,
            chat_history=None
        )
        
        print(f"✅ SUCCESS")
        print(f"Response Preview: {response[:150]}...")
        print(f"Response Length: {len(response)} characters")
        
        results.append({
            "test": scenario['name'],
            "success": True,
            "response_length": len(response)
        })
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results.append({
            "test": scenario['name'],
            "success": False,
            "error": str(e)
        })
    
    print("-" * 80)

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

successful = sum(1 for r in results if r['success'])
total = len(results)

print(f"\nTests Passed: {successful}/{total}")
print(f"Success Rate: {(successful/total)*100:.1f}%\n")

if successful == total:
    print("✅ ALL TESTS PASSED!")
    print("The AI Assistant is working correctly with the new model.")
else:
    print("⚠️ Some tests failed. Check the errors above.")

print("\n" + "=" * 80)

# Test mode detection separately
print("\nTesting Mode Detection:")
print("-" * 80)

test_messages = [
    "How do I build a career roadmap?",
    "Tips for technical interview?",
    "Fix my resume please",
    "What skills should I learn?",
    "Show me job openings"
]

for msg in test_messages:
    detected = detect_intent_and_mode(msg)
    print(f"Message: {msg}")
    print(f"Mode: {detected}")
    print()

print("=" * 80)
print("Test completed!")
print("=" * 80)
