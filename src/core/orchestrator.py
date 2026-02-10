from src.core.listener import Listener
from src.core.brain import InterviewBrain
from src.core.speaker import Speaker

class Orchestrator:
    def __init__(self):
        self.listener = Listener()
        self.brain = InterviewBrain()
        self.speaker = Speaker()
        
        # Interview State
        self.phase = "THEORY" # THEORY, CODING, CONCLUSION
        self.theory_question_count = 0
        self.coding_question_count = 0
        self.max_theory = 5
        self.max_coding = 2

    def start_interview(self, candidate_name, cv_text):
        self.brain.set_context(candidate_name, cv_text)

    def run_interview_turn(self, audio_input, mime_type="audio/wav"):
        """
        Runs one turn of the interview: Audio -> Text -> Brain -> Audio.
        Handles phase transitions automatically.
        """
        if self.phase == "CONCLUSION":
            return None, "The interview is over. Thank you!", None, False

        # 1. Listener: Transcribe audio
        user_text = self.listener.get_transcription(audio_input, mime_type)
        if not user_text:
            return None, "I didn't hear anything.", None, False

        # 2. Brain: Generate response
        # Force phase shift if needed
        if self.phase == "THEORY":
            self.theory_question_count += 1
            if self.theory_question_count >= self.max_theory:
                self.phase = "CODING"
                # Inject a system message to force the AI to switch topics
                self.brain.history.append({"role": "system", "content": "THEORY Phase complete. Switch to CODING phase now. Ask the first coding question. Do not ask more theory."})

        ai_text = self.brain.generate_response(user_text)

        # Check for Coding Mode trigger logic
        coding_mode = False
        if self.phase == "CODING" or "[CODING]" in ai_text:
             coding_mode = True
             if "[CODING]" in ai_text:
                 ai_text = ai_text.replace("[CODING]", "").strip()

        # 3. Speaker: Convert response to audio
        ai_audio = self.speaker.text_to_speech(ai_text)
        
        return user_text, ai_text, ai_audio, coding_mode

    def submit_code(self, code_snippet):
        """
        Evaluates submitted code and progresses the interview.
        """
        evaluation = self.brain.evaluate_code(code_snippet)
        self.coding_question_count += 1
        
        # Inject instruction for next turn
        if self.coding_question_count < self.max_coding:
             self.brain.history.append({"role": "system", "content": "Code submitted. Feedback given. Ask the SECOND coding question now."})
        else:
             self.brain.history.append({"role": "system", "content": "Code submitted. Interview complete. Wrap up and thank the candidate."})
             self.phase = "CONCLUSION"
             
        return evaluation

    def check_coding_status(self):
        """
        Returns True if we should ask another coding question, False if we should move to conclusion.
        """
        if self.coding_question_count >= self.max_coding:
            self.phase = "CONCLUSION"
            return False
        return True
