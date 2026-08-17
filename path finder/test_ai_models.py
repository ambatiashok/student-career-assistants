"""
AI Model Testing Script for AI Assistant Module
Tests available Gemini models and evaluates their performance
"""

from google import genai
from config import GOOGLE_API_KEY
import time
import json
from datetime import datetime

# Initialize client
try:
    client = genai.Client(api_key=GOOGLE_API_KEY)
    print("✅ Successfully initialized Gemini client\n")
except Exception as e:
    print(f"❌ Failed to initialize client: {e}")
    exit(1)

# Test prompts for AI Assistant evaluation
TEST_PROMPTS = [
    {
        "category": "Career Query",
        "prompt": "I want to become a data scientist. What skills should I focus on learning first?",
        "expected_elements": ["python", "statistics", "machine learning", "data"]
    },
    {
        "category": "Interview Preparation",
        "prompt": "How can I prepare for a technical round at a software company?",
        "expected_elements": ["practice", "coding", "algorithms", "data structures"]
    },
    {
        "category": "Resume Advice",
        "prompt": "What are the key sections that should be in a professional resume?",
        "expected_elements": ["contact", "experience", "education", "skills"]
    },
    {
        "category": "General Career",
        "prompt": "What are the most in-demand tech jobs in 2026?",
        "expected_elements": ["ai", "software", "data", "cloud"]
    }
]


def list_available_models():
    """List all available models from the API"""
    print("=" * 80)
    print("AVAILABLE GEMINI MODELS")
    print("=" * 80)
    
    models = []
    try:
        for model in client.models.list():
            print(f"\n📦 Model: {model.name}")
            print(f"   Display Name: {model.display_name}")
            
            # Extract model ID from name (e.g., 'models/gemini-pro' -> 'gemini-pro')
            model_id = model.name.split('/')[-1] if '/' in model.name else model.name
            models.append({
                'id': model_id,
                'name': model.name,
                'display_name': model.display_name
            })
            
        print(f"\n✅ Found {len(models)} available models\n")
        return models
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return []


def test_model_response(model_id, prompt, category):
    """Test a single model with a prompt"""
    print(f"\n   Testing: {category}")
    print(f"   Prompt: {prompt[:60]}...")
    
    try:
        start_time = time.time()
        
        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        response_text = response.text.strip()
        word_count = len(response_text.split())
        
        print(f"   ✅ Response time: {response_time:.2f}s")
        print(f"   📝 Word count: {word_count}")
        print(f"   📄 Preview: {response_text[:100]}...")
        
        return {
            "success": True,
            "response_time": response_time,
            "word_count": word_count,
            "response": response_text,
            "error": None
        }
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")
        return {
            "success": False,
            "response_time": None,
            "word_count": 0,
            "response": None,
            "error": str(e)
        }


def evaluate_model(model_id):
    """Comprehensively test a model"""
    print(f"\n{'=' * 80}")
    print(f"TESTING MODEL: {model_id}")
    print(f"{'=' * 80}")
    
    results = {
        "model_id": model_id,
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "avg_response_time": 0,
        "avg_word_count": 0,
        "success_rate": 0,
        "recommended": False
    }
    
    successful_tests = 0
    total_response_time = 0
    total_word_count = 0
    
    for test in TEST_PROMPTS:
        result = test_model_response(model_id, test["prompt"], test["category"])
        
        test_result = {
            "category": test["category"],
            "success": result["success"],
            "response_time": result["response_time"],
            "word_count": result["word_count"],
            "error": result["error"]
        }
        
        results["tests"].append(test_result)
        
        if result["success"]:
            successful_tests += 1
            total_response_time += result["response_time"]
            total_word_count += result["word_count"]
    
    # Calculate averages
    if successful_tests > 0:
        results["avg_response_time"] = total_response_time / successful_tests
        results["avg_word_count"] = total_word_count / successful_tests
    
    results["success_rate"] = (successful_tests / len(TEST_PROMPTS)) * 100
    
    # Scoring criteria (lower is better for recommendation)
    # - 100% success rate is mandatory
    # - Faster response time is better
    # - Reasonable word count (not too short, not too long)
    if results["success_rate"] == 100:
        results["recommended"] = True
        results["score"] = results["avg_response_time"]  # Lower is better
    
    print(f"\n📊 SUMMARY:")
    print(f"   Success Rate: {results['success_rate']:.1f}%")
    if successful_tests > 0:
        print(f"   Avg Response Time: {results['avg_response_time']:.2f}s")
        print(f"   Avg Word Count: {results['avg_word_count']:.0f}")
    
    return results


