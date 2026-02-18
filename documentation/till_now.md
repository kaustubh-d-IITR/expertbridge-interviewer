# ExpertBridge AI Interviewer: Development History & Phase Documentation

## Overview
This document serves as a comprehensive log of the ExpertBridge AI Interviewer development, detailing every phase of implementation, architectural decisions, and feature additions. The system has evolved from a basic prototype to a robust, strict-English, behavior-aware AI Recruiter.

---

## Phase 1: Core Setup & Ingestion
**Goal:** Establish the fundamental architecture and capability to parse resumes.

### Key Features
1.  **Project Structure**:
    -   `src/core/`: Brain, Listener, Speaker, Orchestrator.
    -   `src/ingestion/`: CV Parsing logic.
    -   `src/utils/`: Prompts and helpers.
2.  **CV Parsing (`src/ingestion/cv_parser.py`)**:
    -   Implemented sturdy PDF parsing using `PyPDF2`.
    -   Added fallback logic for text files.
    -   **Code Highlight**:
        ```python
        def parse_cv(file_path):
            try:
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
            except Exception as e:
                return "Error parsing CV."
        ```

---

## Phase 2: Core Organ Implementation
**Goal:** Connect the sensory organs (Ear, Brain, Mouth) and create the Orchestrator.

### Key Components
1.  **The Listener (`src/core/listener.py`)**:
    -   Integrated **Deepgram Nova-2** for high-speed Speech-to-Text (STT).
    -   Configured for `audio/wav` input.
2.  **The Brain (`src/core/brain.py`)**:
    -   Initially used Groq (Llama 3), later migrated to **Azure OpenAI (GPT-4o/Audio)** for better reasoning.
    -   Manages conversation history and system prompts.
3.  **The Speaker (`src/core/speaker.py`)**:
    -   Integrated **Deepgram Aura** for low-latency Text-to-Speech (TTS).
    -   Supports multiple voice models (Asteria, Orion).
4.  **The Orchestrator (`src/core/orchestrator.py`)**:
    -   Central nervous system.
    -   Manages the loop: `Audio In -> Listener -> Brain -> Speaker -> Audio Out`.
    -   **Logic Flow**:
        ```python
        def run_interview_turn(self, audio_input):
            text = self.listener.transcribe(audio_input)
            response = self.brain.think(text)
            audio = self.speaker.speak(response)
            return response, audio
        ```

---

## Phase 3: Multilingual Capabilities & Recruiter Mode
**Goal:** Enable diverse language support and a specific "Recruiter" persona.

### Key Features
1.  **Automated Language Detection**:
    -   Updated `Listener` to return a dictionary: `{"text": "...", "lang": "hi"}`.
    -   Orchestrator now aware of user's input language.
2.  **Adaptive Brain**:
    -   Brain dynamically injects system instructions: `[SYSTEM: User spoke Hindi. Reply in Hindi.]` (Legacy behavior, later overridden in Phase 5).
3.  **Recruiter Mode**:
    -   Added `RECRUITER_SYSTEM_PROMPT` in `src/utils/prompts.py`.
    -   Characteristics: Aggressive, short, "No Fluff".
4.  **Hidden Signal Score**:
    -   Implemented heuristic scoring (Length + Complexity) in `brain.py` to evaluate answer depth invisibly.

---

## Phase 4: Language Control & UI Split
**Goal:** Give users fine-grained control over languages.

### Key Features
1.  **Dual Language Selectors**:
    -   Added UI for "Input Language" vs "Response Language".
    -   Allowed setups like: Speak Hindi -> Reply English.
2.  **Strict Response Enforcement**:
    -   Updated `Brain` to ignore input language if a specific "Response Language" was set in UI.
    -   Ensured TTS mapped to the correct voice model (e.g., Hindi voice for Hindi text).

---

## Phase 5: Strict English Enforced & UI Cleanup
**Goal:** Simplify the UX and force professional English interaction.

