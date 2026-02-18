import os
from deepgram import DeepgramClient
from dotenv import load_dotenv

load_dotenv(override=True)

def inspect():
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        print("No API Key")
        return

    dg = DeepgramClient(api_key)
    print(f"DeepgramClient: {dg}")
    
    if hasattr(dg, 'speak'):
        print(f"dg.speak type: {type(dg.speak)}")
        print(f"dg.speak dir: {dir(dg.speak)}")
        
        if hasattr(dg.speak, 'rest'):
            print("dg.speak.rest exists!")
        else:
            print("dg.speak.rest DOES NOT exist.")
            
        if hasattr(dg.speak, 'v'):
            print("dg.speak.v exists!")
        else:
            print("dg.speak.v DOES NOT exist.")
    else:
        print("dg has no 'speak' attribute")

if __name__ == "__main__":
    inspect()
