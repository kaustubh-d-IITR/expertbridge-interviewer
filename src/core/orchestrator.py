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

    def start_interview(self, candidate_name, cv_text, job_context=None):
        """
        Initializes the interview with optional Job Context.
        """
        self.brain.set_context(candidate_name, cv_text, job_context)

    def run_interview_turn(self, audio_input, mime_type="audio/wav", settings=None):
        """
        Runs one turn of the interview: Audio -> Text -> Brain -> Audio.
        Accepts settings dict for customization.
        """
        if not settings:
            settings = {}

        # 1. Listener: Transcribe audio
        # Pass language if needed (future expansion)
        user_text = self.listener.get_transcription(audio_input, mime_type) # could add language here
        
        if not user_text:
            return None, "I didn't hear anything.", None, False

        # 2. Brain: Generate response
        try:
             ai_text = self.brain.generate_response(user_text)
        except Exception as e:
             ai_text = "I am having trouble thinking clearly. Let's move on."
             print(f"Brain Error: {e}")

        # 3. Speaker: Convert response to audio
        voice_model = settings.get("voice_model", "aura-asteria-en")
        ai_audio = self.speaker.text_to_speech(ai_text, voice_model=voice_model)
        
        return user_text, ai_text, ai_audio, False # Never triggers coding mode