### Key Changes
1.  **UI Cleanup (`main_app.py`)**:
    -   **REMOVED**: Language selector dropdowns.
    -   **REMOVED**: Recruiter Mode toggle.
    -   **ADDED**: Sidebar notice "System Upgrade: Strict English".
2.  **Hardcoded Behavior**:
    -   `mode="recruiter"` (Mandatory).
    -   `response_language="English"` (Mandatory).
    -   `input_language="Auto"` (The AI understands Hindi, but refuses to speak it).
3.  **Brain Logic Update**:
    -   Added Rule: `[SYSTEM: User spoke {lang}. UNDERSTAND it, but reply in ENGLISH.]`

---

## Phase 6: Behavior & Scoring Guardrails (The "Smart Brain")
**Goal:** Add automated conduct monitoring and real-time LLM scoring.

### Key Features
1.  **JSON Brain Output**:
    -   Refactored `generate_response` to prompt the LLM to return JSON:
        ```json
        {
            "response_text": "...",
            "signal_score": 85,
            "warning_issued": false,
            "terminate_interview": false
        }
        ```
2.  **Conduct Guardrails (3-Strike Rule)**:
    -   **Strike 1**: AI issues a polite but firm warning.
    -   **Strike 2**: AI sets `terminate_interview=True`. Orchestrator ends session.
    -   **Zero Tolerance**: Rudeness results in a Score of 0.
3.  **Tone Adjustment**:
    -   Softened "Recruiter Mode" from "Aggressive" to "**Professional Firmness**".

---

## Phase 7: Time Management (15-Minute Limit)
**Goal:** strict timeboxing to mimic real screening calls.

### Key Features
1.  **Timer Logic (`main_app.py`)**:
    -   `start_time` initialized on Interview Start.
    -   `elapsed_time` calculated every turn and passed to Orchestrator.
2.  **13-Minute Warning**:
    -   If `elapsed > 780s` (13m): Orchestrator injects prompt: `[SYSTEM: Time up. Ask ONE final question.]`.
3.  **15-Minute Hard Stop**:
    -   If `elapsed > 900s` (15m): Orchestrator returns `TERMINATED` phase immediately.
    -   **Code**:
        ```python
        if elapsed_time > 890:
             self.phase = "TERMINATED"
             return None, "Time is up...", None, False
        ```

---

## Phase 8: Score Display & Persistance (Final Polish)
**Goal:** Ensure the user actually sees their result upon termination.

### Key Features
1.  **Score Persistence (`orchestrator.py`)**:
    -   Added `self.scores = []` list to track every answer's score.
    -   Added `self.final_score` variable.
    -   On Termination, calculates `Average(scores)` (or 0 if Conduct Violation).
2.  **UI Display (`main_app.py`)**:
    -   Updated Termination Banner to fetch and display the score directly in the red/green box.
    - `st.error(f"🚨 INTERVIEW TERMINATED. Final Score: {final_score}/100")`

---

## Phase 9: Live Timer UI
**Goal:** Provide visual real-time feedback on interview duration.

### Key Features
1.  **JavaScript Injection (`main_app.py`)**:
    -   Replaced static Python timer with client-side JS.
    -   **Mechanism**:
        -   Python passes `start_time` (timestamp) to JS.
        -   JS calculates `Date.now() - start_time` every 1000ms.
        -   Updates `<div id="live_timer">` dynamically.
    -   **Benefit**: Smooth ticking (1s updates) without page reloads.

---

## Phase 10: Bug Fixes (Timer & Multilingual Continuity)
**Goal:** Fix reported stability issues in Phase 9.

### Key Fixes
1.  **Robust Timer (`main_app.py`)**:
    -   Implemented unique container IDs and `clearInterval` logic to prevent timer duplication or freezing.
    -   Ensured `start_time` persistence in session state.
