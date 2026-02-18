import os
import deepgram
from deepgram import DeepgramClient
from dotenv import load_dotenv

load_dotenv(override=True)

def inspect_deepgram():
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        print("Missing API Key")
        return

    print(f"Deepgram SDK Version: {deepgram.__version__}")
    
    try:
        client = DeepgramClient(api_key)
        print("\n--- Client Attributes ---")
        print(dir(client))
        
        print("\n--- client.speak Attributes ---")
        try:
            print(dir(client.speak))
            print(f"Type: {type(client.speak)}")
        except Exception as e:
            print(f"Error accessing client.speak: {e}")

        print("\n--- client.speak.v('1') Check ---")
        try:
            v1 = client.speak.v("1")
            print("Success! client.speak.v('1') exists.")
            print(dir(v1))
        except Exception as e:
            print(f"Failed to access .v('1'): {e}")
            
        print("\n--- client.speak.rest Check ---")
        try:
            rest = client.speak.rest
            print("Success! client.speak.rest exists.")
            print(dir(rest))
        except Exception as e:
            print(f"Failed to access .rest: {e}")

    except Exception as e:
        print(f"Client Init Error: {e}")

if __name__ == "__main__":
    inspect_deepgram()
