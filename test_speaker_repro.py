import os
from dotenv import load_dotenv
from deepgram import DeepgramClient

load_dotenv(override=True)

def test_speak_raw():
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        print("Missing DEEPGRAM_API_KEY")
        # Try to load from AI_REBUILD .env if not found here (since user might not have .env in this repo)
        # But we rely on system env or local `.env`.
        return

    try:
        # Initialize Client
        # Note: EXPERTBRIDGE_INTERVIEWER speaker.py uses this init
        deepgram = DeepgramClient(api_key=api_key)
        
        text = "Hello, this is a test of the Deepgram Aura voice in EXPERTBRIDGE_INTERVIEWER."
        model = "aura-asteria-en"
        
        print(f"Generating audio for: '{text}' using '{model}'...")
        
        filename = "test_output_exp.mp3"
        
        # Mimic EXPERTBRIDGE_INTERVIEWER usage
        # response = self.deepgram.speak.v1.audio.generate(text=text, model=final_model)
        
        try:
             # This is what's in src/core/speaker.py
             response = deepgram.speak.rest.v("1").save(filename, {"text": text}, {"model": model})
             # Wait, the file has:
             # response = self.deepgram.speak.v1.audio.generate(...)
             # I should test WHAT IS IN THE FILE.
             
             print("Testing the code pattern found in src/core/speaker.py...")
             # Pattern in file: 
             # response = self.deepgram.speak.v1.audio.generate(text=text, model=final_model)
             # But `v1` property might not exist. 
             # Let's try to access it exactly as written?
             # But I can't call `self`.
             
             # Actually I will just import the class and use it.
             pass
        except Exception:
             pass

    except Exception as e:
        print(f"Setup Exception: {e}")

if __name__ == "__main__":
    try:
        from src.core.speaker import Speaker
        print("Imported Speaker class successfully.")
        speaker = Speaker()
        result = speaker.text_to_speech("Testing from script", "test_output_exp.mp3")
        if result and os.path.exists(result):
             print(f"SUCCESS: File created at {result}")
             print(f"Size: {os.path.getsize(result)} bytes")
        else:
             print("FAILURE: No file returned or created.")
    except Exception as e:
        print(f"Test Failed with error: {e}")
