# ExpertBridge AI Interviewer - Detailed System Flow

This document provides a comprehensive, file-by-file breakdown of the **ExpertBridge AI Interviewer** system. It details how the application functions from the moment a user uploads a CV to the final scoring of the interview, highlighting the specific Large Language Models (LLMs) and services involved at each stage.

## 1. System Overview

The application is a **Voice-First AI Interviewer** built with **Streamlit**. It mimics a real-world technical interview by:
1.  **Parsing** a candidate's CV and understanding their background.
2.  **Generating** a personalized interview strategy based on experience level.
3.  **Conducting** a spoken interview using Speech-to-Text (STT) and Text-to-Speech (TTS).
4.  **Managing Time** strictly (15-minute hard stop) to simulate a real screening.
5.  **Evaluating** responses in real-time (architecturally ready) and providing a final score.

### Core Technologies
*   **Orchestration**: Python (Streamlit)
*   **Brain (LLM)**: Azure OpenAI (GPT-4 / GPT-4o-Audio)
*   **Ears (STT)**: Deepgram Nova-2
*   **Mouth (TTS)**: Deepgram Aura
*   **Memory**: GPTCache (with SQLite & Onnx) for semantic caching.

---

## 2. Detailed Flow: File by File

### A. Entry Point: `main_app.py`
**Role**: The Frontend & State Manager.

This file is the heart of the user experience. It handles the UI rendering, session state management (`st.session_state`), and the main event loop.

1.  **Initialization**:
    *   Sets up the Streamlit page config and sidebar.
    *   Initializes the `Orchestrator` class (see `src/core/orchestrator.py`), ensuring a singleton pattern via `st.session_state`.
    *   Loads environment variables and checks for critical API keys (`AZURE_OPENAI_API_KEY`, `DEEPGRAM_API_KEY`). If missing, halts execution.

2.  **Candidate Onboarding (Profile & CV)**:
    *   **Profile Form**: The user fills out details (Name, Role, Skills). These are stored in `st.session_state.expert_profile`.
    *   **CV Upload**: The user uploads a PDF using `st.file_uploader`.
    *   **Action**: Calls `src.ingestion.cv_parser.parse_cv()` to extract text from the PDF.
    *   **Trigger**: When "Start Interview" is clicked, it calls `orchestrator.start_interview()`.

3.  **The Interview Loop**:
    *   **Audio Input**: Uses `st.audio_input` to capture user speech. This widget returns a binary stream (WAV/WEBM).
    *   **Processing**: When audio is received, it calls `orchestrator.run_interview_turn()`.
    *   **Display**: Updates `chat_history` with the user's transcript and the AI's textual response.
    *   **Playback**: Automatically plays the generated audio (`ai_audio`) using `st.audio`.
    *   **Termination Check**: If `orchestrator.phase == "TERMINATED"`, it stops the loop and displays the final score.

4.  **Timers & UI**:
    *   Injects JavaScript for a live interview timer (counting up from start time).
    *   Displays a "Termination" screen if the interview ends (due to time limit or AI decision).
    *   **Debug Logs**: A hidden expander shows system logs (`st.session_state.debug_logs`) for troubleshooting LLM responses.

---

### B. Data Ingestion: `src/ingestion/cv_parser.py`
**Role**: The Raw Data Processor.

*   **Function**: `parse_cv(file)`
*   **LLM Usage**: **None**.
*   **Logic**:
    *   Uses the `pypdf` library to read the binary PDF stream.
    *   Iterates through pages and extracts raw text strings.
    *   Returns the consolidated text to `main_app.py`.
    *   **Why**: Fast, local extraction without API costs.

---

### C. The Strategist: `src/utils/question_strategy.py`
**Role**: The Personalization Engine.

