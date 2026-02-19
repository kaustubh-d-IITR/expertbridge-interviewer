# AI Scoring & Analysis System

This document details the multi-layered scoring system used by the AI Interviewer to evaluate candidates. The system operates on two levels: **Real-time Per-Turn Analysis** and **Post-Interview Comprehensive Analysis**.

## 1. Real-time Per-Turn Analysis (`Brain`)

After every candidate response, the `Brain` component (`src/core/brain.py`) analyzes the answer using a dedicated LLM call (`analyze_answer`). This evaluation happens in parallel with the audio generation to minimize latency.

### 1.1 Core Dimensions (1-5 Scale)
The candidate's answer is evaluated on three specific dimensions, rated from **1 to 5**:

| Dimension | Description | What a '5' looks like |
| :--- | :--- | :--- |
| **DEPTH** | Quality of evidence and domain expertise. | Specific examples, metrics, technical depth, and clear outcomes. |
| **THINKING** | Structure and reasoning quality. | Logical flow, structured approach (e.g., STAR method), and clear problem-solving. |
| **FIT** | Communication and professionalism. | Clear articulation, professional tone, and concise delivery. |

### 1.2 Overall Score (0-100)
A holistic **Overall Score** (0-100) is assigned to each answer.
*   **Significance**: This is the primary metric used for the final quantitative result.
*   **Calculation**: While correlated with the 1-5 dimensions, the LLM generates this as a distinct value based on the total impression of the answer.

### 1.3 Behavioral Penalties & Abuse Detection
The system includes strict behavioral monitoring:

*   **Abuse Detection**: If the user uses offensive language (detected via keyword matching in `detect_abuse`), the system:
    *   Issues a warning (Strike 1) or terminates the interview (Strike 2).
    *   **Auto-Score**: Sets the `overall_score` to **0** for that turn.
    *   **Dimensions**: Sets Depth, Thinking, and Fit scores to **1**.
    *   **Red Flag**: Adds "Inappropriate language" or "Terminated for conduct" to the analysis.

## 2. Session Aggregation (`Orchestrator`)

The `Orchestrator` (`src/core/orchestrator.py`) maintains the state of the interview and aggregates the real-time scores.

*   **Running Score collection**: Every `overall_score` from valid turns is appended to a list.
*   **Final Score Calculation**: 
    $$ \text{Final Score} = \frac{\sum \text{Overall Scores}}{\text{Total Scored Turns}} $$
    *   This results in a final average between 0 and 100.
    *   Examples:
        *   3 answers scoring 80, 90, 70 -> Final: **80**.
        *   Abusive behavior (0 score) significantly drags down the average.

## 3. Post-Interview Comprehensive Analysis

Once the interview concludes, the full transcript is sent to the `ComprehensiveAnalyzer` (`src/analysis/comprehensive_analyzer.py`). This is a separate, more expensive analysis pass (often using stronger models like GPT-4o) to determine the final hiring recommendation.

### 3.1 Qualitative Rating
The analyzer outputs one of three ratings based on the entire context:
*   **Strong Hire**: Exceeds expectations, deep expertise, excellent communication.
*   **Hire**: Meets requirements, solid capability, no major red flags.
*   **No Hire**: Fails to meet requirements, lacks depth, or exhibits red flags.

### 3.2 Report Generation
The qualitative data (Strengths, Weaknesses, Summary) is combined with the quantitative `Final Score` to generate the PDF report (`src/reports/pdf_generator.py`).

---

## Summary Table

| Metric | Range | Source | Purpose |
| :--- | :--- | :--- | :--- |
| **Depth** | 1-5 | Brain (Per Turn) | Granular feedback on expertise. |
| **Thinking** | 1-5 | Brain (Per Turn) | Granular feedback on logic/structure. |
| **Fit** | 1-5 | Brain (Per Turn) | Granular feedback on communication. |
| **Overall Score** | 0-100 | Brain (Per Turn) | Primary quantitative metric for the answer. |
| **Final Score** | 0-100 | Orchestrator (Aggregated) | **The final interview score.** Average of all Overall Scores. |
| **Hiring Rating** | Label | ComprehensiveAnalyzer | "Strong Hire" / "Hire" / "No Hire" recommendation. |
