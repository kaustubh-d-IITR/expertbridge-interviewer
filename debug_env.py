import os
from dotenv import load_dotenv

# Try standard load
print("--- Loading .env ---")
load_dotenv(override=True)

print("\n--- Environment Variables Check ---")
azure_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
openai_key = os.getenv("OPENAI_API_KEY")

print(f"AZURE_OPENAI_API_KEY: {'[PRESENT]' if azure_key else '[MISSING]'}")
if azure_key:
    print(f"  Length: {len(azure_key)}")
    print(f"  Start: {azure_key[:5]}...")
    
print(f"AZURE_OPENAI_ENDPOINT: {'[PRESENT]' if azure_endpoint else '[MISSING]'}")
if azure_endpoint:
    print(f"  Value: {azure_endpoint}")

print(f"OPENAI_API_KEY: {'[PRESENT]' if openai_key else '[MISSING]'}")

print("\n--- File Check ---")
if os.path.exists(".env"):
    print(".env file FOUND on disk.")
    with open(".env", "r") as f:
        content = f.read()
        print(f"File size: {len(content)} bytes")
        if "AZURE_OPENAI_API_KEY" in content:
            print("String 'AZURE_OPENAI_API_KEY' found in file.")
        else:
            print("String 'AZURE_OPENAI_API_KEY' NOT found in file.")
else:
    print(".env file NOT found on disk.")
