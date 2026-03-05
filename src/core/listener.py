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
        print(f"[Listener] Initialized (v4.2). API Key from: {source}")

    def get_transcription(self, audio_data, mime_type="audio/wav"):
        """
        Transcribes audio data using Deepgram's Prerecorded API with official v4.x+ routing.
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

            print(f"[DEBUG] Starting transcription v4.2 (Size: {len(audio_bytes)} bytes)")

            # Official v4.x+ Routing Logic
            response = None
            success = False
            
            # Attempt 1: New v4.x routing (.rest instead of .prerecorded)
            try:
                if hasattr(self.deepgram.listen, "rest"):
                    response = self.deepgram.listen.rest.v("1").transcribe_file(payload, options)
                    success = True
                    print("[DEBUG] Used v4.x routing: listen.rest")
            except Exception: pass

            # Attempt 2: Newest v5/v6 fallback (.v1.media)
            if not success:
                try:
                    if hasattr(self.deepgram.listen, "v1"):
                        response = self.deepgram.listen.v1.media.transcribe_file(payload, options)
                        success = True
                        print("[DEBUG] Used v5/v6 routing: listen.v1.media")
                except Exception: pass

            # Attempt 3: Legacy v3.x fallback (.prerecorded)
            if not success:
                try:
                    if hasattr(self.deepgram.listen, "prerecorded"):
                        response = self.deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
                        success = True
                        print("[DEBUG] Used legacy v3.x routing: listen.prerecorded")
                except Exception: pass

            if not success:
                # Diagnostic dump if all fallbacks fail
                print(f"[DEBUG] Full Discovery Failed. Listen Dir: {dir(self.deepgram.listen)}")
                raise AttributeError("Deepgram SDK: Could not find a valid transcription method in any known path (v4.2).")

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
            
            print(f"[Listener] Transcription Success (v4.2): {transcript[:50]}...")
            
            return {
                "text": transcript,
                "lang": detected_lang,
                "error": None
            }
        
        except Exception as e:
            err_msg = f"Deepgram Transcription Error [v4.2]: {str(e)}"
            print(f"[Listener] {err_msg}")
            return {"text": "", "lang": "en", "error": err_msg}
