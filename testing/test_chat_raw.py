import os
import requests
import json
from dotenv import load_dotenv

load_dotenv(override=True)

def test_chat_raw():
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    # api_key = os.getenv("AZURE_OPENAI_API_KEY")
    # endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    # deployment_name = "gpt-audio" # User requested test
    
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    # We will test the new primary deployment and one fallback
    target_deployments = ["gpt4-extract-updated", "gpt4-extract-1"]
    
    print(f"--- AZURE CHAT TEST (RAW HTTP) ---")
    print(f"Endpoint: {endpoint}")
    
    if not api_key or not endpoint:
        print("Error: Missing .env variables.")
        return

    base_url = endpoint.rstrip("/")
    
    for deployment_name in target_deployments:
        print(f"\n------------------------------------------------")
        print(f"TESTING DEPLOYMENT: '{deployment_name}'")
        print(f"------------------------------------------------")
        
        url = f"{base_url}/openai/deployments/{deployment_name}/chat/completions?api-version=2024-02-15-preview"
    
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    
    # Payload 1: Standard GPT-4
    payload_standard = {
        "messages": [
            {"role": "user", "content": "Hello! Are you working?"}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    # Payload 2: O1-Preview / Reasoning Model (No max_tokens, no temp, no system)
    payload_reasoning = {
        "messages": [
            {"role": "user", "content": "Hello! Are you working?"}
        ],
        "max_completion_tokens": 50
    }
    
    print(f"\nSending Text Input to: {url}")
    
    try:
        # Try Standard First
        print("Attempting Standard Payload...")
        response = requests.post(url, headers=headers, json=payload_standard)
        
        if response.status_code != 200:
             print(f"Standard Failed: {response.text}")
             if "max_tokens" in response.text or "unsupported" in response.text:
                 print("\nRetrying with Reasoning Payload (o1-compatible)...")
                 response = requests.post(url, headers=headers, json=payload_reasoning)

        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            print(f"\nSUCCESS! AI Response:\n{content}")
            print("\nCONCLUSION: The Model ACCEPTS Text Input.")
            
        else:
            print(f"\nFAILURE. Full Response:\n{response.text}")
            # ... diagnostics ...
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_chat_raw()
