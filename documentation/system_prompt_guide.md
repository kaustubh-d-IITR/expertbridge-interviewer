# System Prompts & RAG Workflow Guide

This document explains exactly how the AI generates questions, where the prompts live, and how the "RAG" (Retrieval-Augmented Generation) workflow connects the pieces.

## 🔄 The Data Flow (RAG Workflow)

1.  **Selection (UI)**: You select a "Job Context" (JSON) in the sidebar.
2.  **Ingestion**: `main_app.py` loads this JSON (`current_job_context`).
3.  **Orchestration**: `Orchestrator.start_interview` receives this JSON and passes it to the **Brain**.
4.  **Generation**: The Brain combines **Three Layers** of prompts to generate the AI's personality and questions.

## 🧠 The Three Prompt Layers

The AI's "Mind" is built from these three sources, combined in `src/core/brain.py`:

### Layer 1: The Core Persona (Static)
*   **Location**: `src/core/brain.py` -> `_get_static_system_prompt()`
*   **Purpose**: Defines the "Interviewer" personality (Professional, curious, probing).
*   **Edit Here To**: Change the tone, strictness, or general behavior.

### Layer 2: The Candidate Strategy (Dynamic)
*   **Location**: `src/utils/question_strategy.py` -> `build_question_strategy()`
*   **Purpose**: Analyzes the **Candidate's CV/Profile** (Skills, Experience) to create a tailored strategy.
*   **Edit Here To**: Change how it reacts to Senior vs Junior, or specific tech stacks (e.g., adding a specific question for "Python").

### Layer 3: The Job Context (The Domain JSON)
*   **Location**: `src/core/brain.py` -> `set_job_context()`
*   **Purpose**: Injects the **Specific Domain Knowledge** you selected (e.g., "Healthcare Data Privacy", "SAP S/4HANA").
*   **Action**: The Brain now explicitly sees: *"[DOMAIN KNOWLEDGE] Use this context..."*
*   **Edit Here To**: You don't edit code for this; you edit the **JSON files in `output/`**.

## 🛠️ Comparison: Before vs. After Logic

| Feature | Before (Broken Connection) | Now (Fixed) |
| :--- | :--- | :--- |
| **Persona** | ✅ Standard Interviewer | ✅ Standard Interviewer |
| **Candidate** | ✅ Personalized to CV | ✅ Personalized to CV |
| **Domain JSON** | ❌ **IGNORED** (Dropped in Orchestrator) | ✅ **INJECTED** into System Prompt |

## 📝 How to Enhance Question Quality

To improve the questions "without breaking the system", you have 3 entry points:

1.  **General Quality**: Modify `src/core/brain.py` -> `_get_static_system_prompt`.
    *   *Example*: Add "Always ask for STAR method examples."
2.  **Specific Skills**: Modify `src/utils/question_strategy.py`.
    *   *Example*: Add a new rule for "React Native" in the `skill_questions` dictionary.
3.  **Domain Specifics**: Edit the **JSON files** in `output/`.
    *   *Example*: Add "Key Compliance Regulations" to the JSON description. The AI will see it and ask about it.