*   **Function**: `build_question_strategy(expert_profile)`
*   **LLM Usage**: **None** (Rule-based Logic).
*   **Detailed Logic**:
    *   takes the structured `expert_profile` (Skills, Experience, Industry).
    *   Constructs a highly detailed **System Prompt Instruction** dynamically.
    *   **Seniority Rules**:
        *   **Senior (10+ years)**: Instructs AI to ask about Leadership ("Tell me about a time you managed a team"), Strategy, and Mentorship.
        *   **Mid-Level (5-10 years)**: Focuses on Execution Excellence and Cross-functional work.
        *   **Junior (0-5 years)**: Focuses on Learning Mindset ("What's the hardest skill you've learned?").
    *   **Skill-Specific Rules**:
        *   Iterates through user skills. If "Machine Learning" is found, adds: "Deep dive: Tell me about a time your ML model failed in production."
        *   If "M&A", adds: "Walk me through your most complex deal valuation."
    *   **Industry Context**:
        *   Adds specific context for industries like FinTech ("Ask about regulatory compliance"), SaaS ("Ask about churn"), etc.
    *   **Output**: A text block injected into the LLM's system prompt in `Brain.set_context`. This ensures the AI doesn't sound generic but rather like a seasoned expert in the candidate's field.

---

### D. The Conductor: `src/core/orchestrator.py`
**Role**: Logic Controller & Glue Code.

This class manages the flow of a single interview session. Note: It does **not** contain the AI logic itself; it delegates that to the `Brain`, `Listener`, and `Speaker`.

1.  **State Management**:
    *   Tracks `phase` (INTERVIEW vs TERMINATED).
    *   Tracks `question_count` and `max_questions`.
    *   Tracks `scores` (list of integers).
    *   **Time Management**:
        *   **13 Mins (780s)**: Injects a system warning to the Brain ("Time is almost up, ask one final question"). This forces the AI to wrap up gracefully.
        *   **15 Mins (900s)**: Hard terminates the session. It immediately calculates the final score and stops processing audio.

2.  **`run_interview_turn(audio_input)` Flow**:
    *   **Step 1 (Listen)**: Calls `self.listener.get_transcription()` to convert Audio -> Text.
        *   *Check*: If text is empty/silent, returns prompt ("I didn't hear anything") to speak again.
    *   **Step 2 (Think)**: Calls `self.brain.generate_response()` with the User Text.
        *   Passes `detected_language` to ensure the AI replies in the correct language.
        *   Passes `voice_model` setting.
        *   Receives `ai_text`, `score` (mocked), and `terminate` flag.
        *   *Score Aggregation*: If `score > 0`, appends to `self.scores`.
        *   *Termination Check*: If `terminate` is True, sets `self.phase = "TERMINATED"`.
    *   **Step 3 (Speak)**: Calls `self.speaker.text_to_speech()` with `ai_text`.
        *   Returns the path to the generated MP3 file.
    *   **Return**: Returns the tuple `(UserText, AiText, AudioPath, IsCodingMode)` to `main_app.py`.

---

### E. The Ears: `src/core/listener.py`
**Role**: Speech-to-Text (STT).

*   **Service**: **Deepgram**.
*   **Model**: `nova-2` (The fastest, most accurate STT model currently).
*   **LLM Usage**: Deepgram's proprietary STT models (Neural Networks, but not LLMs in the GPT sense).
*   **Logic**:
    *   Receives raw audio bytes.
    *   Sends to Deepgram API with `smart_format=True` (adds punctuation), `detect_language=True`.
    *   **Output**: Returns a dictionary `{ "text": "...", "lang": "en" }`. The "lang" detected here is crucial for the Brain to know how to reply (e.g., if user switched to Hindi).

---

### F. The Brain: `src/core/brain.py` (The Most Important File)
**Role**: The Intelligence (LLM), Memory, and Scorer.

This is where the actual "Thinking" happens. It encapsulates all interaction with Azure OpenAI.

