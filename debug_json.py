import json
import re

def _clean_json_response(raw_content):
    """
    Robustly extracts response_text from potential JSON output.
    Strategies: JSON Parse -> Regex -> String Split -> Fallback.
    """
    print(f"DEBUG: Processing raw content: {raw_content!r}")
    
    # Strategy 1: Attempt Logic JSON Extraction
    clean_content = raw_content
    json_match = re.search(r"\{.*\}", raw_content, re.DOTALL)
    if json_match:
         clean_content = json_match.group(0)
    
    print(f"DEBUG: Cleaned content for JSON parse: {clean_content!r}")
         
    try:
        data = json.loads(clean_content)
        print("DEBUG: JSON Parse Successful!")
        return {
            "text": data.get("response_text", raw_content),
            "score": data.get("signal_score", 0),
            "terminate": data.get("terminate_interview", False)
        }
    except json.JSONDecodeError as e:
        print(f"DEBUG: JSON Parse Failed: {e}")
        pass # Move to next strategy
        
    # Strategy 2: Regex for specific field "response_text": "..."
    # Handles newlines and escaped quotes reasonably well
    text_match = re.search(r'"response_text"\s*:\s*"(.*?)"', raw_content, re.DOTALL)
    if text_match:
        print("DEBUG: Regex Strategy Successful!")
        return {
            "text": text_match.group(1),
            "score": 0,
            "terminate": False
        }

    # Strategy 3: Brute Force Split (Use if model forgot quotes or messed up syntax)
    if "response_text" in raw_content:
        print("DEBUG: Attempting Brute Force Split...")
        # Try splitting by key
        parts = raw_content.split('"response_text":')
        if len(parts) > 1:
            # Take the right part, clean leading quotes/spaces
            val = parts[1].strip()
            if val.startswith('"'): val = val[1:]
            # Try to find the end of the string (next quote or comma)
            # This is messy but better than showing JSON
            end_idx = val.find('",')
            if end_idx == -1: end_idx = val.find('"}')
            if end_idx != -1:
                return {"text": val[:end_idx], "score": 0, "terminate": False}

    # Strategy 4: Fail-Safe
    print("DEBUG: All strategies failed. Returning Generic Error.")
    return {
        "text": "I apologize, I processed that thought incorrectly. Please continue.",
        "score": 0,
        "terminate": False
    }

# Test Cases
test_input_1 = '{ "response_text": "Understood, Costo. Let’s begin. Can you walk me through your N8N automation experience and what made it successful?", "signal_score": 0, "warning_issued": false, "terminate_interview": false }'

print("\n--- TEST 1 ---")
result = _clean_json_response(test_input_1)
print(f"Result: {result}")
