import os
import json
import requests

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
            
        print(f"[Listener] Initialized (v4.3 - REST Mode). API Key from: {source}")

    def get_transcription(self, audio_data, mime_type="audio/wav"):
        """
        Transcribes audio data using Deepgram's direct REST API for maximum stability.
        Bypasses the SDK to avoid version-drift issues.
        """
        try:
            # 1. Extract raw bytes if it's a Streamlit UploadedFile or file-like object
            if hasattr(audio_data, 'read'):
                audio_bytes = audio_data.read()
            else:
                audio_bytes = audio_data

            if not audio_bytes:
                return {"text": "", "lang": "en", "error": "Empty audio data received"}

            # 2. Configure REST API Call
            url = "https://api.deepgram.com/v1/listen"
            params = {
                "model": "nova-2",
                "smart_format": "true",
                "language": "en"
            }
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": mime_type
            }

            print(f"[DEBUG] Making direct REST call to Deepgram v4.3 (Size: {len(audio_bytes)} bytes)")
            
            # 3. Execute Request
            response = requests.post(url, params=params, headers=headers, data=audio_bytes, timeout=30)
            response.raise_for_status()
            response_data = response.json()

            # 4. Extract transcript safely from REST response structure
            # Structure: results -> channels[0] -> alternatives[0] -> transcript
            channels = response_data.get("results", {}).get("channels", [])
            if not channels:
                raise ValueError("Deepgram REST API: No channels found in response")
            
            alternatives = channels[0].get("alternatives", [])
            if not alternatives:
                raise ValueError("Deepgram REST API: No alternatives found in response")
                
            transcript = alternatives[0].get("transcript", "")
            detected_lang = channels[0].get("detected_language", "en")
            
            print(f"[Listener] Transcription Success (v4.3 REST): {transcript[:50]}...")
            
            return {
                "text": transcript,
                "lang": detected_lang,
                "error": None
            }
        
        except Exception as e:
            err_msg = f"Deepgram Transcription Error [v4.3 REST]: {str(e)}"
            print(f"[Listener] {err_msg}")
            # Try to print response text if available for the user to see the error from Deepgram
            if 'response' in locals() and hasattr(response, 'text'):
                print(f"[DEBUG] Deepgram Error Body: {response.text}")
            return {"text": "", "lang": "en", "error": err_msg}