1.  **Initialization (`__init__`)**:
    *   Connects to **Azure OpenAI Service**.
    *   Initializes **Semantic Cache** (`gptcache` + `ONNX` + `SQLite`). This checks if a user's question has been asked before to serve a cached response instantly, saving money and time. If FAISS/SQLite is unavailable, it gracefully degrades to no-cache mode.

2.  **Context Setup (`set_context`)**:
    *   **LLM Usage**: **GPT-4 / GPT-4 Turbo** (via Azure).
    *   **Input**: Candidate Name, CV Text, Job Description (optional), and the *Question Strategy* from step C.
    *   **Prompt Engineering**:
        *   Constructs a massive System Prompt defining the "Persona" (e.g., "Strict Technical Recruiter").
        *   Injects the custom Strategy block (e.g., "Ask about leadership...").
        *   Injects the CV summary.
        *   Sends the first "User Message" as a trigger: "Please start the interview."
    *   **Output**: The first question (e.g., "Hi [Name], tell me about yourself").

3.  **Generating Responses (`generate_response`)**:
    *   **LLM Usage**: **Azure OpenAI -> gpt-audio-AI-Assessment** (or GPT-4o).
    *   **Input**: User's transcribed text.
    *   **The Process**:
        1.  **Cache Check**: Computes embedding of user query (via ONNX). Checks SQLite. If high similarity match found (>0.9), return cached answer immediately.
        2.  **Language Enforcement**: Adds system instructions if the user is speaking a non-English language but English is required (or vice versa).
        3.  **LLM Call**: Calls `client.chat.completions.create()`.
            *   *Modality Handling*: If the model is an "Audio" model (GPT-4o-Audio), it requests `modalities=["text", "audio"]`. While we discard the native audio (preferring Deepgram for TTS), this mode is required for some Azure deployments.
            *   *Fallback*: If the primary model fails (e.g., Modality error), it retries with forced audio. If that fails, it falls back to text-only models like `gpt-4o` or `gpt-4`.
        4.  **Sanitization**: Calls `src.utils.sanitizer` to strip any markdown, JSON artifacts, or weird tokens.
        5.  **Scoring (Internal)**:
            *   Historically, the Brain was asked to return JSON `{ "text": "...", "score": 85, "terminate": false }`.
            *   **Current State**: Due to issues with LLMs occasionally outputting bad JSON, the system now enforces **Plain Text** for stability.
            *   *Code Reference*: `signal_score = 0 # Mocked`.
            *   *Note*: The infrastructure for scoring exists, but it's currently bypassed to ensure the interview doesn't crash on a JSON error.
    *   **Output**: The text response to be spoken.

4.  **Code Evaluation (`evaluate_code`)**:
    *   **LLM Usage**: **GPT-4 / GPT-3.5**.
    *   **Function**: A separate method to grade code snippets.
    *   **Prompt**: "Evaluate the following Python code... Correctness, Efficiency, Style."
    *   **Output**: A text summary of Pass/Fail.

---

### G. The Mouth: `src/core/speaker.py`
**Role**: Text-to-Speech (TTS).

*   **Service**: **Deepgram Aura**.
*   **Model**: `aura-asteria-en` (Human-like, low latency voice).
*   **LLM Usage**: Deepgram's Generative Audio models.
*   **Logic**:
    *   Takes the `ai_text` from the Brain.
    *   Sends strict text to Deepgram API.
    *   Streams the resulting audio chunks into an MP3 file (`output_tts.mp3`).
    *   **Features**: Capable of switching voices (Male/Female) based on user selection in the UI.

### H. Question Generator: `src/ingestion/question_gen.py`
**Role**: CV Analyzer.

*   **Function**: `generate_initial_questions(cv_text)`
*   **LLM Usage**: **Azure OpenAI GPT-4**.
*   **Logic**:
    *   Takes the raw CV text.
    *   Prompt: "Analyze the following CV and generate a list of 3-5 technical interview topics/questions."
    *   Output: A python list of strings. These can be used to prime the interview context if needed, though the `Brain.set_context` usually handles the live questioning.

