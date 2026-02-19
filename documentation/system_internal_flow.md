# System Internal Flow & Intelligence Architecture 🧠

This document details the end-to-end flow of the **ExpertBridge AI Interviewer (v3.0)**, explaining how data moves, how the RAG (Retrieval-Augmented Generation) system works, and the core logic behind the "Crucible Protocol" scoring.

---

## 1. End-to-End System Flow 🌊

### **Phase 1: Ingestion & Setup**
1.  **Job Selection**: User selects a "Job Context" (JSON) from the Sidebar (e.g., *Senior Python Developer*).
    *   *System Action*: `main_app.py` loads this JSON and passes it to `Orchestrator`.
2.  **Profile Creation**: User fills out manual details (Name, Experience).
    *   *System Action*: Saved to `st.session_state.expert_profile`.
3.  **CV Upload**: User uploads a PDF Resume.
    *   *System Action*: `src.ingestion.cv_parser.parse_cv()` extracts raw text.
    *   *System Action*: `Orchestrator` initializes `Brain` with `expert_profile` and `job_context`.

### **Phase 2: The Interview Loop (Real-Time)**
The interview runs in a loop triggered by the **Audio Input** widget (`main_app.py`).

1.  **Audio Capture**: User speaks into the microphone.
2.  **Transcription (Ear)**:
    *   `Listener.get_transcription()` sends audio bytes to **Deepgram Nova-2**.
    *   Returns text (e.g., *"I used AWS Lambda for that project."*).
3.  **Intelligence Processing (Brain)**:
    *   `Orchestrator` calls `Brain.handle_user_input(text, elapsed_time)`.
    *   **Step A (Safety)**: Checks for abuse keywords.
    *   **Step B (Time Check)**:
        *   If > 13 mins: Injects **"Final Question"** instruction.
        *   If "Closing Statement" detected: Sets `terminate=True`.
    *   **Step C (Response Generation)**:
        *   Constructs prompt (See Section 2).
        *   Calls **Azure OpenAI (GPT-4o)** to generate a spoken reply.
    *   **Step D (Scoring)**:
        *   Calls `analyze_answer()` (See Section 3) in parallel.
4.  **Speech Synthesis (Voice)**:
    *   `Speaker.text_to_speech()` sends the AI's text to **Deepgram Aura**.
    *   Returns audio bytes.
5.  **Output**:
    *   `main_app.py` plays the audio and updates the chat history.

### **Phase 3: Termination & Reporting**
1.  **Termination**: Triggered by Time Limit (15m) or Natural Conclusion.
2.  **Final Scoring**:
    *   `Orchestrator` calculates the average of all per-turn scores.
3.  **Feedback**:
    *   UI displays the Final Score (0-100) and a Pass/Fail status.

---

## 2. RAG & Prompt Injection (The "Brain") 🧩

The "Intelligence" comes from injecting specific data into the **System Prompt** of the LLM. This is how the AI "knows" what to ask.

### **Data Source 1: The Persona (Static)**
*   **Source**: `Brain._get_static_system_prompt()`
*   **Content**: "You are a professional expert interviewer... The Crucible Protocol... Ask one question at a time."

### **Data Source 2: The Candidate Strategy (Dynamic)**
*   **Source**: `src.utils.question_strategy.build_question_strategy(expert_profile)`
*   **Injection**:
    ```text
    [EXPERT PROFILE & STRATEGY]
    - Candidate: John Doe, 10 years experience.
    - Key Project: "Payment Engine".
    - Focus Areas: Ask about Scalability and Transaction Safety.
    ```

### **Data Source 3: The Job Context (Dynamic)**
*   **Source**: Selected JSON from Sidebar (e.g., `output/senior_python.json`).
*   **Injection**:
    ```text
    [DOMAIN KNOWLEDGE / JOB CONTEXT]
    Use this context to ask specific, grounded questions:
    {
      "role": "Senior Python Developer",
      "required_skills": ["Django", "AWS", "PostgreSQL"],
      "culture_fit": "Biased for Action"
    }
    ```

**Result**: The LLM receives a massive, context-rich prompt combining *Who it is* (Persona), *Who it's talking to* (Strategy), and *What it's hiring for* (Job Context).

---

## 3. Scoring Logic (The "Crucible" Engine) ⚖️

The system evaluates **every single answer** individually using a dedicated "Analysis Prompt".

### **A. Core Logic: Bayesian Signal Detection**
Instead of just checking keywords, the AI looks for **High-Signal Evidence**:

| Signal Type | Description | Impact on Score |
| :--- | :--- | :--- |
| **Information Density** | Specific metrics (*"Reduced latency by 20ms"*), named tools (*"Redis Cluster"*), constraints (*"Memory limited to 512MB"*). | 🔼 High Boost |
| **Decision Maturity** | Explaining **Trade-offs** (*"We chose SQL over NoSQL because..."*) rather than just choices. | 🔼 High Boost |
| **Confidence** | Admitting unknowns (*"I haven't used K8s explicitly"*) vs. faking it. | 🔼 Boost (Integrity) |
| **Fluff / Buzzwords** | Generic phrases (*"I'm a team player"*, *"I used AI"*). | 🔽 Penalty |

### **B. Scoring Dimensions (1-5)**

1.  **Depth (Knowledge)**:
    *   **5/5**: Multiple concrete examples, deep technical details, handles complexity.
    *   **1/5**: Vague, theoretical, no evidence.
2.  **Thinking (Structure)**:
    *   **5/5**: Clear STAR method, logical flow, explains "Why".
    *   **1/5**: Scattered, incoherent.
3.  **Fit (Communication)**:
    *   **5/5**: Concise, professional, confident.
    *   **1/5**: Rude, hesitant, confusing.

### **C. The Overall Score Equation**
The model outputs a raw `overall_score` (0-100) for each turn.
*   **Final Interview Score** = Average of all `overall_score` values across the session.

### **D. Red Flag Detection**
The system actively scans for:
*   **Evasion**: answering a different question.
*   **Contradictions**: conflicting details compared to previous answers.
*   **Defensiveness**: reacting poorly to probing questions.

---
**Summary**: The system is a **Voice-First RAG Pipeline** that uses prompt injection to contextualize the AI, and a separate parallel scoring agent to grade "Information Density" in real-time.
