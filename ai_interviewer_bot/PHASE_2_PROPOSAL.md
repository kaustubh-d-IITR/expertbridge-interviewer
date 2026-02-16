# ExpertBridge AI Interviewer - Phase 2 Evolution 🚀

This document outlines the architectural roadmap to evolve the Interviewer into a domain-agnostic, multilingual, and context-aware system.

---

## 1. Core Changes & Objectives

### A. Remove Code Execution Engine 🚫
**Goal:** Shift focus entirely to theoretical knowledge, situational judgment, and domain expertise.
*   **Action:** Deactivate the `Coding Challenge` tab and the `evaluate_code` method in the Brain.
*   **Result:** A streamlined, conversation-first interface suitable for doctors, lawyers, accountants, etc., not just programmers.

### B. Dynamic Domain Recognition 🧠
**Goal:** The system must "know" whom it is interviewing.
*   **Method:** Introduce a **Classification Step** before the interview starts.
    1.  **Input:** Candidate's CV Text + Job Description (JD).
    2.  **Process:** The LLM analyzes the text to classify the domain (e.g., `MEDICAL`, `FINANCE`, `LEGAL`, `SALES`, `TECH`).
    3.  **Output:** Selects a specific `SYSTEM_PROMPT` tailored to that domain (e.g., "You are a Senior Medical Board Member..." vs. "You are a CTO...").

### C. Context-Aware Interviewing (CV + JD Integration) 🤝
**Goal:** Bridge the gap between what the candidate *has* (CV) and what the company *needs* (Job Description).
*   **Input 1:** **Candidate CV** (Parsed from PDF).
*   **Input 2:** **Job Description (JSON)** (Fetched from PostgreSQL database).
*   **Logic:** The System Prompt will be dynamically constructed:
    > "You are interviewing [Candidate Name] for the role of [Job Title].
    >
    > **Their Experience:** [Summary of CV]
    > **Role Requirements:** [Summary of JSON JD]
    >
    > **Task:** Verify if the candidate's experience matches the requirements. Probe specifically for gaps between their CV and the JD."

---

## 2. Deepgram vs. ElevenLabs: The Voice Dilemma 🗣️

You asked for a comparison to support Multilingual (English, Hindi, French) and Multi-Voice options.

| Feature | **Deepgram Aura** (Current) | **ElevenLabs Turbo** |
| :--- | :--- | :--- |
| **Primary Strength** | ⚡ **Speed (Latency)** | 🎭 **Emotion & Quality** |
| **Latency** | Extremely Fast (~250ms). Feels like a real conversation. | Slower (~600ms - 1.5s). Can feel "laggy" in live chat. |
| **Cost** | Much Cheaper ($0.015/min). | Expensive ($0.18/min - 10x more). |
| **Multilingual** | Good English. Expanding support for other langs. | **Best in Class.** Automatically speaks Hindi/French perfectly with the *same* voice. |
| **Voice Variety** | Limited (~12 voices). | Unlimited (Voice Cloning & 1000+ community voices). |

### **Recommendation:**
*   **For "Real-Time" Interaction:** Stick with **Deepgram**.
    *   *Why?* In a voice interview, if the bot takes 2 seconds to answer, it breaks the immersion. Deepgram is instant.
    *   *Voices:* Deepgram offers distinct male/female voices (`asteria`, `orion`, `arcas`, `luna`) which we can expose as a dropdown setting.
*   **For "Human Connection" (if budget allows):** Use **ElevenLabs**.
    *   *Why?* If you need the AI to sound *indistinguishable* from a human (breaths, laughs, hesitation) and speak Hindi with a perfect accent.
    *   *Trade-off:* You will sacrifice speed. The user will wait longer for a response.

---

## 3. Implementation Plan (Architecture)

### **Phase 2.1: The Brain Upgrade (No Coding)**
1.  **Modify `main_app.py`:** Remove the "Coding Challenge" tab.
2.  **Update `Orchestrator`:** Remove the "Code Phase" logic. The interview acts as a strictly linear conversation (Intro -> Deep Dive -> Conclusion).

### **Phase 2.2: The Context Merger (JD + CV)**
1.  **Database Connector:** Create a module to fetch the "Job JSON" from PostgreSQL based on a Job ID.
2.  **Prompt Engineering:** Rewrite the `INTERVIEWER_SYSTEM_PROMPT` to accept two inputs:
    ```python
    SYSTEM_PROMPT = f"""
    You are an expert in {domain}.
    Candidate: {cv_text}
    Job Requirements: {job_json}
    
    GOAL: Assess if {candidate_name} fits these requirements.
    """
    ```

### **Phase 2.3: Multilingual & Voice Selection**
1.  **UI Update:** Add a "Settings" sidebar in Streamlit.
    *   **Dropdown:** `Language` (English, Hindi, French).
    *   **Dropdown:** `Interviewer Voice` (Male - Orion, Female - Asteria).
2.  **Backend Logic:**
    *   Pass the selected `language` to **Deepgram STT** (so it understands Hindi input).
    *   Pass the selected `voice_model` to **Deepgram TTS** (so it speaks with a Male/Female voice).
    *   *Note on Translation:* If the user speaks Hindi, the **Brain (GPT-4o)** handles the translation automatically. You simply tell the System Prompt: *"Conduct the interview in {selected_language}."*

## 4. Summary of Workflows
1.  **Recruiter** posts a Job -> Stored as JSON in DB.
2.  **Candidate** applies -> System fetches Job JSON + Parses Candidate CV.
3.  **Brain** analyzes both -> Decides Domain (Medical/Tech) -> Selects Voice/Persona.
4.  **Interview Starts**:
    *   User speaks (Hindi/English).
    *   **Deepgram** transcribes (auto-detect language).
    *   **GPT-4o** thinks (compares CV vs JD).
    *   **GPT-4o** generates response (in Hindi/English).
    *   **Deepgram/ElevenLabs** speaks it out.
