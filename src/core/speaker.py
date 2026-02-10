import os
from deepgram import DeepgramClient

class Speaker:
    def __init__(self):
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY not found in environment variables")
        self.deepgram = DeepgramClient(api_key=self.api_key)

    def text_to_speech(self, text, output_file="output_tts.mp3"):
        """
        Converts text to speech using Deepgram Aura.
        Returns the path to the audio file.
        """
        try:
            # Deepgram SDK v3+ usage for TTS
            # client.speak.v1.audio.generate(text=..., model=...) returns a stream of bytes
            
            filename = output_file
            response = self.deepgram.speak.v1.audio.generate(
                text=text, 
                model="aura-asteria-en"
            )
            
            # Write the streaming response to file
            with open(filename, "wb") as f:
                for chunk in response:
                    if chunk:
                        f.write(chunk)
            
            return filename

        except Exception as e:
            print(f"TTS Error: {e}")
            return None