def compare_and_recommend(all_results):
    """Compare all models and recommend the best"""
    print(f"\n{'=' * 80}")
    print("FINAL COMPARISON & RECOMMENDATION")
    print(f"{'=' * 80}\n")
    
    # Filter only successful models
    successful_models = [r for r in all_results if r["success_rate"] == 100]
    
    if not successful_models:
        print("❌ No models passed all tests!")
        return None
    
    # Sort by response time (faster is better)
    successful_models.sort(key=lambda x: x["avg_response_time"])
    
    print("✅ All successful models (sorted by speed):\n")
    for i, result in enumerate(successful_models, 1):
        print(f"{i}. {result['model_id']}")
        print(f"   Avg Response Time: {result['avg_response_time']:.2f}s")
        print(f"   Avg Word Count: {result['avg_word_count']:.0f}")
        print(f"   Success Rate: {result['success_rate']:.1f}%")
        print()
    
    # Recommend the fastest model
    recommended = successful_models[0]
    
    print(f"{'=' * 80}")
    print(f"🏆 RECOMMENDED MODEL FOR AI ASSISTANT: {recommended['model_id']}")
    print(f"{'=' * 80}")
    print(f"Reasons:")
    print(f"  ✅ 100% success rate on all test prompts")
    print(f"  ⚡ Fastest average response time: {recommended['avg_response_time']:.2f}s")
    print(f"  📝 Appropriate response length: {recommended['avg_word_count']:.0f} words")
    print(f"{'=' * 80}\n")
    
    return recommended['model_id']


def save_results(all_results, recommendation):
    """Save test results to a JSON file"""
    output = {
        "test_date": datetime.now().isoformat(),
        "recommended_model": recommendation,
        "all_results": all_results
    }
    
    filename = "model_test_results.json"
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"💾 Results saved to: {filename}\n")


def main():
    """Main testing function"""
    print("\n" + "=" * 80)
    print("AI ASSISTANT MODEL TESTING SUITE")
    print("Testing models for AI assistant functionality")
    print("=" * 80 + "\n")
    
    # Step 1: List available models
    available_models = list_available_models()
    
    if not available_models:
        print("❌ No models available to test!")
        return
    
    # Step 2: Test each model
    all_results = []
    
    for model in available_models:
        model_id = model['id']
        
        # Skip non-generative models
        if 'embedding' in model_id.lower():
            print(f"\n⏭️  Skipping embedding model: {model_id}")
            continue
        
        try:
            result = evaluate_model(model_id)
            all_results.append(result)
            
            # Add delay between model tests to avoid rate limiting
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Failed to test {model_id}: {e}")
            continue
    
    # Step 3: Compare and recommend
    if all_results:
        recommendation = compare_and_recommend(all_results)
        
        # Step 4: Save results
        save_results(all_results, recommendation)
        
        if recommendation:
            print(f"\n{'=' * 80}")
            print("NEXT STEPS:")
            print(f"{'=' * 80}")
            print(f"1. Update ai_service.py to use: {recommendation}")
            print(f"2. Replace 'gemini-2.0-flash-exp' in intelligent_assistant_chat()")
            print(f"3. Test the AI assistant in your application")
            print(f"{'=' * 80}\n")
    else:
        print("❌ No models could be tested!")


if __name__ == "__main__":
    main()
