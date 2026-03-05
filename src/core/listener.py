import os
import json
from deepgram import DeepgramClient, PrerecordedOptions, FileSource

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
        print(f"[Listener] Initialized (v3.8). API Key from: {source}")

    def get_transcription(self, audio_data, mime_type="audio/wav"):
        """
        Transcribes audio data using Deepgram's Prerecorded API with official v3 syntax.
        """
        try:
            # Prepare payload for v3
            # Streamlit passes bytes, we wrap them in FileSource
            payload: FileSource = {"buffer": audio_data}
            
            # Configure options
            options = PrerecordedOptions(
                model="nova-2",
                language="en",
                smart_format=True,
                utterances=False, # Basic transcript
                punctuate=True
            )
            
            print(f"[DEBUG] Starting transcription v3.8 (Size: {len(audio_data)} bytes)")

            # Call official v3 endpoint
            response = self.deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
            
            # Convert response to dictionary if it's an object (SDK behavior varies)
            if not isinstance(response, dict):
                try:
                    response_dict = json.loads(response.to_json())
                except:
                    response_dict = response
            else:
                response_dict = response

            # Log raw response keys for debugging if it fails
            # print(f"[DEBUG] Deepgram keys: {response_dict.keys()}")

            transcript = response_dict["results"]["channels"][0]["alternatives"][0]["transcript"]
            detected_lang = response_dict.get("results", {}).get("channels", [{}])[0].get("detected_language", "en")
            
            print(f"[Listener] Transcription Success (v3.8): {transcript[:50]}...")
            
            return {
                "text": transcript,
                "lang": detected_lang,
                "error": None
            }
        
        except Exception as e:
            err_msg = f"Deepgram Transcription Error [v3.8]: {str(e)}"
            print(f"[Listener] {err_msg}")
            # Diagnostic dump
            try:
                print(f"[DEBUG] Listener Dir: {dir(self.deepgram.listen)}")
                if hasattr(self.deepgram.listen, "prerecorded"):
                    print(f"[DEBUG] Prerecorded Dir: {dir(self.deepgram.listen.prerecorded)}")
            except: pass
            
            return {"text": "", "lang": "en", "error": err_msg}
