"""
Model Comparison for AI Assistant
Compares different models specifically for AI assistant use cases
"""

from google import genai
from config import GOOGLE_API_KEY
import time
import json

client = genai.Client(api_key=GOOGLE_API_KEY)

# Models to compare (based on availability)
MODELS_TO_COMPARE = [
    "gemini-flash-latest",       # Current recommended
    "gemini-2.5-flash",          # Stable alternative
    "gemini-flash-lite-latest",  # Faster but less capable
    "gemini-2.5-flash-lite",     # Lightweight version
]

# AI Assistant specific test prompts
TEST_PROMPTS = [
    {
        "type": "Short Query",
        "prompt": "What are the top 3 programming languages for beginners?",
        "expected_length": "short"
    },
    {
        "type": "Career Advice",
        "prompt": """I'm a computer science student in my 3rd year. My mock test average is 75%, 
        interview average is 68%, and resume score is 80%. What should I focus on to improve my 
        career readiness?""",
        "expected_length": "medium"
    },
    {
        "type": "Detailed Guidance",
        "prompt": """Create a detailed 6-month roadmap for me to become a full-stack developer. 
        I know Python and JavaScript basics. Include specific skills, resources, and timeline.""",
        "expected_length": "long"
    }
]

print("=" * 100)
print("AI ASSISTANT MODEL COMPARISON")
print("Comparing models for AI assistant performance")
print("=" * 100)
print()

comparison_results = {}

for model_id in MODELS_TO_COMPARE:
    print(f"\n{'=' * 100}")
    print(f"Testing: {model_id}")
    print(f"{'=' * 100}")
    
    model_results = {
        "model": model_id,
        "tests": [],
        "avg_time": 0,
        "avg_response_length": 0,
        "success_count": 0,
        "failed_count": 0
    }
    
    total_time = 0
    total_length = 0
    
    for test in TEST_PROMPTS:
        print(f"\n📝 Test: {test['type']}")
        print(f"   Prompt length: {len(test['prompt'])} chars")
        
        try:
            start = time.time()
            response = client.models.generate_content(
                model=model_id,
                contents=test['prompt']
            )
            elapsed = time.time() - start
            
            response_text = response.text.strip()
            word_count = len(response_text.split())
            char_count = len(response_text)
            
            print(f"   ✅ Success")
            print(f"   ⏱️  Time: {elapsed:.2f}s")
            print(f"   📊 Response: {word_count} words, {char_count} chars")
            print(f"   📄 Preview: {response_text[:100]}...")
            
            model_results["tests"].append({
                "type": test['type'],
                "success": True,
                "time": elapsed,
                "word_count": word_count,
                "char_count": char_count
            })
            
            model_results["success_count"] += 1
            total_time += elapsed
            total_length += char_count
            
            # Small delay to avoid rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Failed: {str(e)[:100]}")
            model_results["tests"].append({
                "type": test['type'],
                "success": False,
                "error": str(e)
            })
            model_results["failed_count"] += 1
    
    # Calculate averages
    if model_results["success_count"] > 0:
        model_results["avg_time"] = total_time / model_results["success_count"]
        model_results["avg_response_length"] = total_length / model_results["success_count"]
    
    comparison_results[model_id] = model_results
    
    print(f"\n📊 {model_id} Summary:")
    print(f"   Success: {model_results['success_count']}/{len(TEST_PROMPTS)}")
    if model_results["success_count"] > 0:
        print(f"   Avg Time: {model_results['avg_time']:.2f}s")
        print(f"   Avg Length: {model_results['avg_response_length']:.0f} chars")

# Final Comparison
print(f"\n{'=' * 100}")
print("FINAL COMPARISON")
print(f"{'=' * 100}\n")

# Create comparison table
print(f"{'Model':<35} {'Success Rate':<15} {'Avg Time':<15} {'Avg Length':<15}")
print("-" * 100)

successful_models = []

for model_id, results in comparison_results.items():
    success_rate = (results['success_count'] / len(TEST_PROMPTS)) * 100
    
    if results['success_count'] > 0:
        print(f"{model_id:<35} {success_rate:>5.1f}%        {results['avg_time']:>6.2f}s          {results['avg_response_length']:>8.0f} chars")
        
        if success_rate == 100:
            successful_models.append((model_id, results['avg_time']))
    else:
        print(f"{model_id:<35} {success_rate:>5.1f}%        N/A            N/A")

print()

# Recommendation
if successful_models:
    successful_models.sort(key=lambda x: x[1])  # Sort by speed
    winner = successful_models[0]
    
    print(f"{'=' * 100}")
    print("🏆 RECOMMENDATION FOR AI ASSISTANT")
    print(f"{'=' * 100}\n")
    print(f"Best Model: {winner[0]}")
    print(f"Average Response Time: {winner[1]:.2f}s")
    print(f"Success Rate: 100%")
    print()
    
    if len(successful_models) > 1:
        print("Alternative Options (in order of speed):")
        for i, (model, speed) in enumerate(successful_models[1:], 2):
            print(f"{i}. {model} ({speed:.2f}s)")
    
    print()
    print("✅ Your current configuration uses: gemini-flash-latest")
    if winner[0] == "gemini-flash-latest":
        print("   Perfect! This is the optimal choice.")
    else:
        print(f"   Consider switching to: {winner[0]} for better performance")
    
else:
    print("❌ No models completed all tests successfully")

print()
print(f"{'=' * 100}")

# Save results
output_file = "model_comparison_results.json"
with open(output_file, 'w') as f:
    json.dump(comparison_results, f, indent=2)

print(f"\n💾 Detailed results saved to: {output_file}")
print(f"{'=' * 100}\n")
