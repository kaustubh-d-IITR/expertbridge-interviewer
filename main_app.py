import streamlit as st
# ExpertBridge AI Interviewer - v1.1
import os
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

# Page Config
st.set_page_config(page_title="ExpertBridge AI Interviewer", page_icon="🎤")

def main():
    st.title("ExpertBridge AI Interviewer 🤖")

    # Initialize Session State
    if "orchestrator" not in st.session_state:
        try:
            st.session_state.orchestrator = Orchestrator()
        except ValueError as e:
            st.error(f"⚠️ Configuration Missing: {e}")
            st.info("To fix this on Streamlit Cloud:\n1. Go to **Manage App** -> **Settings** -> **Secrets**\n2. Add your keys:\n```\nAZURE_OPENAI_API_KEY = \"...\"\nAZURE_OPENAI_ENDPOINT = \"...\"\nDEEPGRAM_API_KEY = \"...\"\n```")
            st.stop()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "interview_active" not in st.session_state:
        st.session_state.interview_active = False
    if "cv_text" not in st.session_state:
        st.session_state.cv_text = ""
    if "candidate_name" not in st.session_state:
        st.session_state.candidate_name = "Candidate"
    if "coding_mode" not in st.session_state:
        st.session_state.coding_mode = False
    
    # Sidebar: CV Upload
    with st.sidebar:
        st.header("Upload Resume")
        uploaded_file = st.file_uploader("Upload PDF CV", type=["pdf"])
        
        if uploaded_file and not st.session_state.interview_active:
            if st.button("Start Interview"):
                with st.spinner("Analyzing CV..."):
                    # Parse CV
                    cv_text = parse_cv(uploaded_file)
                    st.session_state.cv_text = cv_text
                    
                    # Generate Questions (Optional display or priming)
                    questions = generate_initial_questions(cv_text)
                    if questions and any("Error" in q for q in questions): # Basic error check
                         st.error("Error generating questions. Check API keys.")
                    # else:
                    #     st.write("### topics identified:")
                    #     for q in questions:
                    #         st.write(f"- {q}")
                    
                    # Initialize Orchestrator
                    st.session_state.orchestrator.start_interview(st.session_state.candidate_name, cv_text)
                    st.session_state.interview_active = True
                    st.success("Interview Started! Please introduce yourself.")

    # Main Area
    if st.session_state.interview_active:
        
        # Tabs for Voice and Coding
        tab1, tab2 = st.tabs(["🎤 Voice Interview", "💻 Coding Challenge"])
        
        with tab1:
            # Display Chat History
            for sender, message, _ in st.session_state.chat_history:
                with st.chat_message(sender):
                    st.write(message)

            # Audio Input
            audio_key = f"audio_record_{st.session_state.get('audio_key_count', 0)}"
            try:
                audio_value = st.audio_input("Record your answer", key=audio_key)
            except AttributeError:
                 st.warning("st.audio_input not supported. Use text input for debug?")
                 audio_value = None

            # Debug: Check audio input properties
            if audio_value:
                 st.write(f"Audio Input Type: {type(audio_value)}")
                 st.write(f"Audio Input Size: {audio_value.getbuffer().nbytes} bytes")

            if audio_value:
                 # Process the audio input
                 with st.spinner("Listening..."):
                     # Pass the mimetype as well for better Deepgram handling
                     mime_type = audio_value.type
                     st.write(f"Detected MIME Type: {mime_type}") # Debug
                     
                     user_text, ai_text, ai_audio, coding_triggered = st.session_state.orchestrator.run_interview_turn(audio_value, mime_type)
                     
                     if coding_triggered:
                         st.session_state.coding_mode = True
                         st.toast("Coding Challenge Unlocked! Check the Coding Tab.", icon="💻")
                     
                     if user_text:
                         # Add to history
                         st.session_state.chat_history.append(("user", user_text, None))
                         st.session_state.chat_history.append(("assistant", ai_text, ai_audio))
                         
                         # Increment key to reset audio widget
                         st.session_state.audio_key_count = st.session_state.get('audio_key_count', 0) + 1
                         
                         # Rerun to display new messages
                         st.rerun()
                     else:
                         st.warning("I couldn't hear that. Please try speaking again/louder or check your microphone.")

            # Autoplay latest AI audio
            if st.session_state.chat_history:
                last_sender, _, last_audio = st.session_state.chat_history[-1]
                if last_sender == "assistant" and last_audio:
                    st.audio(last_audio, format="audio/mp3", autoplay=True)
        
        with tab2:
            st.header("Coding Challenge")
            if st.session_state.coding_mode:
                st.info("The interviewer has asked you to solve a coding problem.")
                code = st.text_area("Write your code here (Python):", height=300)
                if st.button("Submit Code"):
                    # Call Orchestrator to evaluate
                    with st.spinner("Evaluating Code..."):
                        evaluation = st.session_state.orchestrator.submit_code(code)
                    
                    st.success("Code Evaluation Complete!")
                    st.write(evaluation)
                    
                    # Check if we should continue coding or finish
                    if not st.session_state.orchestrator.check_coding_status():
                        st.session_state.coding_mode = False
                        st.balloons()
                        st.success("Interview Completed! Thank you.")
                    else:
                        st.info("Please wait for the next coding question via voice or switch back to the Voice Tab.")
            else:
                st.write("No active coding challenge yet. Continue the voice interview.")

    else:
        st.info("Please upload a CV and click 'Start Interview' to begin.")

if __name__ == "__main__":
    main()
