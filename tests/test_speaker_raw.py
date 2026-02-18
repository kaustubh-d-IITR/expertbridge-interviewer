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
        
        filename = "test_output.mp3"
        
        # Proper SDK usage with Dict
        options = {"model": model}
        
        # Calling the API
        # Revert: .rest accessor is not available. Using .v("1") with dict options.
        response = deepgram.speak.v("1").save(filename, {"text": text}, options)
        
        print(f"Result: {response}")
        
        if os.path.exists(filename):
            print(f"SUCCESS: File created at {filename}")
            print(f"Size: {os.path.getsize(filename)} bytes")
        else:
            print("FAILURE: File not found.")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_speak_raw()
