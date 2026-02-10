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
                language="en",
            )
            print(f"[DEBUG] Raw Deepgram Response: {response}")
            
            print(f"[DEBUG] Transcription Response: {response}")
            
            # Response is likely an object, try dot notation
            if hasattr(response, 'results'):
                return response.results.channels[0].alternatives[0].transcript
            else:
                # Fallback to dict access if it's a dict
                return response["results"]["channels"][0]["alternatives"][0]["transcript"]
        
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""
