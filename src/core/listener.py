import os
from deepgram import DeepgramClient

class Listener:
    def __init__(self):
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        source = "os.environ"
        
        # Fallback to Streamlit secrets (for Cloud deployment)
        if not self.api_key:
            try:
                import streamlit as st
                self.api_key = st.secrets.get("DEEPGRAM_API_KEY")
                if self.api_key:
                    source = "st.secrets"
            except Exception:
                pass
                
        if not self.api_key:
            print("[Listener] ERROR: DEEPGRAM_API_KEY not found in environment variables or Streamlit secrets")
            raise ValueError("DEEPGRAM_API_KEY not found in any available source.")
            
        print(f"[Listener] Initialized (v3.1). API Key loaded from: {source}")
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
                return {"text": "", "lang": "en"}

            # Deepgram "payload" for raw audio
            payload = {
                "buffer": buffer_data,
                "mimetype": mime_type
            }
            
            options = {
                "model": "nova-2",
                "smart_format": True,
                "utterances": True,
                "punctuate": True,
                "detect_language": True, # Feature 1: Auto-Detect Language
            }
            
            # Try 'prerecorded' first, then 'rest' for compatibility
            if hasattr(self.deepgram.listen, "prerecorded"):
                response = self.deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
            elif hasattr(self.deepgram.listen, "rest"):
                response = self.deepgram.listen.rest.v("1").transcribe_file(payload, options)
            else:
                # Fallback for older v3 versions
                response = self.deepgram.listen.v("1").transcribe_file(payload, options)
            print(f"[DEBUG] Raw Deepgram Response: {response}")
            
            # Extract transcript and detected language
            transcript = ""
            detected_lang = "en"

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
            err_msg = f"Deepgram Transcription Error [v3.1]: {str(e)}"
            print(f"[Listener] {err_msg}")
            # Ensure we return a structured dictionary so Orchestrator can handle the message
            return {"text": "", "lang": "en", "error": err_msg}
