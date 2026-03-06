# Project Status Report: Zero-Touch Implementation (Part 2)
**Date**: 2026-03-05
**Status**: v4.9 (Alpha-Stable, Semantic Unstable)

## 1. Work Accomplished (Post Part 1)
Since the restoration of the Deepgram REST API, the following "Zero-Touch" features were implemented:

*   **v4.4 (Zero-Touch Core)**: Removed manual "Candidate Profile" form and implemented automated PDF text extraction + LLM JSON parsing.
*   **v4.5-v4.6 (Connectivity)**: Resolved `ImportError` issues caused by SDK caching and legacy prompt deletions. System stability restored.
*   **v4.7 (Semantic Intelligence)**: Introduced a new JSON schema focusing on `key_project` and `key_experience` to replace generic keyword extraction.
*   **v4.8 (Forced Opening)**: Refactored `brain.py` to eliminate hardcoded greetings. The AI now performs an active LLM call for the first turn, strictly bound to the extracted JSON profile.
*   **v4.9 (Extraction Tuning)**: Optimized the extraction prompt and added `[DEBUG]` terminal logs to verify what the LLM captures from the resume.

## 2. The Persistent Problem: "Semantic Blindness"
Despite the logic being strictly bound to the JSON, the **Extraction Step is yielding "Not Specified" or generic summaries** for complex resumes. 

**Root Causes:**
1.  **PDF Noise**: Raw text extraction from PDFs often lacks structured headers, making it hard for a single-pass LLM to isolate "Experience" vs "Education".
2.  **Prompt Overload**: A single prompt asking to "Extract Name, Skills, Roles, AND Summarize 2 Projects" often leads the LLM to take the path of least resistance (generic output).
3.  **Context Context**: The extraction happens in a vacuum without knowing the target Job Description, so it doesn't know *which* project is "impressive".

## 3. Proposed Strategic Approaches

### Approach A: Multi-Pass Chain-of-Thought (The Pipeline approach)
Instead of one prompt, use a 3-step pipeline:
1.  **Sectioning**: LLM identifies and splits the raw text into `Contact`, `Skills`, and `Professional_History` blocks.
2.  **Targeting**: LLM picks the top 2 roles from `Professional_History`.
3.  **Synthesis**: LLM summarizes those 2 roles into the high-signal "Key Project" format.
*Pros*: High accuracy. *Cons*: Slower startup (+5-7 seconds).

### Approach B: The "5-Second Verification" UI (The Product approach)
Instead of a "Zero-Touch" flow that might be "Zero-Quality", implement a "Low-Touch" flow:
1.  User uploads resume.
2.  AI extracts JSON and displays it in a sleek, editable card.
3.  User spends 5 seconds confirming or tweaking the "Key Project" summary.
4.  User clicks "Confirm & Start".
*Pros*: Ensures 100% interview quality. *Cons*: Adds one click to the user flow.

### Approach C: RAG-Lite Selection (The Technical approach)
Don't summarize the resume during ingestion at all.
1.  Ingest the entire raw resume text into the Brain's context.
2.  Have the Brain's "Opening Instruction" be: "Read the entire raw text below. Find the most complex technical project mentioned. Ask a deep-dive question about it immediately."
*Pros*: Fastest startup. *Cons*: Relies on the Brain's long-context reasoning (higher token cost per turn).

---
**Recommendation**: I suggest starting with **Approach B** or **Approach A** to ensure the interviewer remains "Elite" and doesn't fall back to generic behavior.
