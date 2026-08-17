from google import genai

client = genai.Client(api_key="AIzaSyDKCPDvMsBrp8yg3ifzPP5VTn4ZIhWCVRQ")

print("Available models:")
print("-" * 80)

for model in client.models.list():
    print(f"Model: {model.name}")
    print(f"  Display Name: {model.display_name}")
    print("-" * 80)
