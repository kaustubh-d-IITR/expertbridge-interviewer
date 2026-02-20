import streamlit as st
# ExpertBridge AI Interviewer - v1.1
import os
import json # Added import
from src.ingestion.cv_parser import parse_cv
from src.ingestion.question_gen import generate_initial_questions
from src.core.orchestrator import Orchestrator
# from src.utils.sanitizer import clean_ai_response # Removed in Refactor

# Load environment variables
try:
    from dotenv import load_dotenv
    # Force load from absolute path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(current_dir, ".env")
    load_dotenv(env_path, override=True)
except ImportError:
    pass # Expected on Streamlit Cloud (secrets are injected)

# Check for required API keys early
if not (os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")) and not os.getenv("DEEPGRAM_API_KEY"):
     st.warning("⚠️ API Keys missing. Please configure them in your .env file or Streamlit Secrets.")

# Page Config (This will be moved inside main() as per instruction)
# st.set_page_config(page_title="ExpertBridge AI Interviewer", page_icon="🎤")

def main():
    # Page Config
    st.set_page_config(page_title="ExpertBridge AI Interviewer", page_icon="🤖", layout="wide")

    # --- Session State ---
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "expert_profile" not in st.session_state:
        st.session_state.expert_profile = None
    if "interview_active" not in st.session_state:
        st.session_state.interview_active = False
    if "current_phase" not in st.session_state:
        st.session_state.current_phase = "setup"
    if "orchestrator_v3" not in st.session_state or st.session_state.orchestrator_v3 is None:
        try:
            st.session_state.orchestrator_v3 = Orchestrator()
            # Restore profile if available
            if st.session_state.expert_profile:
                st.session_state.orchestrator_v3 = Orchestrator(expert_profile=st.session_state.expert_profile)
        except ValueError as e:
            st.error(f"⚠️ Configuration Missing: {e}")
            st.info("To fix this on Streamlit Cloud:\n1. Go to **Manage App** -> **Settings** -> **Secrets**\n2. Add your keys (Either Azure OR Standard OpenAI):\n```\n# Option 1: Azure\nAZURE_OPENAI_API_KEY = \"...\"\nAZURE_OPENAI_ENDPOINT = \"...\"\n\n# Option 2: Standard OpenAI\nOPENAI_API_KEY = \"sk-...\"\n\n# Required\nDEEPGRAM_API_KEY = \"...\"\n```")
            st.stop()
    if "cv_text" not in st.session_state:
        st.session_state.cv_text = ""
    if "candidate_name" not in st.session_state:
        st.session_state.candidate_name = "Candidate"
    if "coding_mode" not in st.session_state:
        st.session_state.coding_mode = False
    if "debug_logs" not in st.session_state:
        st.session_state.debug_logs = "" # Phase 34: Ensure Debug Logs exist

    # Legacy Module Reload Block Removed in Refactor v3.0
    
    # --- Sidebar Settings ---
    with st.sidebar:
        st.title("⚙️ Interview Settings")
        
        # DEBUG: Show loaded config
        st.divider()
        st.subheader("🔧 Config Debug")
        az_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        az_end = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        oa_key = os.getenv("OPENAI_API_KEY", "")
        
        st.code(f"Start Dir: {current_dir}\n"
                f"Env Path: {env_path}\n"
                f"Exists: {os.path.exists(env_path)}\n"
                f"Azure Key: {az_key[:5]}...{az_key[-3:] if az_key else 'None'}\n"
                f"Azure End: {az_end[:20]}...\n"
                f"OpenAI Key: {oa_key[:5]}...{oa_key[-3:] if oa_key else 'None'}")
        
        # 1. Job Selection
        st.subheader("1. Select Job Role")
        
        # Robust Path Handling
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(base_dir, "output")
        
        job_options = {} # Map "Title" -> "filename"
        if os.path.exists(output_dir):
            files = [f for f in os.listdir(output_dir) if f.endswith(".json")]
            for f in files:
                try:
                    with open(os.path.join(output_dir, f), "r") as json_file:
                        data = json.load(json_file)
                        title = data.get("job_title", f)
                        # Create unique key if needed, or just use title
                        job_options[title] = f
                except Exception:
                    continue # Skip bad json
        
        if not job_options:
            st.warning("No Job Descriptions found in 'output' folder.")
            selected_job_title = "None"
        else:
            selected_job_title = st.selectbox("Choose a Job Description:", ["None"] + list(job_options.keys()))
        
        job_context = None
        if selected_job_title and selected_job_title != "None":
            selected_filename = job_options[selected_job_title]
            with open(os.path.join(output_dir, selected_filename), "r") as f:
                job_context = json.load(f)
            st.success(f"Loaded Role: {job_context.get('job_title', 'Unknown Role')}")
            st.caption(f"Domain: {job_context.get('industry_domain', 'General')}")
            st.session_state.current_job_context = job_context
        else:
            st.session_state.current_job_context = None

        # 2. Voice (Gender only)
        st.subheader("2. Interviewer Voice")
        voice_gender = st.radio("Select Voice", ["Female (Asteria)", "Male (Orion)"], index=0)
        
        # Hardcoded Settings for Phase 5 (Strict English + Recruiter Mode)
        st.session_state.voice_model = "aura-asteria-en" if "Female" in voice_gender else "aura-orion-en"
        st.session_state.input_language = "Auto" # Auto-detect but ignored for output
        st.session_state.response_language = "English" # Strict Enforce
        st.session_state.mode = "recruiter" # Mandatory Recruiter Mode

        st.markdown("---")
        st.info("💡 **System Upgrade:**\n- Strict English Output\n- Auto-Detect Input\n- Mandatory Recruiter Mode")

        # Sidebar: CV Upload (Original content, moved after new settings)
        st.header("Upload Resume")
        uploaded_file = st.file_uploader("Upload PDF CV", type=["pdf"])
        
        if uploaded_file and not st.session_state.interview_active:
            # Start Interview Button Logic
            if st.button("Start Interview"):
                if not st.session_state.expert_profile:
                    st.error("⚠️ Please fill out and SAVE the Candidate Profile in the main window first!")
                else:
                    with st.spinner("Initializing AI Interviewer..."):
                        # Re-initialize Orchestrator with Profile (Phase 17)
                        st.session_state.orchestrator_v3 = Orchestrator(expert_profile=st.session_state.expert_profile)
                        
                        # Parse CV
                        cv_text = parse_cv(uploaded_file)
                        st.session_state.cv_text = cv_text
                        
                        # Start Interview
                        st.session_state.orchestrator_v3.start_interview(
                            st.session_state.candidate_name, 
                            cv_text, 
                            st.session_state.get("current_job_context"),
                            mode=st.session_state.mode
                        )
                    st.session_state.interview_active = True
                    import time
                    st.session_state.start_time = time.time()
                    st.success("Interview Started! Please introduce yourself.")
                    st.rerun()

        # Feature 9: Live Timer (JavaScript) - Robust Version (Now outside the 'not active' block)
        if st.session_state.interview_active:
            import time
            if "start_time" not in st.session_state:
                st.session_state.start_time = time.time()
            
            # Feature: Auto-Refresh for Timer & Termination (Fix for "Timer Keeps Going")
            try:
                from streamlit_autorefresh import st_autorefresh
                # Refresh every 5 seconds to check for termination (Passively)
                st_autorefresh(interval=5000, limit=None, key="interview_timer")
            except ImportError:
                # Fallback if package not installed
                pass
                
            # Use the robust iframe timer from utils
            try:
                from src.utils.timer import display_timer
                
                # Check for termination to freeze timer
                stop_timer = False
                if hasattr(st.session_state.orchestrator_v3, "phase") and st.session_state.orchestrator_v3.phase == "TERMINATED":
                    stop_timer = True
                
                st.sidebar.markdown("---")
                with st.sidebar:
                    display_timer(st.session_state.start_time, stop=stop_timer)
            except ImportError:
                st.sidebar.error("Timer Module Missing")
            
            # Feature 12: Passive Timeout Check (Triggers via Auto-Refresh)
            elapsed = time.time() - st.session_state.start_time
            if elapsed > 905 and not stop_timer: # 15 mins + buffer
                 st.warning("⏳ Time Limit Reached! Wrapping up...")
                 if hasattr(st.session_state.orchestrator_v3, "phase"):
                     st.session_state.orchestrator_v3.phase = "TERMINATED"
                     # Force Score Calculation if missing
                     if st.session_state.orchestrator_v3.scores and st.session_state.orchestrator_v3.final_score == 0:
                         total = sum([s.get("overall_score", 0) for s in st.session_state.orchestrator_v3.scores])
                         st.session_state.orchestrator_v3.final_score = int(total / len(st.session_state.orchestrator_v3.scores))
                 st.rerun()

            
            st.markdown("---")
            if st.button("🔄 Reset Interview", type="primary"):
                # Clear critical session state
                st.session_state.chat_history = []
                st.session_state.interview_active = False
                st.session_state.cv_text = ""
                # Re-init orchestrator logic
                st.session_state.orchestrator_v3 = Orchestrator()
                st.rerun()

    # Main Area
    if st.session_state.interview_active:
        
        # Display Chat History
        for sender, message, _ in st.session_state.chat_history:
             with st.chat_message(sender):
                 # Refactor v3.0: Brain now guarantees clean text
                 st.write(message)

        # Feature 6: Termination Check
        if hasattr(st.session_state.orchestrator_v3, "phase") and st.session_state.orchestrator_v3.phase == "TERMINATED":
             final_score = getattr(st.session_state.orchestrator_v3, "final_score", 0)
             
             st.error(f"🚨 INTERVIEW TERMINATED. Final Score: {final_score}/100")
             
             if final_score > 0:
                st.balloons()
                st.success(f"🏆 Your Performance Score: {final_score}/100")
             else:
                st.error("Termination Reason: Conduct Violation or Time Exceeded with no answers.")
                
             st.warning("Please reset the interview to try again (if allowed).")
             st.stop()
             
        # Debug Logs (Hidden by default)
        with st.expander("🛠️ System Logs (Debug)", expanded=False):
            if "debug_logs" in st.session_state:
                st.text(st.session_state.debug_logs)

        # Audio Input
        audio_key = f"audio_record_{st.session_state.get('audio_key_count', 0)}"
        audio_value = st.audio_input("Record your answer", key=audio_key)

        if audio_value:
             with st.spinner("Listening..."):
                 mime_type = audio_value.type
                 
                 import time
                 elapsed_seconds = time.time() - st.session_state.get("start_time", time.time())
                 
                 settings = {
                    "input_language": st.session_state.get("input_language", "English"),
                    "response_language": st.session_state.get("response_language", "English"),
                    "voice_model": st.session_state.get("voice_model", "aura-asteria-en"),
                    "job_context": st.session_state.get("current_job_context", None),
                    "elapsed_time": elapsed_seconds # Feature 7: Pass elapsed time
                 }

                 user_text, ai_text, ai_audio, _ = st.session_state.orchestrator_v3.run_interview_turn(
                     audio_value, 
                     mime_type,
                     settings=settings
                 )
                 
                 # Feature 34: Capture Debug Logs from Orchestrator
                 if hasattr(st.session_state.orchestrator_v3, "last_error") and st.session_state.orchestrator_v3.last_error:
                     st.session_state.debug_logs += f"\n[ERROR] {st.session_state.orchestrator_v3.last_error}"
                     # Clear it so it doesn't persist forever
                     st.session_state.orchestrator_v3.last_error = None
                 
                 if user_text:
                     st.session_state.chat_history.append(("user", user_text, None))
                     st.session_state.chat_history.append(("assistant", ai_text, ai_audio))
                     st.session_state.audio_key_count = st.session_state.get('audio_key_count', 0) + 1
                     st.rerun()
                 else:
                     st.warning("I couldn't hear that. Please try speaking again/louder.")

        # Autoplay
        if st.session_state.chat_history:
            last_sender, _, last_audio = st.session_state.chat_history[-1]
            if last_sender == "assistant" and last_audio:
                st.audio(last_audio, format="audio/mp3", autoplay=True)
    else:
        # Phase 17: Candidate Profile Form (Main Area)
        st.title("👤 Candidate Profile")
        st.markdown("Please tell us about your background so we can tailor the interview.")
        
        with st.form("profile_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name", value=st.session_state.candidate_name)
                role = st.text_input("Current Role", placeholder="e.g. Senior Backend Engineer")
                years = st.number_input("Years of Experience", min_value=0, max_value=50, value=5)
            with col2:
                skills = st.text_input("Top Skills (comma-separated)", placeholder="Python, AWS, System Design")
                industries = st.text_input("Industries (comma-separated)", placeholder="FinTech, E-commerce, AI")
                companies = st.text_input("Target/Past Companies", placeholder="Google, StartupX")
            
            project = st.text_area("Key Project (Briefly describe one major achievement)", 
                                   placeholder="Built a real-time payment engine handling 10k TPS...")
            
            if st.form_submit_button("💾 Save Profile"):
                st.session_state.candidate_name = name
                st.session_state.expert_profile = {
                    "name": name,
                    "current_role": role,
                    "experience_years": years,
                    "top_skills": skills,
                    "industries": industries,
                    "past_companies": companies,
                    "key_project": project
                }
                st.success("✅ Profile Saved! You can now upload your CV in the sidebar and start.")

        st.info("👈 **Next Step:** Upload your CV in the sidebar and click 'Start Interview'.")

if __name__ == "__main__":
    main()
