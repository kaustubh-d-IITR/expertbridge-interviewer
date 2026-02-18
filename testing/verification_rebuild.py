
import os
import sys
import time
import json
import io
from reportlab.pdfgen import canvas
from src.ingestion.cv_parser import parse_cv
from src.core.orchestrator import Orchestrator

# Setup Logging
def log_step(step, status, details=""):
    symbol = "✅" if status == "PASS" else "❌"
    print(f"\n{symbol} [STEP {step}]: {status}")
    if details:
        print(f"   Details: {details}")

def create_dummy_pdf(filename="test_cv.pdf"):
    try:
        c = canvas.Canvas(filename)
        c.drawString(100, 750, "John Doe")
        c.drawString(100, 730, "Senior Software Engineer")
        c.drawString(100, 710, "Skills: Python, AWS, System Design")
        c.drawString(100, 690, "Experience: Used Deepgram and OpenAI to build AI agents.")
        c.save()
        return True, filename
    except Exception as e:
        return False, str(e)

def main():
    print("🚀 STARTING VERIFICATION: AI_REBUILD Backend Flow\n")
    
    # 1. Environment Check
    api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    deepgram_key = os.getenv("DEEPGRAM_API_KEY")
    
    if not api_key:
        log_step(1, "FAIL", "Missing Azure/OpenAI API Key")
        return
    if not deepgram_key:
        log_step(1, "FAIL", "Missing Deepgram API Key")
        return
    log_step(1, "PASS", "Environment Variables Loaded")

    # 2. Resume Parsing
    success, pdf_path = create_dummy_pdf()
    if not success:
        log_step(2, "FAIL", f"Could not create dummy PDF: {pdf_path}")
        return
    
    try:
        with open(pdf_path, "rb") as f:
            cv_text = parse_cv(f)
        if "John Doe" in cv_text and "Python" in cv_text:
            log_step(2, "PASS", f"PDF Parsed Successfully ({len(cv_text)} chars)")
        else:
            log_step(2, "FAIL", "PDF Parsed but content mismatch")
            print(f"   Extracted: {cv_text[:100]}...")
    except Exception as e:
        log_step(2, "FAIL", f"Parsing Exception: {e}")
        return

    # 3. Initialization
    try:
        # Dummy Profile
        expert_profile = {
            "name": "John Doe",
            "current_role": "Senior Software Engineer",
            "experience_years": 5,
            "top_skills": "Python, AWS",
            "key_project": "AI Agent System"
        }
        
        orch = Orchestrator(expert_profile=expert_profile)
        log_step(3, "PASS", "Orchestrator Initialized")
    except Exception as e:
        log_step(3, "FAIL", f"Initialization Failed: {e}")
        return

    # 4. Start Interview
    try:
        orch.start_interview("John Doe", cv_text, job_context=None, mode="recruiter")
        if orch.phase == "ACTIVE":
             log_step(4, "PASS", "Interview Started (Phase: ACTIVE)")
        else:
             log_step(4, "FAIL", f"Interview Phase Invalid: {orch.phase}")
    except Exception as e:
        log_step(4, "FAIL", f"Start Interview Error: {e}")
        return

    # 5. Process Turn (Audio -> Audio)
    # Check for debug_audio.wav or create dummy
    audio_file = "debug_audio.wav"
    if not os.path.exists(audio_file):
        print("   [INFO] debug_audio.wav not found. Skipping Audio Input test (Simulating text input via internal methods if possible, or failing).")
        # Creating a dummy text injection for testing would be ideal, but Orchestrator takes audio.
        # We can try to use a dummy file, but Deepgram will reject it.
        # Let's hope debug_audio.wav exists as seen in file list.
        log_step(5, "WARNING", "debug_audio.wav missing. Cannot verify Deepgram Listener.")
        audio_data = None
    else:
        with open(audio_file, "rb") as f:
            audio_data = f.read()

    if audio_data:
        try:
            print("   [INFO] Sending Audio to Orchestrator (This calls Deepgram + OpenAI + Deepgram TTS)... calling real APIs...")
            start_t = time.time()
            
            # Run Turn
            user_text, ai_text, ai_audio, coding_mode = orch.run_interview_turn(audio_data, mime_type="audio/wav")
            
            duration = time.time() - start_t
            print(f"   [INFO] Turn Duration: {duration:.2f}s")
            
            # Checks
            checks = []
            if user_text and len(user_text) > 0: checks.append("STT (Listener)")
            if ai_text and len(ai_text) > 0: checks.append("LLM (Brain)")
            if ai_audio and len(ai_audio) > 1000: checks.append("TTS (Speaker)")
            
            if len(checks) == 3:
                log_step(5, "PASS", f"Full Turn Complete. Verified: {', '.join(checks)}")
                print(f"   User said: {user_text}")
                print(f"   AI said: {ai_text}")
                print(f"   Audio size: {len(ai_audio)} bytes")
            else:
                log_step(5, "FAIL", f"Incomplete Turn. Verified: {', '.join(checks)}")
                print(f"   [DEBUG] user_text: '{user_text}'")
                print(f"   [DEBUG] ai_text: '{ai_text}'")
                print(f"   [DEBUG] ai_audio type: {type(ai_audio)}")
                if hasattr(ai_audio, '__len__'):
                    print(f"   [DEBUG] ai_audio len: {len(ai_audio)}")
                if not user_text: print("   ❌ Listener Result Empty")
                
        except Exception as e:
            log_step(5, "FAIL", f"Turn Execution Exception: {e}")

    # 6. Check Analysis
    try:
        if orch.scores:
            latest_score = orch.scores[-1]
            if isinstance(latest_score, dict) and "overall_score" in latest_score:
                log_step(6, "PASS", f"Scoring Verified: {latest_score.get('overall_score')}/100")
            else:
                log_step(6, "FAIL", f"Invalid Score Format: {latest_score}")
        else:
             # If turn failed, scores might be empty
             log_step(6, "SKIP", "No scores generated (Turn failed or no analysis)")
    except Exception as e:
        log_step(6, "FAIL", f"Scoring Check Error: {e}")

    print("\n🏁 VERIFICATION COMPLETE.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(override=True)
    main()
