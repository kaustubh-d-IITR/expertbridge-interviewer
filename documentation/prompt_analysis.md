# System Prompts & Workflow Analysis
**Project**: ExpertBridge AI Interviewer
**Location**: `documentation/prompt_analysis.md`
**Date**: 2026-03-06

This document details all RAG (Retrieval-Augmented Generation) and System prompts currently active in the AI Interviewer logic, their exact roles, where they reside in the codebase, and the chronological sequence of their execution.

---

## 1. Sequence of Prompt Execution

The AI Interviewer operates on a multi-agent, chained-prompt architecture. Here is the sequence of tasks:

1. **Phase 1: Resume Ingestion & Extraction**
   - **Trigger**: User uploads a CV.
   - **Prompt Used**: `EXTRACTION_SYSTEM_PROMPT` (from `src/utils/prompts.py`)
   - **Role**: Validates and structures the raw PDF text into a strict candidate JSON profile focusing on "Key Project" and "Key Experience".

2. **Phase 2: Brain Initialization & Persona Anchoring**
   - **Trigger**: The `Orchestrator` initializes the `Brain`.
   - **Prompts Used**: `_get_static_system_prompt()` (from `src/core/brain.py`) + `ZERO_TOUCH_INTERVIEWER_PROMPT` (from `src/utils/prompts.py`).
   - **Role**: Establishes the overarching "Executive Interviewer" persona, strict interviewing rules (no fluff, 2-question limit per topic), and injects the extracted candidate JSON directly into the context window.

3. **Phase 3: The Opening Turn (Turn 0)**
   - **Trigger**: The interview officially starts.
   - **Prompts Used**: Inline `get_opening_message` prompt (from `src/core/brain.py`) + Turn 0 instruction from `_get_dynamic_topic_instruction()` (from `src/core/brain.py`).
   - **Role**: Forces the LLM to completely bypass generic greetings ("Hello", "Welcome") and generate a highly specific, deep technical question based exactly on the candidate's "Key Project".

4. **Phase 4: The Core Interview Loop (Turns 1 - 7)**
   - **Trigger**: The user speaks an answer.
   - **Analysis Prompt**: Inline `analyze_answer` prompt (from `src/core/brain.py`) evaluates the user's transcript on Depth, Thinking, and Fit (The Crucible Framework) and outputs a JSON score.
   - **Next Question Prompt**: `_get_dynamic_topic_instruction()[N]` (from `src/core/brain.py`) is injected into the system array to explicitly force the LLM to change topics (e.g., from "System Depth" to "Financial Ownership" to "Crisis Recovery").

5. **Phase 5: Conclusion & Termination (Turn 8+)**
   - **Trigger**: The maximum turn limit or time limit is reached.
   - **Prompt Used**: Inline `generate_closing_message` prompt (from `src/core/brain.py`).
   - **Role**: Instructs the LLM to gracefully end the interview without asking any further questions.

---

## 2. Detailed Prompt Directory & File Locations

### A. Data Extraction (Ingestion Phase)
- **`EXTRACTION_SYSTEM_PROMPT`**
  - **File Location**: `src/utils/prompts.py`
  - **Functionality**: Uses an LLM to read the raw resume text. Instructs the AI to scan for specific sections ("Experience", "Projects") and structure the data into a JSON schema (`full_name`, `years_of_experience`, `key_project`, `key_experience`, `top_skills`).
  - **Importance**: Critical for the "Zero-Touch" flow. If this prompt fails or hallucinates, the rest of the interview becomes generic.

### B. Overarching Persona & Guidelines (Contextual RAG)
- **`_get_static_system_prompt()`**
  - **File Location**: `src/core/brain.py` (Inside the `Brain` class)
  - **Functionality**: Defines the "Elite Senior Recruiter" persona. Enforces the **MAX-2, NO-REPEAT RULE** (forces the AI to move to a new topic after 2 questions) and strictly blocks generic praise ("Great answer!").
  
- **`ZERO_TOUCH_INTERVIEWER_PROMPT`**
  - **File Location**: `src/utils/prompts.py`
  - **Functionality**: Acts as the injection site for the candidate's JSON profile (`{key_project}`, `{key_experience}`). Houses the `YOUR DIRECTIVES` (e.g., "THE BS DETECTOR"). This is concatenated with the static system prompt inside `brain.py`.

- **`DOMAIN_PERSONAS` & `INTERVIEWER_SYSTEM_PROMPT`** (Legacy/Fallback)
  - **File Location**: `src/utils/prompts.py`
  - **Functionality**: Used to dynamically tint the AI's vocabulary based on the candidate's industry (e.g., shifting the tone to a "Senior Medical Board Director" for Healthcare vs. a "Wall Street CFO" for Finance) when the Zero-Touch profile mechanism is not used.

### C. Dynamic Turn-by-Turn Steering (Execution Phase)
- **`get_opening_message` Inline Prompt**
  - **File Location**: `src/core/brain.py` (Inside `Brain.get_opening_message`)
  - **Functionality**: An explicit user-role trigger sent at Turn 0: *"The candidate has just joined the call. Look at their [MANDATORY CANDIDATE CONTEXT]. Ask the first highly specific technical question right now. No pleasantries."*
  
- **`_get_dynamic_topic_instruction(turn_count)`**
  - **File Location**: `src/core/brain.py` (Inside the `Brain` class)
  - **Functionality**: A Python dictionary containing 8 distinct system commands. Depending on how many questions have been asked, this injects a `[CRITICAL INSTRUCTION]` forcing the LLM to ask about a specific dimension:
    - *Turn 0 & 1*: System / Architectural Depth.
    - *Turn 2 & 3*: Financial Ownership & Crisis Recovery.
    - *Turn 4 & 5*: Stakeholder Influence & Ethics.
    - *Turn 6 & 7*: Career Pattern Validation.

### D. Analytical & Administrative (Evaluation Phase)
- **`analyze_answer` Inline Prompt**
  - **File Location**: `src/core/brain.py` (Inside `Brain.analyze_answer`)
  - **Functionality**: A completely separate LLM call that happens in the background while the user is waiting for the next question. It evaluates the user's just-spoken answer against the "Crucible Framework", scoring Information Density, Expert Signals (war stories), and Amateur Signals (buzzwords), outputting a JSON payload.
  
- **`generate_closing_message` Inline Prompt**
  - **File Location**: `src/core/brain.py` (Inside `Brain.generate_closing_message`)
  - **Functionality**: A safety-valve inline prompt used when the interview time/turn limits hit. It feeds the user's final answer to a fast LLM (`gpt-4o-mini`) and strictly forbids it from asking another question, ensuring a professional sign-off ("*Generate a brief, professional closing statement (Thank them, say goodbye). Do NOT ask a question.*").

---

## Summary of the Architecture
The system does not rely on a single "God Prompt". Instead, it utilizes **State-Machine Prompting**. The foundational rules are established once at the beginning (`_get_static_system_prompt`, `ZERO_TOUCH_INTERVIEWER_PROMPT`), and the granular behavior is micro-managed frame-by-frame using situational context injections (`_get_dynamic_topic_instruction`). This prevents context drift and ensures the AI remains highly aggressive and hyper-personalized throughout the interview.
