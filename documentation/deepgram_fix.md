# Deepgram Aura TTS Fix Guide

This guide details the exact steps taken to fix the Deepgram Aura TTS issue in the `AI_REBUILD` (and `EXPERTBRIDGE_INTERVIEWER`) repository.

## 1. Code Fix: deepgram.speak Attribute Error

**Issue:**
The `DeepgramClient` was throwing `AttributeError: 'SpeakClient' object has no attribute 'v'` when accessing the `.speak.v("1")` shortcut. This is due to SDK updates or environment differences.

**Fix:**
We updated `src/core/speaker.py` to use a **Dictionary** for options instead of the `SpeakOptions` class (which was causing imports errors). We also reverted to `.speak.v("1")` as `.rest` is not available in SDK 3.7.3.

**File:** `src/core/speaker.py`

```python
# BEFORE (Line ~37)
# from deepgram import SpeakOptions
# options = SpeakOptions(model=...)

# AFTER
# Simple Dict (Compatible with all versions)
options = {"model": final_model}
# Use standard .v("1")
self.deepgram.speak.v("1").save(temp_filename, {"text": text}, options)
```

## 2. Dependency Fix: OpenAI Crash (httpx incompatibility)

**Issue:**
The application was crashing on startup with `TypeError: Client.__init__() got an unexpected keyword argument 'proxies'`. This was causd by an incompatibility between `openai==1.54.0` and the latest `httpx==0.28.1`. The old `openai` library tries to pass a `proxies` argument that the new `httpx` client no longer accepts.

**Fix:**
We downgraded `httpx` to version `0.27.2`.

**Steps to Apply:**

1.  **Update `requirements.txt`**:
    Ensure the file contains `httpx==0.27.2`.
    
    ```text
    httpx==0.27.2
    ```

2.  **Install the specific version**:
    Run this command in your terminal:
    
    ```bash
    pip install httpx==0.27.2
    ```

## Verification

After applying these fixes:
1.  Run `streamlit run main_app.py`.
2.  Start an interview.
3.  Speak a sentence.
4.  The AI should respond with both text and audio.
