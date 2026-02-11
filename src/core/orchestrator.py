from src.core.listener import Listener
from src.core.brain import InterviewBrain
from src.core.speaker import Speaker

class Orchestrator:
    def __init__(self):
        self.listener = Listener()
        self.brain = InterviewBrain()
        self.speaker = Speaker()
        
        # Interview State
        self.phase = "INTERVIEW" 
        self.question_count = 0
        self.max_questions = 7 # Increased for depth

    def start_interview(self, candidate_name, cv_text, job_context=None, mode="standard"):
        """
        Initializes the interview with optional Job Context.
        """
        self.brain.set_context(candidate_name, cv_text, job_context, mode=mode)

    def run_interview_turn(self, audio_input, mime_type="audio/wav", settings=None):
        """
        Runs one turn of the interview: Audio -> Text -> Brain -> Audio.
        Accepts settings dict for customization.
        """
        if not settings:
            settings = {}

        # 1. Listener: Transcribe audio
        transcription_result = self.listener.get_transcription(audio_input, mime_type)
        
        # Handle new dict format (Feature 1) or legacy string
        if isinstance(transcription_result, dict):
            user_text = transcription_result.get("text", "")
            detected_lang = transcription_result.get("lang", "en")
            # Update settings with detected language for this turn
            settings["detected_language"] = detected_lang
            print(f"[Orchestrator] Detected Language: {detected_lang}")
        else:
            user_text = transcription_result
            detected_lang = "en"
        
        if not user_text:
            return None, "I didn't hear anything.", None, False

        # 2. Brain: Generate response
        try:
             # Feature 2: Pass detected language for adaptive response
             brain_response = self.brain.generate_response(user_text, detected_language=detected_lang)
             
             # Feature 6: Handle Signal Score (Hidden)
             if isinstance(brain_response, dict):
                 ai_text = brain_response.get("text", "")
                 signal_score = brain_response.get("score", 0)
                 print(f"[Orchestrator] Signal Quality Score: {signal_score}/100")
                 # We could store this in self.scores list if we wanted to track it over time
             else:
                 ai_text = brain_response
                 
        except Exception as e:
             ai_text = "I am having trouble thinking clearly. Let's move on."
             print(f"Brain Error: {e}")

        # 3. Speaker: Convert response to audio
        voice_model = settings.get("voice_model", "aura-asteria-en")
        try:
            ai_audio = self.speaker.text_to_speech(ai_text, voice_model=voice_model, language=detected_lang)
        except Exception as e:
            print(f"Speaker Error: {e}")
            ai_audio = None
        
        return user_text, ai_text, ai_audio, False # Never triggers coding mode
