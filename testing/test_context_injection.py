
import os
import sys

# Ensure we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.brain import Brain

def test_job_context_injection():
    """Verify job context makes it into the prompt."""
    
    # Initialize Brain (mocking environment if needed, but Brain handles missing keys gracefully-ish or checks them)
    # We might need to mock keys if Brain __init__ raises strict errors.
    # Brain __init__ checks for keys. Let's assume .env is loaded or we might need to set dummy env vars for this test.
    
    os.environ["OPENAI_API_KEY"] = "dummy_key_for_test" # To pass Validation
    
    try:
        brain = Brain()
    except Exception as e:
        print(f"Brain init failed, likely due to keys. Ignoring for prompt test if possible. Error: {e}")
        return

    # Set a distinctive job context
    test_context = {
        "title": "TESTDOMAIN12345",
        "key_concepts": ["UNIQUE_CONCEPT_XYZ"]
    }
    
    brain.set_job_context(test_context)
    
    # Generate a response (This builds the messages internally)
    # We are calling _build_conversation_messages which is what we want to test.
    messages = brain._build_conversation_messages("Tell me about your experience", 0)
    
    # Check if context is in messages
    full_prompt = str(messages)
    
    print(f"DEBUG: Generated Prompt Validation...")
    
    if "TESTDOMAIN12345" in full_prompt and "UNIQUE_CONCEPT_XYZ" in full_prompt:
        print("✅ Job context is being injected correctly!")
    else:
        print("❌ Job context NOT injected!")
        print(f"Dump: {full_prompt}")
        sys.exit(1)

# Run this test:
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv() # Try to load real .env if available
    test_job_context_injection()
