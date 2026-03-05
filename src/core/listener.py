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
            
        self.deepgram = DeepgramClient(api_key=self.api_key)
        print(f"[Listener] Initialized (v3.7). Type: {type(self.deepgram)}")

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
            
            # SMART DISCOVERY: Crawl the SDK to find 'transcribe_file'
            response = None
            success = False
            
            # Step 1: Check known high-level entry points (including v1/v2 found in logs)
            for path in ["v1", "v2", "prerecorded", "rest"]:
                obj = getattr(self.deepgram.listen, path, None)
                if obj and hasattr(obj, "transcribe_file"):
                    try:
                        response = obj.transcribe_file(payload, options)
                        success = True
                        print(f"[DEBUG] Found transcription method via: listen.{path}")
                        break
                    except Exception: continue
            
            # Step 2: If failed, try with .v("1") appended to known paths
            if not success:
                for path in ["v1", "v2", "prerecorded", "rest", ""]:
                    try:
                        obj = self.deepgram.listen if path == "" else getattr(self.deepgram.listen, path, None)
                        if obj and hasattr(obj, "v"):
                            target = obj.v("1")
                            if hasattr(target, "transcribe_file"):
                                response = target.transcribe_file(payload, options)
                                success = True
                                print(f"[DEBUG] Found transcription method via: listen.{path}.v('1')")
                                break
                    except Exception: continue

            # Step 3: Nuclear fallback - iterate EVERYTHING in listen
            if not success:
                for attr in dir(self.deepgram.listen):
                    if attr.startswith("_"): continue
                    try:
                        obj = getattr(self.deepgram.listen, attr)
                        if hasattr(obj, "transcribe_file"):
                            response = obj.transcribe_file(payload, options)
                            success = True
                            print(f"[DEBUG] Found transcription method via blind discovery: listen.{attr}")
                            break
                    except Exception: continue

            if not success:
                # Diagnostic dump for debugging
                print(f"[DEBUG] Full Discovery Failed. Attributes searched: {dir(self.deepgram.listen)}")
                raise AttributeError("Deepgram SDK: Could not find 'transcribe_file' in any attribute of 'deepgram.listen'.")
            
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
            err_msg = f"Deepgram Transcription Error [v3.7]: {str(e)}"
            print(f"[Listener] {err_msg}")
            # Ensure we return a structured dictionary so Orchestrator can handle the message
            return {"text": "", "lang": "en", "error": err_msg}