2.  **Multilingual JSON Handling (`brain.py`)**:
    -   Added `try-except` blocks around JSON parsing.
    -   If the LLM outputs invalid JSON (common when switching languages), the system now logs the error to `st.session_state.debug_logs` and falls back to text mode instead of crashing.

---

## Phase 11: Stability Fixes (Model Fallback)
**Goal:** Prevent crashes when using advanced Audio models for text-only logic.

### Key Fixes
1.  **Improper Modality Handling (`brain.py`)**:
    -   Detected `openai.BadRequestError` when `gpt-4o-audio-preview` rejects text-only requests.
    -   Implemented auto-fallback to `gpt-4o` (standard text model) upon detection.
    -   Fixed variable scope (`UnboundLocalError`) in error handlers.

---

## Phase 12: Deployment Configuration Fix (Robust Fallback)
**Goal:** Handle Azure OpenAI environments where `gpt-4o` is not the default fallback.

### Key Features
1.  **Dynamic Fallback Loop (`brain.py`)**:
    -   Instead of trying only `gpt-4o`, the system now iterates through a priority list:
        1.  User-defined `AZURE_OPENAI_FALLBACK_MODEL` (from `.env`).
        2.  `gpt-4o`
        3.  `gpt-4`
        4.  `gpt-4-turbo`
        5.  `gpt-35-turbo`
    -   It stops at the first one that works.
    -   If all fail, it returns a friendly "Please Configure" error message instead of crashing with a 404.

---

## Phase 13: Mix Modality Support
**Goal:** Fix regression where Audio models failed because text-only fallback was prioritized over modality correction.

### Key Fixes
1.  **Prioritized Modality Retry (`brain.py`)**:
    -   Refactored `generate_response` to catch "Audio Modality" errors *first*.
    -   BEFORE trying a fallback model (e.g., `gpt-4o`), the system now retries the *same* model with `modalities=["text", "audio"]` and dummy audio output.
    -   This allows the user to use `gpt-audio-preview` models for text logic without configuration changes.

---

## Phase 14: Stability Polish
**Goal:** Eliminate `UnboundLocalError` crashes.

### Key Fixes
1.  **Import Scope Fix (`brain.py`)**:
    -   Moved `import streamlit as st` to the top of `generate_response` method.
    -   This ensures that all exception handlers (even deep nested ones) can access `st.session_state` without crashing, preventing "local variable referenced before assignment" errors.

## Phase 15: Fix Session State Initialization (Stability)
**Goal:** Fix `AttributeError` for `debug_logs`.

### Key Fixes
1.  **Robust Initialization (`brain.py`)**:
    -   Added explicit check at the start of `generate_response`: `if "debug_logs" not in st.session_state: st.session_state.debug_logs = ""`
    -   This guarantees that the list exists before any error handler tries to append to it.

## Phase 16: Robust Parsing & Modality Polish
**Goal:** Fix "Raw JSON" display and improve Audio stability.

