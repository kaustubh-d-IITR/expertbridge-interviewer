import time
from typing import Dict, Any, Optional
from src.core.brain import Brain
from src.core.listener import Listener
from src.core.speaker import Speaker

class Orchestrator:
    """
    Refactored Orchestrator (Adapter Pattern) for v3.0 Brain.
    """
    def __init__(self, expert_profile: Optional[Dict] = None):
        self.brain = Brain(expert_profile=expert_profile)
        self.listener = Listener() # Deepgram
        self.speaker = Speaker() # Deepgram Aura
        self.expert_profile = expert_profile
        self.transcript = []
        self.scores = []
        self.phase = "READY"
        self.start_time = None
        self.final_score = 0
        self.final_score = 0
        self.question_count = 0 
        self.last_error = None # Feature 34
        
        
    def start_interview(self, candidate_name, cv_text, job_context=None, mode="standard"):
        self.start_time = time.time()
        self.phase = "ACTIVE"
        self.transcript = []
        self.scores = []

    def run_interview_turn(self, audio_input, mime_type="audio/wav", settings=None):
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        
        try:
            transcription_result = self.listener.get_transcription(audio_input, mime_type)
            if isinstance(transcription_result, dict):
                user_text = transcription_result.get("text", "")
            else:
                user_text = str(transcription_result)
            
            if not user_text:
                return None, "I didn't catch that. Could you repeat?", None, False
        except Exception as e:
            print(f"[Orchestrator] Transcription error: {e}")
            return None, "I'm having trouble hearing you. Please try again.", None, False
        
        try:
            brain_result = self.brain.handle_user_input(user_text, elapsed_time)
            ai_text = brain_result["spoken_response"]
            analysis = brain_result["analysis"]
            should_terminate = brain_result["terminate"]
            ai_text = brain_result["spoken_response"]
            analysis = brain_result["analysis"]
            should_terminate = brain_result["terminate"]
            self.phase = brain_result["phase"]
            
            # Feature 34: Check for suppressed Brain errors
            if self.brain.last_error:
                self.last_error = f"[Brain Internal] {self.brain.last_error}"
                # We don't overwrite ai_text because it contains the polite message
                self.brain.last_error = None # Clear it

        except Exception as e:
            error_msg = f"[Brain Error] {str(e)}"
            print(error_msg)
            # Return the error message as the 4th element (was coding_mode, getting hijacked for debug info or we add a 5th?)
            # Wait, main_app expects 4 values. Let's hijack the 2nd value (ai_text) to include a user friendly message, 
            # and we need a way to pass the debug log. 
            # Actually, I can append to a global log or return a tuple with error info.
            # Compatibility: main_app expects (user_text, ai_text, ai_audio, coding_mode).
            # Let's attach the error to the ai_text temporarily or use a side channel? 
            # BETTER: Orchestrator has state. I can store the last error in self.last_error?
            self.last_error = error_msg
            return user_text, "I'm having a technical issue. Please check the System Logs below for details.", None, False
        
        ai_audio = None
        try:
            voice = "aura-asteria-en"
            if settings and "voice_model" in settings:
                voice = settings["voice_model"]
            ai_audio = self.speaker.text_to_speech(ai_text, voice_model=voice)
        except Exception as e:
            print(f"[Orchestrator] Speaker error: {e}")
        
        self.transcript.append({"role": "user", "text": user_text, "timestamp": elapsed_time})
        self.transcript.append({"role": "ai", "text": ai_text, "timestamp": elapsed_time})
        
        if analysis:
            self.scores.append(analysis)
            
        if self.scores:
            total = sum([s.get("overall_score", 0) for s in self.scores if isinstance(s, dict)])
            self.final_score = int(total / len(self.scores))
            
        if should_terminate:
            self.phase = "TERMINATED"
            
        return user_text, ai_text, ai_audio, False
    
    def get_final_report(self) -> Dict[str, Any]:
        return {
            "average_score": self.final_score,
            "scores": self.scores,
            "transcript": self.transcript,
            "duration": time.time() - self.start_time if self.start_time else 0
        }
