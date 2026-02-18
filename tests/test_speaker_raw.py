import os
from dotenv import load_dotenv
from deepgram import DeepgramClient, SpeakOptions

load_dotenv(override=True)

def test_speak_raw():
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        print("Missing DEEPGRAM_API_KEY")
        return

    try:
        # Initialize Client
        deepgram = DeepgramClient(api_key)
        
        text = "Hello, this is a test of the Deepgram Aura voice."
        model = "aura-asteria-en"
        
        print(f"Generating audio for: '{text}' using '{model}'...")
        
        url = f"https://api.deepgram.com/v1/speak?model={model}"
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json"
        }
        payload = {"text": text}
        
        import requests
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            filename = "test_output.mp3"
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"SUCCESS: File created at {filename}")
            print(f"Size: {len(response.content)} bytes")
        else:
            print(f"FAILURE: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_speak_raw()
