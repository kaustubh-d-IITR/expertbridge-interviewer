from src.core.listener import Listener
from src.core.brain import InterviewBrain
from src.core.speaker import Speaker

class Orchestrator:
    def __init__(self, expert_profile=None):
        self.listener = Listener()
        # Phase 17: Pass profile to Brain
        self.brain = InterviewBrain(expert_profile=expert_profile)
        self.speaker = Speaker()
        
        # Interview State
        self.phase = "INTERVIEW" 
        self.question_count = 0
        self.max_questions = 7 
        self.final_warning_given = False 
        self.scores = [] # Feature 8: Track scores
        self.final_score = 0

    def start_interview(self, candidate_name, cv_text, job_context=None, mode="standard"):
        """
        Initializes the interview with optional Job Context.
        """
        self.final_warning_given = False 
        self.scores = []
        self.final_score = 0
        self.brain.set_context(candidate_name, cv_text, job_context, mode=mode)

    def run_interview_turn(self, audio_input, mime_type="audio/wav", settings=None):
        """
        Runs one turn of the interview: Audio -> Text -> Brain -> Audio.
        Accepts settings dict for customization.
        """
        if not settings:
            settings = {}

        # Feature 7: Time Management Logic
        elapsed_time = settings.get("elapsed_time", 0)
        
        # A. Hard Stop (15 Minutes = 900s). Buffer at 890s.
        if elapsed_time > 890:
             self.phase = "TERMINATED"
             # Calculate Average Score
             if self.scores:
                 self.final_score = int(sum(self.scores) / len(self.scores))
             else:
                 self.final_score = 0
             return None, f"Time is up. The interview is now over. Your Final Score: {self.final_score}/100. Thank you.", None, False

        # 1. Listener: Transcribe audio
        transcription_result = self.listener.get_transcription(audio_input, mime_type)
        
        # ... (Listener logic unchanged) ...
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

        # Feature 7B: 13 Minute Warning (780s)
        if elapsed_time > 780 and not self.final_warning_given:
            print("[Orchestrator] 13 Minute Mark - Injecting Final Question Prompt")
            user_text = "[SYSTEM ALERT: Time is almost up (13 mins passed). You must ask ONE FINAL short question and then wrap up. Do NOT ask multiple questions.]\n\n" + user_text
            self.final_warning_given = True

        # 2. Brain: Generate response
        try:
             # Feature 2 & 4: Pass detected language AND strict response language
             response_lang = settings.get("response_language", None)
             
             brain_response = self.brain.generate_response(
                 user_text, 
                 detected_language=detected_lang,
                 response_language=response_lang
             )
             
             # Feature 6: Handle Signal Score (Hidden) & Termination
             if isinstance(brain_response, dict):
                 ai_text = brain_response.get("text", "")
                 signal_score = brain_response.get("score", 0)
                 terminate = brain_response.get("terminate", False)
                 
                 # Store Score
                 if signal_score > 0:
                     self.scores.append(signal_score)
                 
                 print(f"[Orchestrator] Signal Quality Score: {signal_score}/100")
                 
                 if terminate:
                     self.phase = "TERMINATED"
                     # Phase 18 Fix: Don't zero out score. Give them their average.
                     # Unless it's a very low score loop, but per user request -> "whatever current score he has"
                     if self.scores:
                         self.final_score = int(sum(self.scores) / len(self.scores))
                     else:
                         self.final_score = 0
                     print(f"[Orchestrator] INTERVIEW TERMINATED BY AI. Final Score: {self.final_score}")
             else:
                 ai_text = brain_response
                 
        except Exception as e:
             ai_text = "I am having trouble thinking clearly. Let's move on."
             print(f"Brain Error: {e}")

        # 3. Speaker: Convert response to audio
        voice_model = settings.get("voice_model", "aura-asteria-en")
        response_lang = settings.get("response_language", None)
        
        # TTS Language: Use explicit response language if set, else detected
        tts_lang = response_lang if response_lang else detected_lang
        
        try:
            ai_audio = self.speaker.text_to_speech(ai_text, voice_model=voice_model, language=tts_lang)
        except Exception as e:
            print(f"Speaker Error: {e}")
            ai_audio = None
        
        return user_text, ai_text, ai_audio, False # Never triggers coding mode
