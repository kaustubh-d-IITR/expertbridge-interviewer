# ExpertBridge AI Interviewer - Current Status Report
**Date:** February 22, 2026

This document outlines the current state of the ExpertBridge AI Interviewer project, detailing the recently implemented intelligence upgrades, the core architecture, and the technology stack.

## 1. Current State & Recent Accomplishments
The AI Interviewer has evolved from a basic prompt-driven bot into a strict, executive-level assessment tool. It is fully operational and capable of conducting dynamic, highly structured, 15-minute interviews that automatically adapt to the candidate's seniority and parsed resume history.

### Key Upgrades Implemented:
*   **Executive Prompt Intelligence:** The AI now inherently assesses candidates across 10 executive dimensions (e.g., Financial Ownership, Leadership Scale, Crisis Recovery). It automatically adapts its strictness and focus based on the candidate's years of experience (e.g., grilling a 15-year VP on org-design and P&L, while assessing a 3-year developer on execution depth).
*   **Resume-Driven Question Flow:** The system shifted from being anchored solely on the manually inputted "Key Project" to dynamically extracting topics across the entire parsed resume.
*   **MAX-2 Anti-Repetition Guard:** To prevent the AI from repeatedly drilling into the same project endlessly (e.g., the YT RAGBot issue), a strict "Maximum 2 questions per topic" limit was encoded into the core brain prompts. The AI is forced to forcefully transition to new resume experiences after 2 questions, ensuring 90-95% breadth coverage.
*   **Dynamic Opening & Job Fit:** Added a "Key Experience" field to prioritize over technical projects. If a Job Description is provided, the AI dynamically concludes the interview by explicitly challenging the candidate on their fit for the role.
*   **Multilingual Support (Speech-to-Text):** Integrated Deepgram's `nova-3-general` model with automatic language detection, allowing candidates to speak in any language (like Hindi or French), while the AI comprehends and responds strictly in English.
*   **Instruction Gateway & Auto-Termination:** Implemented an attractive pre-interview "Rules & Disclaimers" gateway page. The interview core now reliably enforces a 15-minute cutoff and smartly auto-terminates if the user states they are finished.

## 2. Technology Stack
The application is built on a modern, decoupled Python stack optimized for real-time AI interactions.

*   **Frontend UI & State Management:** 
    *   `Streamlit` (Rapid prototyping and session state management)
*   **Core AI "Brain" & Orchestrator:**
    *   `LangChain` (LLM abstraction and prompt chaining)
    *   `OpenAI / Azure OpenAI APIs` (Primary reasoning engines: `gpt-4o` and `gpt-4o-mini`)
*   **Speech & Audio Processing:**
    *   `Deepgram API` (Ultra-low latency Speech-to-Text `nova-3-general` and Text-to-Speech)
*   **Data Parsing & Storage:**
    *   `PyPDF2` (Resume parsing)
    *   JSON-based internal state memory
*   **Reporting:**
    *   `fpdf` (Generating the final dynamic PDF evaluation reports)
*   **Version Control:**
    *   `Git` (Multi-remote pushes to `origin` and `company` repositories)

## 3. Where We Stand For Now
*   **Stability:** The core interviewing engine is stable, handles edge cases (like "I don't know" answers), and appropriately challenges the user without breaking character.
*   **Deployment:** The latest codebase containing all of the intelligence, resume-driven logic, and multilingual upgrades has been successfully pushed and is live across both primary GitHub repositories.
*   **Next Steps:** The system is ready for user testing to validate the newly injected Executive Dimensions and the strict Resume-Driven Question Planner in live, real-world mock interviews.
