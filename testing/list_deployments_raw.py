import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

def list_deployments():
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    print(f"Checking Endpoint: {endpoint}")
    
    if not api_key or not endpoint:
        print("Missing keys.")
        return

    # Strip trailing slash
    base_url = endpoint.rstrip("/")
    
    # Azure OpenAI Deployment List API
    # https://learn.microsoft.com/en-us/rest/api/azureopenai/deployments/list?view=rest-azureopenai-2023-05-15
    url = f"{base_url}/openai/deployments?api-version=2023-05-15"
    
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    
    print(f"Requesting: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nFOUND DEPLOYMENTS:")
            for item in data.get("data", []):
                print(f" - ID: {item['id']}")
                print(f"   Model: {item['model']}")
                print(f"   Status: {item['status']}")
                print("---")
            
            if not data.get("data"):
                print("No deployments found. You need to create one in Azure AI Foundry.")
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    list_deployments()
