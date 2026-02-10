# ExpertBridge AI Interviewer 🤖

ExpertBridge is an advanced AI-powered technical interviewer designed to conduct realistic, voice-based interviews. It analyzes a candidate's CV, generates relevant questions, listens to spoken answers, and provides a coding challenge if needed.

## 🌟 Features
- **Voice-First Interface**: Candidates speak naturally; the AI listens and responds with a human-like voice.
- **Smart CV Analysis**: Extracts key skills from a PDF resume to tailor the interview.
- **Structured Phases**:
  1.  **Theory Phase**: 5 conceptual questions to test depth of knowledge.
  2.  **Coding Phase**: Triggered after theory, asks the candidate to write code.
- **Real-time Feedback**: Evaluates code submissions for correctness and efficiency.

---

## 🛠️ System Architecture

The system mimics a human interviewer's brain using three core "organs":

### **1. Language Model (LLM)**
*   **Provider**: **Azure OpenAI**
*   **Model**: `gpt-4o` (via `gpt-audio-AI-Assessment` deployment)
*   **Role**:
    *   **Phase 1 (Setup)**: Analyzes CV to generate topics.
    *   **Phase 2 (Theory)**: Generates the next question and conversationally responds to the candidate.
    *   **Phase 3 (Coding)**: Evaluates the Python code submitted by the user.

### **2. Speech-to-Text (Transcriber)**
*   **Provider**: **Deepgram**
*   **Model**: `nova-2`
*   **Role**: real-time transcription of the user's voice answers.

### **3. Text-to-Speech (TTS)**
*   **Provider**: **Deepgram**
*   **Model**: `aura-asteria-en`
*   **Role**: Generates the audio for the AI interviewer's voice.

### **4. UI Framework**
*   **Library**: **Streamlit**
*   **Role**: Provides the web interface, audio recorder widget, and coding text editor.

---

## 🚀 Deployment Instructions

### 1. GitHub Setup
Push **only** the files listed above. The `.gitignore` file included in this repo will automatically prevent you from pushing unnecessary files like `__pycache__`, `*.wav`, or your secret `.env` file. Ensure `packages.txt` is also pushed if you added system dependencies (it can be empty).

### 2. Streamlit Cloud Deployment
1.  Push this repository to GitHub.
2.  Go to [share.streamlit.io](https://share.streamlit.io/).
3.  Connect your GitHub account and select this repository.
4.  Set the **Main file path** to `main_app.py`.
5.  **Crucial**: In "Advanced Settings" -> "Secrets", add your API keys:
    ```toml
    AZURE_OPENAI_API_KEY = "your_azure_key"
    AZURE_OPENAI_ENDPOINT = "https://expertbridge-foundry.openai.azure.com/"
    AZURE_OPENAI_DEPLOYMENT_NAME = "gpt-audio-AI-Assessment"
    DEEPGRAM_API_KEY = "your_deepgram_key"
    ```
6.  Click **Deploy**.

---

## 💻 Local Execution
To run locally:
1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Setup Keys**:
    Create a `.env` file with:
    ```env
    AZURE_OPENAI_API_KEY=your_key
    AZURE_OPENAI_ENDPOINT=https://expertbridge-foundry.openai.azure.com/
    AZURE_OPENAI_DEPLOYMENT_NAME=gpt-audio-AI-Assessment
    DEEPGRAM_API_KEY=your_deepgram_key
    ```
3.  **Run App**:
    ```bash
    streamlit run main_app.py
    ```

---

## 🧠 System Prompts & Logic

### **Interviewer Persona (`INTERVIEWER_SYSTEM_PROMPT`)**
The AI is instructed to:
1.  Be professional but encouraging.
2.  Ask **ONE** question at a time.
3.  **NEVER** autocomplete or hallucinate the user's response.
4.  Switch to `[CODING]` mode when instructed.

### **Phasewise Logic**
1.  **Theory Phase**:
    *   The `Orchestrator` counts every question asked.
    *   After **5 questions**, it injects a "System Message" telling the brain: *"THEORY Phase complete. Switch to CODING phase now."*
2.  **Coding Phase**:
    *   The AI asks a coding problem.
    *   The User switches to the "Coding Challenge" tab.
    *   The User writes code and clicks "Submit".
    *   The `submit_code` function sends the code to **Azure OpenAI** for evaluation (Pass/Fail + Feedback).
    *   After **2 questions**, the interview concludes.
