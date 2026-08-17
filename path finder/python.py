import requests

# 🔑 Replace with your credentials
APP_ID = "98b115be"
APP_KEY = "1a6d62937008cdcf89ac9499e4ff37a9"

# API endpoint (India job search)
url = "https://api.adzuna.com/v1/api/jobs/in/search/1"

params = {
    "app_id": APP_ID,
    "app_key": APP_KEY,
    "what": "software developer",   # job search keyword
    "where": "India",
    "results_per_page": 5
}

print("Testing Adzuna API...")

response = requests.get(url, params=params)

# Check response
if response.status_code == 200:
    data = response.json()
    print("✅ API Working Successfully!\n")

    jobs = data.get("results", [])

    if not jobs:
        print("No jobs found.")
    else:
        for job in jobs:
            print("Job Title:", job["title"])
            print("Company:", job["company"]["display_name"])
            print("Location:", job["location"]["display_name"])
            print("Apply Link:", job["redirect_url"])
            print("-" * 40)

else:
    print("❌ API Error:", response.status_code)
    print(response.text)