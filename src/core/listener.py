import os
from deepgram import DeepgramClient

class Listener:
    def __init__(self):
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY not found in environment variables")
        self.deepgram = DeepgramClient(api_key=self.api_key)

    def get_transcription(self, audio_data, mime_type="audio/wav"):
        """
        Transcribes audio data using Deepgram's Prerecorded API.
        Args:
            audio_data: Bytes or file-like object containing audio.
            mime_type: The mimetype of the audio data.
        """
        try:
            # Check for empty audio
            if not audio_data:
                return ""

            # standard streamlit audio_input returns a BytesIO-like object
            if hasattr(audio_data, 'getvalue'):
                 buffer_data = audio_data.getvalue()
            elif hasattr(audio_data, 'read'):
                audio_data.seek(0)
                buffer_data = audio_data.read()
            else:
                buffer_data = audio_data

            print(f"[DEBUG] Audio data received. Size: {len(buffer_data)} bytes. Mime: {mime_type}")
            
            if len(buffer_data) < 100: 
                print("[DEBUG] Audio data too small, ignoring.")
                return ""

            # Deepgram "payload" for raw audio should be the bytes themselves 
            # passed as 'request' keyword argument.
            
            response = self.deepgram.listen.v1.media.transcribe_file(
                request=buffer_data,
                model="nova-2",
                smart_format=True,
                utterances=True,
                punctuate=True,
                detect_language=True, # Feature 1: Auto-Detect Language
                # language="en", # Removed hardcoded language
            )
            print(f"[DEBUG] Raw Deepgram Response: {response}")
            
            # Extract transcript and detected language
            transcript = ""
            detected_lang = "en"
            confidence = 0.0

            if hasattr(response, 'results'):
                 # Deepgram SDK v3 structure
                 result = response.results
                 if result and result.channels:
                     channel = result.channels[0]
                     if channel.alternatives:
                         alt = channel.alternatives[0]
                         transcript = alt.transcript
                         # Deepgram returns 'detected_language' in the alternative
                         if hasattr(alt, 'detected_language'):
                             detected_lang = alt.detected_language
                         elif hasattr(channel, 'detected_language'): # Fallback location
                             detected_lang = channel.detected_language
            else:
                # Dict fallback
                try:
                    alt = response["results"]["channels"][0]["alternatives"][0]
                    transcript = alt.get("transcript", "")
                    detected_lang = alt.get("detected_language", "en")
                except (KeyError, IndexError):
                    transcript = ""

            print(f"[DEBUG] Transcribed: '{transcript}' | Lang: {detected_lang}")
            
            # Return Dictionary as per Feature 1 Requirement
            return {
                "text": transcript,
                "lang": detected_lang,
                "confidence": 1.0 # Placeholder or extract if needed
            }
        
        except Exception as e:
            print(f"Transcription error: {e}")
            return {"text": "", "lang": "en"}
