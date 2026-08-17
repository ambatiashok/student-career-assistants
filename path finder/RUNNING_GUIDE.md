# Project Running Guide

This document explains how to set up, run, and test the project on Windows, including where the Gemini API key must be placed.

## What This Project Uses

- Flask for the web app
- SQLite for the local database
- Google Gemini API for AI features such as the assistant, roadmap generation, resume help, interview help, and job suggestions

## Prerequisites

- Python 3.10 or newer
- A Google Gemini API key from Google AI Studio
- PowerShell on Windows

## Project Folder

Open the folder that contains these files:

- `app.py`
- `config.py`
- `requirements.txt`
- `ai_service.py`
- `templates/`

## Install Dependencies

Open PowerShell in the project root and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks script activation, run this once and then activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Create the `.env` File

The app loads environment variables from a `.env` file in the project root.

Create a file named `.env` next to `app.py` and add:

```env
GOOGLE_API_KEY=your_real_gemini_api_key_here
SECRET_KEY=any_long_random_string_here
```

### Where the API key should be placed

- Put the key in the project root `.env` file
- Use the exact variable name `GOOGLE_API_KEY`
- Do not put the key inside `app.py` or `ai_service.py`
- Do not commit `.env` to Git

### Example

```env
GOOGLE_API_KEY=AIzaSyExampleYourActualKeyHere
SECRET_KEY=career-assistant-dev-secret
```

## How the API Key Is Used

- `config.py` loads `.env` automatically with `python-dotenv`
- `config.py` reads `GOOGLE_API_KEY`
- `ai_service.py` creates the Gemini client with that key
- If the key is missing, the app prints a warning and AI features may fail

## Run the Project

Start the Flask app with:

```powershell
python app.py
```

Then open the app in your browser:

```text
http://127.0.0.1:5000
```

The home route redirects to login, so you will usually start by creating an account and logging in.

## Main App Routes

- `/register` - create a new account
- `/login` - sign in
- `/dashboard` - main dashboard
- `/generate-roadmap` - create a roadmap
- `/assistant` - AI assistant page
- `/assistant/chat` - assistant chat API
- `/assistant/clear` - clear assistant chat history
- `/assistant/mode` - change assistant mode

## Useful Commands

Run these from the project root:

```powershell
# Start the app
python app.py

# Test the assistant behavior
python test_assistant.py

# Quickly check Gemini models
python quick_model_test.py

# Run the larger model comparison test
python test_ai_models.py

# Compare available Gemini models
python compare_models.py

# List models using the configured API key
python list_models.py
```

## What to Check If AI Features Do Not Work

1. Confirm the `.env` file exists in the project root.
2. Confirm `GOOGLE_API_KEY` is present and not empty.
3. Restart the Flask app after editing `.env`.
4. Make sure the API key was copied correctly from Google AI Studio.
5. Check that you are not using an expired or disabled key.
6. Run `python test_assistant.py` to confirm the assistant function works.

## How to Get a Gemini API Key

1. Open Google AI Studio: https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy the generated key
5. Paste it into the project `.env` file as `GOOGLE_API_KEY=...`
6. Restart the app

## Notes for Deployment

- On Vercel or other hosted environments, set `GOOGLE_API_KEY` and `SECRET_KEY` in the platform environment settings instead of using a local `.env` file.
- Local file uploads and the SQLite database are stored in the project folder during development.
- On Vercel, the app uses temporary paths under `/tmp` for the database and uploads.

## Quick Verification Checklist

- `pip install -r requirements.txt` completed successfully
- `.env` contains `GOOGLE_API_KEY`
- `python app.py` starts without errors
- `http://127.0.0.1:5000/login` opens in the browser
- `/assistant` loads after login