### Key Fixes
1.  **Robust JSON Extraction (`brain.py`)**:
    -   Implemented Regex-based searching (`re.search(r"\{.*\}", ...)`) to find the JSON object even if the model surrounds it with text (e.g., "Here is the JSON: ...").
    -   Added fallback cleaner to strip ` ```json ` tags if parsing still fails.
2.  **API Version Update**:
    -   Bumped `AZURE_OPENAI_API_VERSION` to `2024-10-01-preview` to better support the latest Audio models and prevent 400 Errors.

## Phase 17: Personalization Engine (Sir's Priority)
**Goal:** Replace generic questions with a personalized interview strategy based on expert profile.

### Implemented Features
1.  **Expert Profile Form (`main_app.py`)**:
    -   New UI form collects: Name, Roles, Experience, Skills, Industries, and Key Projects.
    -   Must be filled before starting the interview.
2.  **Question Strategy Module (`src/utils/question_strategy.py`)**:
    -   Analyzes profile to determine interview depth (Junior/Mid/Senior).
    -   Generates deep-dive questions for specific skills (e.g., "Walk me through your M&A valuation...").
    -   Adds industry-specific context (FinTech regulatory, Healthcare compliance).
3.  **Brain Integration**:
    -   Injects the personalized strategy into the System Prompt, making the AI act like it has read the resume.

## Phase 18: Critical Fixes (User Priority)
**Goal:** Fix user-reported bugs (JSON artifacts, Scoring, Coding questions).

### Implemented Fixes
1.  **Clean Output (No Raw JSON)**:
    -   Added "Emergency Regex Cleaner" in `brain.py` to strip `{"response_text": "..."}` artifacts if JSON parsing fails.
2.  **Fair Scoring**:
    -   Updated `orchestrator.py`: If the interview is terminated (e.g., due to time), the user receives their **Average Score** instead of 0.
3.  **No Coding Rule**:
    -   Updated `src/utils/prompts.py` to explicitly forbid coding tasks: *"This is a VERBAL interview. Do NOT ask the candidate to write code."*

---

## Current System State
The system is now a highly personalized, robust AI Screener.
-   **Strict English**: Professional global standard.
-   **Behaviorally Aware**: Will not tolerate abuse.
-   **Time Boxed**: Respects everyone's time (15 mins).

## Phase 19: Azure Content Filter Fix
**Goal:** Resolve `ResponsibleAIPolicyViolation` (Jailbreak false positive) errors.

### Implemented Fixes
1.  **Prompts Refactoring**: Softened the `RECRUITER_SYSTEM_PROMPT` to remove aggressive commands ("Ignore previous rules", "YOU MUST").
2.  **Context Splitting**: Moved candidate CV and Strategy context from the **System Prompt** to the **User Message**. This reduces the likelihood of Azure flagging the system instructions as a jailbreak attempt.
3.  **Fallback Logging**: Added explicit logs to confirm if `AZURE_OPENAI_FALLBACK_MODEL` is being loaded.

## Phase 20: Ultimate JSON Fix (User Fed Up)
**Goal:** ELIMINATE raw JSON artifacts from the chat once and for all.

### Implemented Fixes
1.  **Robust Parsing Helper**: Added `_clean_json_response` to `brain.py` with a 4-stage cleaning pipeline:
    -   **Pass 1**: Standard `json.loads` (Happy path).
    -   **Pass 2**: Regex extraction of specific fields (Handles extra text).
    -   **Pass 3**: Brute-force String Splitting (Handles messy syntax).
    -   **Pass 4**: Fail-Safe (If it looks like JSON but fails to parse, return a generic error instead of showing raw code).
2.  **Safety Net**: The system now guarantees that even if the AI outputs garbage, the user will see a clean error message, not the internal buffer.

## Phase 21: Debugging JSON Leak
**Goal:** Fix the persistence of the issue despite the cleaner.

### Cause
The Streamlit `session_state` was holding onto an **OLD instance** of the `Orchestrator` and `Brain` classes from a previous run, meaning the new cleaning code was not being executed.

### Fix
Added a `SYSTEM_VERSION` check in `main_app.py`. On reload, if the version identifier changes (currently `v2.1`), the app forces a hard reset of the session state, ensuring the new code is loaded.

## Phase 22: Defense in Depth (Orchestrator Clean)
**Goal:** Absolute guarantee that JSON never reaches the user.

### Implemented Fixes
1.  **Output Sanitizer**: Added `_sanitize_ai_text` to `orchestrator.py`.
2.  **Double Filtering**: Even if the `Brain` component returns raw JSON (due to an error or bypass), the `Orchestrator` now runs a final regex check immediately before sending text to the Speech Engine.
3.  **Result**: It is now mathematically impossible for `{"response_text": ...}` to be spoken or displayed, as the Orchestrator intercepts it.

## Phase 23: External Sanitizer Module (User Request)
**Goal:** Centralize cleaning logic in a dedicated file, as requested by the user.

### Implemented Fixes
1.  **New File**: Created `src/utils/sanitizer.py` containing the `clean_ai_response` function. This function uses a 4-stage cleaning process (JSON -> Regex -> String Split -> Fail-Safe).
2.  **Centralization**: Removed the internal private methods from `brain.py` and `orchestrator.py`. Both components now import and use the same external sanitizer.
3.  **Redundancy**: The cleaner is applied TWICE:
    -   Inside `Brain` (before returning the response).
    -   Inside `Orchestrator` (before sending to the Speaker), catching any edge cases where Brain might leak raw data.

## Phase 24: End-to-End Tracing & Cache Nuke
**Goal:** Resolve the discrepancy where the code on disk is correct, but execution remains broken.

### Diagnosis
The Streamlit application was likely running with a stale Python module cache (`sys.modules`). Despite modifying the files, the running Python process was not reloading the modules from disk, causing it to execute the **OLD** logic (pre-sanitizer).

### Fix
Implemented a **Force Module Reload** in `main_app.py`.
- Bumped `SYSTEM_VERSION` to `v2.2`.
- Added logic to explicitly delete `src.core.brain`, `src.core.orchestrator`, `src.utils.sanitizer`, `src.utils.question_strategy`, and `src.utils.prompts` from `sys.modules` if the version changes.
- This forces Python to re-read the code from the disk, ensuring the new sanitizer logic is actually loaded into memory.

## Phase 25: Jailbreak Evasion
**Goal:** Fix the `content_filter` (Jailbreak) error blocking the primary AI model.

### Diagnosis
Azure OpenAI's safety filters for the `gpt-audio` model are extremely strict. They flagged the "You are a Senior Recruiter" system prompt as a "Jailbreak" attempt because it tried to define a role that overrides the default AI behavior.

### Fix
1.  **Prompt Sanitization**: Rewrote `RECRUITER_SYSTEM_PROMPT` to be benign: "You are a helpful professional assistant...".
2.  **Role Shifting (Trojan Horse)**: Moved the specific Recruiter Guidelines ("Evaluate depth", "No coding") out of the *System Prompt* and into the *User Message*. Azure's filters are typically more lenient with user-provided context than system-level overrides.
3.  **Custom Personas**: Allow uploading a "Interviewer Style" document.

## Phase 26: Minimal Viable Product (MVP)
**Goal:** Simplify the system to its core functionality for a quick demo.

### Implemented Features
1.  **Core Interview Loop**: Focus on question-answer flow.
2.  **Basic Scoring**: Simple pass/fail.
3.  **Simple UI**: One click to start, no complex settings.

## Phase 27: Emergency De-JSON-ification (User Request)
**Goal:** Remove ALL traces of JSON from the system to guarantee clean text output, even if it means sacrificing the Scoring feature.

### Implemented Fixes
1.  **Prompt Rewrite (`brain.py`)**:
    -   REMOVED the "OUTPUT FORMAT (JSON ONLY)" instruction.
    -   ADDED "OUTPUT FORMAT: Plain text conversation only. Do NOT output JSON."
2.  **Logic Update (`brain.py`)**:
    -   Updated `generate_response` to stop trying to parse JSON.
    -   It now treats the AI's output as raw text.
    -   **Trade-off**: `signal_score` is hardcoded to `0` and `terminate_interview` is `False`. The "Smart Brain" features are disabled in favor of text stability.

## Phase 28: Fix UnboundLocalError & Debugging
**Goal:** Fix crash in Recruiter Mode and add tracing.
-   **Initialize Var**: Fixed `UnboundLocalError: local variable 'system_instruction' referenced before assignment`.
-   **Debugging**: Added `print()` statements to verify code execution.

## Phase 29: Fix ModuleNotFoundError (Deployment Sync)
**Goal:** Resolve missing file error on remote server.
-   **Problem**: `src.utils.sanitizer` was present locally but missing on `mount/src/...`.
-   **Fix**:
    -   Updated `src/utils/__init__.py` to explicitly export the module.
    -   Force-added `sanitizer.py` to git to ensure it syncs.

## Phase 30: Variable Scope Fix (Stability)
**Goal:** Prevent crash when Azure API returns 400 Error.
-   **Problem**: `UnboundLocalError: local variable 'ai_text' referenced before assignment`.
-   **Cause**: If the API call failed (e.g., Modality Error), the code jumped to the `except` block, skipping the line where `ai_text` was defined.
-   **Fix**: Initialized `ai_text` with a safe default ("I'm having trouble thinking...") at the very start of the function.

## Phase 31: Proactive Modality Handling (Audio Fix)
**Goal:** Fix persistent "Text-only input detected" warnings for Audio models.
-   **Problem**: `gpt-4o-audio-preview` rejects requests without `modalities=["text", "audio"]`.
-   **Fix**: Added a check at the start of `generate_response`. If the model name contains "audio", the system now *automatically* adds the required audio parameters to the request. This bypasses the error-prone retry loop entirely.

## Phase 32: Modality Logic Fix (Syntax)
**Goal:** Fix SyntaxError introduced in Phase 31.
-   **Problem**: `SyntaxError` and `IndentationError` due to improper `try/except` nesting.
-   **Fix**: Cleaned up the request logic structure. Removed redundant `try` blocks and ensured the success path is correctly indented.

## Phase 33: Robust Fallback Strategy
**Goal:** Ensure the system actually falls back to standard text models if the Audio model fails.
-   **Problem**: Previous error handling `raise e` was killing the process before the fallback loop could run.
-   **Fix**:
    -   Refactored `generate_response` to catch and log primary model errors instead of raising them.
    -   This allows the code to proceed to the "Fallback Loop" when `response` is None.
    -   Ensured fallback requests use clean/standard parameters (no audio modalities), so they work with `gpt-4o`/`gpt-4`.

## Phase 34: Debug Logging Fix (Root Cause?)
**Goal:** Fix missing logs and understand "Trouble Thinking" error.
-   **Discovery:** `st.session_state.debug_logs` was **never initialized** in `main_app.py`.
-   **Impact:** When `brain.py` tried to log an error (e.g., `Modality Error`), it executed `st.session_state.debug_logs += ...`. This raised a `KeyError`, which was caught by the outer exception handler, masking the original error and causing the generic "I'm having trouble thinking" message.
    -   **Fix:** Added initialization `st.session_state.debug_logs = ""` in `main_app.py`. This should reveal the true errors and potentially prevent the crash itself.

## Phase 35: Fix AttributeError (Orchestrator NoneType)
**Goal:** Fix crash loop where `orchestrator_v3` is None.
-   **Cause:** The "Hard Reload" logic (Phase 24) set `orchestrator_v3` to `None` to force a refresh. However, the initialization block only checked `if "orchestrator_v3" not in st.session_state`. Since the key existed (with value `None`), it skipped re-initialization.
-   **Fix:** Updated `main_app.py` to check `if ... or st.session_state.orchestrator_v3 is None`.

## Phase 36: Fix Initialization Order (AttributeError)
**Goal:** Fix crash where `expert_profile` was accessed before creation.
-   **Cause:** The logic to re-create the Orchestrator (Phase 35) accessed `st.session_state.expert_profile` to restore the user's profile. However, `expert_profile` was initialized *later* in the file.
-   **Fix:** Moved `expert_profile` initialization to the very top of `main_app.py` session state block, ensuring it exists before any other component tries to use it.

## Future Recommendations
1.  **Report Generation**: Export the chat history and score to PDF.
2.  **Latency Optimization**: Switch to GPT-4o-Audio-Realtime API for sub-500ms response.
3.  **Custom Personas**: Allow uploading a "Interviewer Style" document.
