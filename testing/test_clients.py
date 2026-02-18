import os
print("--- Testing OpenAI Init ---")
try:
    from openai import OpenAI
    # Use dummy key to bypass validation and hit httpx init
    client = OpenAI(api_key="sk-dummy-key-for-testing-httpx-compat")
    print("OpenAI Init SUCCESS")
    
    # Also test AzureOpenAI just in case
    from openai import AzureOpenAI
    az = AzureOpenAI(
        api_key="dummy", 
        api_version="2023-05-15", 
        azure_endpoint="https://dummy.openai.azure.com"
    )
    print("AzureOpenAI Init SUCCESS")
    
except Exception as e:
    print(f"OpenAI Init FAILED: {e}")
    import traceback
    traceback.print_exc()

print("--- Testing Deepgram Init ---")
try:
    from deepgram import DeepgramClient
    dg = DeepgramClient(api_key="dummy")
    print("Deepgram Init SUCCESS")
except Exception as e:
    print(f"Deepgram Init FAILED: {e}")
