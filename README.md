# ExpertBridge AI Recruiter 🤖🎤

**Version 3.0 (Refactored & Enriched)**

ExpertBridge is an advanced, voice-first AI interviewer designed to screen technical candidates. It uses a **Multi-Layered "Brain"** to generate context-aware questions based on the candidate's CV and the specific Job Description.

---

## 🌟 Key Features (v3.0)

### 1. 🧠 Smart "RAG" Brain
The AI doesn't just ask generic questions. It combines three layers of context:
*   **Persona**: A professional, probing interviewer personality.
*   **Strategy**: Analyzes the **Candidate's CV** to tailor questions (e.g., "Ask about your React experience").
*   **Domain Context**: Injects specific **Job Descriptions (JSON)** from the sidebar directly into the system prompt.

### 2. ⏱️ Robust Interview Timer
*   **Persistent Iframe**: A custom-built timer that won't reset or disappear during UI updates.
*   **Visual Cues**:
    *   **13 Minutes**: Turns **RED** with a "WRAP UP" warning.
    *   **15 Minutes**: Turns **RED** with "TIME UP".
    *   **Finished**: Turns **GREEN** when the interview ends.

### 3. 🛑 Smart Termination
The AI listens for "Closing Statements". If the interview naturally concludes (e.g., "Thank you, goodbye") after the final question, the system **automatically stops**, freezes the timer, and generates a score. No need to wait for the clock to run out.

### 4. 🗣️ Voice-First Interaction
*   **Listening**: Uses **Deepgram Nova-2** for lightning-fast transcription.
*   **Speaking**: Uses **Deepgram Aura** for human-like, low-latency voice output.

---

## 🛠️ System Architecture (Refactored)

The project is organized into a clean, modular structure:

```
AI_REBUILD/
├── src/
│   ├── core/
│   │   ├── orchestrator.py  # The "Manager" - coordinates I/O and logic
│   │   ├── brain.py        # The "Mind" - Prompt engineering & decision making
│   │   ├── listener.py     # Speech-to-Text (Deepgram)
│   │   └── speaker.py      # Text-to-Speech (Deepgram HTTP)
│   ├── ingestion/          # CV Parsing & Initial Q Generation
│   └── utils/
│       ├── timer.py        # Robust Iframe Timer Component
│       └── question_strategy.py # Dynamic strategy builder
├── documentation/          # Guides, Logs, and System Prompt Info
├── testing/                # Unit tests and debug scripts
├── output/                 # Extracted Job Descriptions (JSON)
├── main_app.py             # Streamlit Entry Point (UI)
└── .env                    # API Keys (Not committed)
```

---

## 🚀 Setup & Usage

### 1. Prerequisites
*   Python 3.9+
*   **API Keys**:
    *   Azure OpenAI (for Intelligence) - OR - Standard OpenAI
    *   Deepgram (for Voice)

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Configuration (.env)
Create a `.env` file in the root directory:
```env
# Intelligence
AZURE_OPENAI_API_KEY="your_key"
AZURE_OPENAI_ENDPOINT="your_endpoint"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"

# Voice
DEEPGRAM_API_KEY="your_deepgram_key"
```

### 4. Running the App
```bash
streamlit run main_app.py
```

---

## 🎮 How to Use

1.  **Select Job Role**: usage the Sidebar dropdown to pick a Job Context (e.g., "Senior Python Dev").
2.  **Fill Profile**: Enter your name/experience in the main form and click "Save".
3.  **Upload CV**: Upload your PDF resume in the sidebar.
4.  **Start**: Click "Start Interview".
5.  **Speak**: The AI will greet you. Reply verbally.
6.  **Finish**: The interview ends automatically after ~15 mins or when you say goodbye after the final question.

---

## 🧪 Testing & Verification

*   Run `python testing/test_context_injection.py` to verify the RAG prompt injection.
*   Run `python testing/verification_rebuild.py` for a full backend simulation.

---

**Built with Streamlit, Azure OpenAI, and Deepgram.**
