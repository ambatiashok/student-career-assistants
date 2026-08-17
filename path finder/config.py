import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
# IMPORTANT: Set your Gemini API key in the .env file
# Get a free API key from: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if not GOOGLE_API_KEY or GOOGLE_API_KEY == 'your_gemini_api_key_here':
    print("\n" + "="*70)
    print("WARNING: Google Gemini API Key not configured!")
    print("="*70)
    print("Please follow these steps to fix:")
    print("1. Visit https://aistudio.google.com/app/apikey")
    print("2. Sign in with your Google account")
    print("3. Click 'Create API Key'")
    print("4. Copy the API key")
    print("5. Open the .env file in your project folder")
    print("6. Replace 'your_gemini_api_key_here' with your actual API key")
    print("7. Restart the Flask application")
    print("="*70 + "\n")
