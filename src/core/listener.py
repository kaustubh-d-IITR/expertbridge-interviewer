import os
import json
from deepgram import DeepgramClient

# RESILIENT IMPORTS: SDK behavior varies between minor versions on various platforms
try:
    from deepgram import PrerecordedOptions, FileSource
except ImportError:
    try:
        from deepgram.clients.prerecorded.v1 import PrerecordedOptions, FileSource
    except ImportError:
        # Final fallback: use dictionaries if the classes are missing
        PrerecordedOptions = dict
        FileSource = dict

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
            
        self.deepgram = DeepgramClient(api_key=self.api_key)
        print(f"[Listener] Initialized (v4.0). API Key from: {source}")

    def get_transcription(self, audio_data, mime_type="audio/wav"):
        """
        Transcribes audio data using Deepgram's Prerecorded API with official v3 syntax and byte extraction.
        """
        try:
            # Extract raw bytes if it's a Streamlit UploadedFile or file-like object
            if hasattr(audio_data, 'read'):
                audio_bytes = audio_data.read()
            else:
                audio_bytes = audio_data

            # Prepare payload with raw bytes
            payload: FileSource = {"buffer": audio_bytes}
            
            # Configure options
            options_dict = {
                "model": "nova-2",
                "smart_format": True,
                "punctuate": True,
                "utterances": False
            }
            
            # Use PrerecordedOptions class if available, else dict
            try:
                options = PrerecordedOptions(**options_dict) if PrerecordedOptions is not dict else options_dict
            except:
                options = options_dict

            print(f"[DEBUG] Starting transcription v4.0 (Size: {len(audio_bytes)} bytes)")

            # Official v3 endpoint call with path discovery
            try:
                response = self.deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
            except (AttributeError, Exception):
                if hasattr(self.deepgram.listen, "prerecorded"):
                    response = self.deepgram.listen.prerecorded.transcribe_file(payload, options)
                elif hasattr(self.deepgram.listen, "rest"):
                    response = self.deepgram.listen.rest.v("1").transcribe_file(payload, options)
                else:
                    raise AttributeError("Could not find a valid transcription method path.")

            # Convert response to dictionary safely
            if not isinstance(response, dict):
                try:
                    response_dict = json.loads(response.to_json())
                except:
                    response_dict = response
            else:
                response_dict = response

            transcript = response_dict["results"]["channels"][0]["alternatives"][0]["transcript"]
            detected_lang = response_dict.get("results", {}).get("channels", [{}])[0].get("detected_language", "en")
            
            print(f"[Listener] Transcription Success (v4.0): {transcript[:50]}...")
            
            return {
                "text": transcript,
                "lang": detected_lang,
                "error": None
            }
        
        except Exception as e:
            err_msg = f"Deepgram Transcription Error [v4.0]: {str(e)}"
            print(f"[Listener] {err_msg}")
            return {"text": "", "lang": "en", "error": err_msg}
