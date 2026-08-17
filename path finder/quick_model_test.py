"""
Quick AI Model Test - Testing best models for AI Assistant
"""

from google import genai
from config import GOOGLE_API_KEY
import time

client = genai.Client(api_key=GOOGLE_API_KEY)

# Test these specific models (fastest and most reliable)
MODELS_TO_TEST = [
    "gemini-2.5-flash",      # Currently used in most functions
    "gemini-2.0-flash",      # Alternative Gemini 2.0
    "gemini-flash-latest",   # Always points to latest flash
    "gemini-2.5-pro",        # More powerful but slower
]

TEST_PROMPT = "Explain in 2 sentences what a data scientist does."

print("=" * 80)
print("QUICK AI MODEL TEST FOR ASSISTANT")
print("=" * 80)
print()

results = []

for model_id in MODELS_TO_TEST:
    print(f"Testing: {model_id}")
    
    try:
        start = time.time()
        response = client.models.generate_content(
            model=model_id,
            contents=TEST_PROMPT
        )
        elapsed = time.time() - start
        
        print(f"  ✅ SUCCESS - Response time: {elapsed:.2f}s")
        print(f"  Response: {response.text[:100]}...")
        print()
        
        results.append({
            "model": model_id,
            "success": True,
            "time": elapsed,
            "response": response.text
        })
        
    except Exception as e:
        print(f"  ❌ FAILED - {str(e)[:80]}")
        print()
        results.append({
            "model": model_id,
            "success": False,
            "error": str(e)
        })

print("=" * 80)
print("RECOMMENDATION")
print("=" * 80)

# Find successful models sorted by speed
successful = [r for r in results if r["success"]]
if successful:
    successful.sort(key=lambda x: x["time"])
    recommended = successful[0]
    
    print(f"✅ RECOMMENDED MODEL: {recommended['model']}")
    print(f"   Speed: {recommended['time']:.2f}s")
    print()
    print("Action: Update ai_service.py intelligent_assistant_chat() function")
    print(f"   Change 'gemini-2.0-flash-exp' to '{recommended['model']}'")
    print()
else:
    print("❌ No models worked!")

print("=" * 80)
