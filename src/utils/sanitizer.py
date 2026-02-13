import json
import re

def clean_ai_response(raw_content):
    """
    EXTREMELY ROBUST CLEANER for AI Responses.
    Guarantees that NO JSON artifacts are returned to the user.
    """
    if not raw_content:
        return {
            "text": "I didn't catch that.",
            "score": 0,
            "terminate": False
        }

    # 1. Try Standard JSON Parse (Happy Path)
    # We first try to find the largest outer block of JSON
    json_match = re.search(r"\{.*\}", raw_content, re.DOTALL)
    clean_json_str = json_match.group(0) if json_match else raw_content
    
    try:
        data = json.loads(clean_json_str)
        # If successfully parsed, extract fields
        return {
            "text": data.get("response_text", raw_content).strip(),
            "score": data.get("signal_score", 0),
            "terminate": data.get("terminate_interview", False)
        }
    except json.JSONDecodeError:
        pass # Continue to regex strategy

    # 2. Regex Strategy (The "Nuclear" Option)
    # specifically looks for "response_text": "VALUE" pattern
    text_match = re.search(r'"response_text"\s*:\s*"(.*?)"', raw_content, re.DOTALL)
    
    extracted_text = ""
    if text_match:
        extracted_text = text_match.group(1)
    else:
        # 3. Brute Force Cleanup (If regex fails due to complex nesting/escaping)
        # If we see the key, we try to chop it off
        if "response_text" in raw_content:
            parts = raw_content.split('"response_text":')
            if len(parts) > 1:
                chunk = parts[1].strip()
                # Remove leading quote
                if chunk.startswith('"'): chunk = chunk[1:]
                # Find end of value (next quote or end of object)
                # We assume the value is validly quoted usually
                end_idx = chunk.find('",')
                if end_idx == -1: end_idx = chunk.find('"}')
                
                if end_idx != -1:
                    extracted_text = chunk[:end_idx]
                else:
                    # desperation: valid text until the next newline or something?
                    extracted_text = chunk # risking it
            else:
                extracted_text = raw_content # Should not happen if 'in' check passed
        else:
            # No "response_text" key found. Checking if it looks like JSON info
            if "{" in raw_content and "}" in raw_content:
                 # It IS JSON but we can't find the key. 
                 # Return a safe error message to hide the code.
                 return {
                     "text": "I apologize, I had a momentary system glitch. Could you please repeat your answer?",
                     "score": 0,
                     "terminate": False
                 }
            else:
                # It's likely just plain text (Model ignored JSON instruction)
                extracted_text = raw_content

    # Final Cleanup of extracted text
    # Sometimes it might still have artifacts if regex was greedy
    extracted_text = extracted_text.strip()
    
    # Check for leftover JSON artifacts at the end
    extracted_text = re.sub(r'",\s*"signal_score".*$', '', extracted_text, flags=re.DOTALL)
    extracted_text = re.sub(r'"\s*\}\s*$', '', extracted_text)
    
    # Try to extract Score/Terminate separately via Regex for partial matches
    score = 0
    score_match = re.search(r'"signal_score"\s*:\s*(\d+)', raw_content)
    if score_match: score = int(score_match.group(1))
    
    terminate = False
    term_match = re.search(r'"terminate_interview"\s*:\s*(true|false)', raw_content, re.IGNORECASE)
    if term_match and term_match.group(1).lower() == 'true': terminate = True

    return {
        "text": extracted_text,
        "score": score,
        "terminate": terminate
    }
