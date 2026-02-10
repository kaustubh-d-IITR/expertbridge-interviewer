import streamlit as st
# ExpertBridge AI Interviewer - v1.1
import os
import json # Added import
from src.ingestion.cv_parser import parse_cv
from src.ingestion.question_gen import generate_initial_questions
from src.core.orchestrator import Orchestrator

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass # Expected on Streamlit Cloud (secrets are injected)

# Check for required API keys early
if not os.getenv("AZURE_OPENAI_API_KEY") and not os.getenv("DEEPGRAM_API_KEY"):
     st.warning("⚠️ API Keys missing. Please configure them in your .env file or Streamlit Secrets.")

# Page Config (This will be moved inside main() as per instruction)
# st.set_page_config(page_title="ExpertBridge AI Interviewer", page_icon="🎤")

def main():
    # Page Config
    st.set_page_config(page_title="ExpertBridge AI Interviewer", page_icon="🤖", layout="wide")

    # --- Session State ---
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "interview_active" not in st.session_state:
        st.session_state.interview_active = False
    if "current_phase" not in st.session_state:
        st.session_state.current_phase = "setup"
    if "orchestrator" not in st.session_state:
        try:
            st.session_state.orchestrator = Orchestrator()
        except ValueError as e:
            st.error(f"⚠️ Configuration Missing: {e}")
            st.info("To fix this on Streamlit Cloud:\n1. Go to **Manage App** -> **Settings** -> **Secrets**\n2. Add your keys:\n```\nAZURE_OPENAI_API_KEY = \"...\"\nAZURE_OPENAI_ENDPOINT = \"...\"\nDEEPGRAM_API_KEY = \"...\"\n```")
            st.stop()
    if "cv_text" not in st.session_state:
        st.session_state.cv_text = ""
    if "candidate_name" not in st.session_state:
        st.session_state.candidate_name = "Candidate"
    if "coding_mode" not in st.session_state:
        st.session_state.coding_mode = False
    
    # --- Sidebar Settings ---
    with st.sidebar:
        st.title("⚙️ Interview Settings")
        
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

        # 2. Language & Voice
        st.subheader("2. Audio Settings")
        language = st.selectbox("Interview Language", ["English", "Hindi", "French", "Spanish"], index=0)
        voice_gender = st.radio("Interviewer Voice", ["Female (Asteria)", "Male (Orion)"], index=0)
        
        # Store settings in session state for other modules to access
        st.session_state.voice_model = "aura-asteria-en" if "Female" in voice_gender else "aura-orion-en"
        st.session_state.language = language

        st.markdown("---")
        st.info("💡 **Phase 2 Update:**\nCoding challenges disabled.\nFocus on Domain Expertise.")

        # Sidebar: CV Upload (Original content, moved after new settings)
        st.header("Upload Resume")
        uploaded_file = st.file_uploader("Upload PDF CV", type=["pdf"])
        
        if uploaded_file and not st.session_state.interview_active:
            if st.button("Start Interview"):
                with st.spinner("Analyzing CV..."):
                    # Parse CV
                    cv_text = parse_cv(uploaded_file)
                    st.session_state.cv_text = cv_text
                    
                    # Initialize Orchestrator
                    st.session_state.orchestrator.start_interview(
                        st.session_state.candidate_name, 
                        cv_text, 
                        st.session_state.get("current_job_context")
                    )
                    st.session_state.interview_active = True
                    st.success("Interview Started! Please introduce yourself.")
        
        # Reset Button (For Testing)
        if st.session_state.interview_active:
            st.markdown("---")
            if st.button("🔄 Reset Interview", type="primary"):
                # Clear critical session state
                st.session_state.chat_history = []
                st.session_state.interview_active = False
                st.session_state.cv_text = ""
                # Re-init orchestrator logic if needed, or just let next start handle it
                # Effectively "Stop"
                st.rerun()

    # Main Area
    if st.session_state.interview_active:
        
        # Display Chat History
        for sender, message, _ in st.session_state.chat_history:
             with st.chat_message(sender):
                 st.write(message)

        # Audio Input
        audio_key = f"audio_record_{st.session_state.get('audio_key_count', 0)}"
        audio_value = st.audio_input("Record your answer", key=audio_key)

        if audio_value:
             with st.spinner("Listening..."):
                 mime_type = audio_value.type
                 
                 settings = {
                    "language": st.session_state.get("language", "English"),
                    "voice_model": st.session_state.get("voice_model", "aura-asteria-en"),
                    "job_context": st.session_state.get("current_job_context", None)
                 }

                 user_text, ai_text, ai_audio, _ = st.session_state.orchestrator.run_interview_turn(
                     audio_value, 
                     mime_type,
                     settings=settings
                 )
                 
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
        st.info("Please upload a CV and click 'Start Interview' to begin.")

if __name__ == "__main__":
    main()
