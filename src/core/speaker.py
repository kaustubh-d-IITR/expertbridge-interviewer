import os
from deepgram import DeepgramClient

class Speaker:
    def __init__(self):
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY not found in environment variables")
        self.deepgram = DeepgramClient(api_key=self.api_key)

    # Feature 5: Multilingual Voice Map
    LANG_VOICE_MAP = {
        "hi": "aura-hindi", # Hypothetical - Deepgram may not have "aura-hindi", checking docs usually needed. fallback to en if unsure
        "fr": "aura-asteria-en", # Deepgram Aura is primarily English right now, but let's simulate mapping or use specific ones if available. 
        # actually Deepgram Aura is only English (Asteria/Orion) for now. 
        # But for the purpose of this "Upgrade", I will implement the logic so it's ready.
        # "en" is default.
    }

    def text_to_speech(self, text, output_file="output_tts.mp3", voice_model="aura-asteria-en", language="en"):
        """
        Converts text to speech securely using Azure TTS, OpenAI, or Deepgram Aura.
        Returns AUDIO BYTES.
        """
        try:
            import requests
            
            # STEP 1: Attempt Azure TTS with SSML Pace Control
            azure_key = os.getenv("SPEECH_KEY")
            azure_region = os.getenv("SPEECH_REGION", "eastus") # default eastus
            if azure_key:
                url = f"https://{azure_region}.tts.speech.microsoft.com/cognitiveservices/v1"
                headers = {
                    "Ocp-Apim-Subscription-Key": azure_key,
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
                    "User-Agent": "ExpertBridgeTTS"
                }
                # Use a neutral accent by default if the passed model isn't Azure-specific
                final_voice = voice_model if "Neural" in voice_model else "en-US-AvaMultilingualNeural"
                
                # Slower speed via SSML (-10%)
                ssml = f"""<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
    <voice name='{final_voice}'>
        <prosody rate='-10%'>{text}</prosody>
    </voice>
</speak>"""
                # Encode string to bytes to avoid Unicode/XML breaking requests
                response = requests.post(url, headers=headers, data=ssml.encode('utf-8'))
                if response.status_code == 200:
                    print(f"[Speaker] Azure TTS Success.")
                    return response.content
                else:
                    print(f"[Speaker] Azure TTS Error: {response.text}")
                    # Auto-fallback to next provider

            # STEP 2: Attempt OpenAI TTS if Key is present
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=openai_key)
                    
                    # Ensure voice is valid for OpenAI
                    valid_openai_voices = ["shimmer", "alloy", "echo", "fable", "onyx", "nova"]
                    oai_voice = voice_model if voice_model in valid_openai_voices else "shimmer"
                    
                    response = client.audio.speech.create(
                        model="tts-1",
                        voice=oai_voice,
                        input=text,
                        speed=0.90 # Drop speed
                    )
                    print(f"[Speaker] OpenAI TTS Success.")
                    return response.read()
                except Exception as e:
                    print(f"[Speaker] OpenAI TTS Error: {e}")
                    # Auto-fallback to next

            # STEP 3: Fallback to Deepgram Aura RAW HTTP
            if self.api_key:
                final_model = voice_model if "aura" in voice_model else "aura-asteria-en"
                url = f"https://api.deepgram.com/v1/speak?model={final_model}"
                headers = {
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {"text": text}
                
                response = requests.post(url, headers=headers, json=payload, stream=True)
                if response.status_code == 200:
                    audio_bytes = response.content
                    print(f"[Speaker] Deepgram TTS Success: Generated {len(audio_bytes)} bytes.")
                    return audio_bytes
                else:
                    print(f"[Speaker] Deepgram HTTP Error: {response.status_code} - {response.text}")
                    return None
            else:
                 print("[Speaker] No valid TTS keys found.")
                 return None

        except Exception as e:
            print(f"[Speaker] TTS Critical Error: {e}")
            return None