---

## 3. Summary of Intelligence

| Component | Technology | Function |
| :--- | :--- | :--- |
| **CV Parser** | Python `pypdf` | Extract text from PDF (Deterministic) |
| **Strategy** | Python Logic | Create personalized prompt instructions (Deterministic) |
| **Hearing** | Deepgram `nova-2` | Transcribe User Audio -> Text (AI Model) |
| **Thinking** | **Azure OpenAI GPT-4o** | Understand context, generate questions, manage conversation (LLM) |
| **Speaking** | Deepgram `aura-asteria` | Generate Audio -> User (Generative Audio) |

## 4. Scoring Mechanism Detail

While the user requested a score, it is important to understand **how currently implemented**:

1.  **The Ideal Flow**: Use `response_format={"type": "json_object"}` in OpenAI to force the LLM to output `{ "score": 85 }` with every answer.
2.  **The Constraint**: Streamlit and the strict "Recruiter Persona" requires very natural, conversational text. Mixing JSON and Conversation often leads to hallucinations or "I cannot answer in JSON" errors from stricter models.
3.  **The Solution (v2.2)**: `Brain.py` currently focuses on **Conversation Stability**.
    *   The `signal_score` is hardcoded to `0` in the loop.
    *   `Orchestrator` typically calculates the *Average* of these scores.
    *   **Result**: The user gets a smooth interview, but the final score might show `0/100` unless the `evaluate_code` module is triggered explicitly (which returns a separate rating).

This architecture separates the **Conversation** from the **Meta-Data**, allowing us to swap out the Brain model (e.g., to a cheaper/faster one) without breaking the audio pipeline.

## 5. Deployment Considerations

The system handles failures gracefully across the stack:
*   **API Limits**: Check `__init__.py` for API Key validation.
*   **Audio Failures**: Fallback to text if TTS fails.
*   **Model Failures**: Fallback chain (GPT-4o-Audio -> GPT-4o -> GPT-4 -> GPT-3.5) inside `Brain._safe_completion()`.
*   **Web Latency**: The `Listener` and `Speaker` APIs operate in near real-time, but network latency can affect perceived speed. The `stream=False` flag is currently used for simplicity, but future versions could use streaming.

## 6. Glossary & Key Concepts

*   **Orchestrator**: The central controller pattern used in this app. It manages state but delegates intelligence.
*   **LLM (Large Language Model)**: The "Brain" (GPT-4) that generates text.
*   **STT (Speech-to-Text)**: Converting audio to text. We use Deepgram Nova-2.
*   **TTS (Text-to-Speech)**: Converting text to audio. We use Deepgram Aura.
*   **Semantic Caching**: Using vector embeddings (lists of numbers representing meaning) to find if a question is "similar enough" to a previous one to reuse the answer, rather than just checking if the text strings are identical.

## 7. Testing & Verification

To verify the flow works as intended:
1.  **Unit Tests**: Check `src/core/test_brain.py` (if available) to mock `AzureOpenAI` responses.
2.  **Manual Verification**:
    *   Upload a dummy PDF.
    *   Fill out the profile.
    *   Speak clearly into the microphone.
    *   Confirm the Timer starts and audio plays back.
3.  **Silence Test**: Record silence for 5 seconds. The system should return "I didn't hear anything" without crashing, handled by `Listener.get_transcription`.

## 8. Future Roadmap

Potential enhancements identified in the codebase:
1.  **Re-enable Scoring**: Use a secondary, parallel LLM call *just* for scoring (Scorekeeper Agent) to avoid polluting the main conversation.
2.  **Multilingual TTS**: Fully implement voice switching based on detected language (e.g., switching to `aura-hindi` if available).
3.  **Video Analysis**: Integrate webcam stream for non-verbal cues (posture, eye contact).
4.  **WebSocket Streaming**: Switch from REST API to WebSockets for sub-second latency.
