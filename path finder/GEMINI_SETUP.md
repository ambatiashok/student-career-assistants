# Google Gemini API Setup Guide

## Quick Setup Instructions

Your AI Career Assistant now uses **Google Gemini API** (free tier available!).

### Step 1: Get Your Free API Key

1. Visit **[Google AI Studio](https://aistudio.google.com/app/apikey)**
2. Sign in with your Google account
3. Click the **"Create API Key"** button
4. Copy the generated API key (it will look like: `AIzaSyABc...`)

### Step 2: Configure Your Application

1. Open the `.env` file in your project root folder
2. Find the line: `GOOGLE_API_KEY=your_gemini_api_key_here`
3. Replace `your_gemini_api_key_here` with your actual API key
4. Save the file

**Example:**
```
GOOGLE_API_KEY=AIzaSyABcDeFgHiJkLmNoPqRsTuVwXyZ1234567
```

### Step 3: Restart Your Application

1. Stop the Flask server (press `Ctrl+C` in terminal)
2. Run the application again:
   ```bash
   python app.py
   ```

### Verification

- The warning message about missing API key should disappear
- The AI Assistant should now respond to your messages
- If you still see errors, verify your API key is correct

## Troubleshooting

### "API Key not configured" warning
- Make sure you saved the `.env` file after adding your API key
- Check that there are no extra spaces before or after the API key
- Restart the Flask application

### "Failed to process message" error
- Verify your API key is valid at [Google AI Studio](https://aistudio.google.com/app/apikey)
- Check your internet connection
- Make sure you haven't exceeded the free tier limits

### API Key Limits (Free Tier)
- 15 requests per minute
- 1,500 requests per day
- 1 million tokens per day

For most development and testing purposes, the free tier is sufficient!

## Security Note

⚠️ **Never commit your `.env` file to version control (Git)**

The `.env` file contains sensitive information and should be kept private.

---

**Need help?** Check the [Gemini API documentation](https://ai.google.dev/docs)
