from pypdf import PdfReader
import json
import os
import re
# Cache Buster v4.5

def parse_llm_json(raw_text):
    """Robustly strips markdown and extracts JSON from LLM output."""
    try:
        # Try direct parsing first
        return json.loads(raw_text)
    except json.JSONDecodeError:
        # Strip markdown backticks
        cleaned = re.sub(r'```(?:json)?', '', raw_text).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            print(f"[ERROR] Final JSON parsing failed on: {cleaned[:100]}...")
            return None

def parse_cv(file):
    """
    Extracts raw text from the uploaded PDF file.
    Args:
        file: A file-like object (e.g., from st.file_uploader)
    Returns:
        str: Extracted text from the PDF.
    """
    try:
        pdf_reader = PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += (page.extract_text() or "") + "\n"
            
        print(f"[DEBUG] Extracted {len(text)} characters from CV.")
        return text
    except Exception as e:
        print(f"[ERROR] PDF Parsing failed: {e}")
        return f"Error reading PDF: {e}"

def extract_profile_to_json(resume_text, brain_instance):
    """
    Uses the Brain's LLM client to extract a structured profile from resume text.
    """
    from src.utils.prompts import EXTRACTION_SYSTEM_PROMPT
    
    print("[Parser] Extracting profile via AI...")
    try:
        response = brain_instance.client.chat.completions.create(
            model=brain_instance.deployment_name,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"EXTRACT FROM THIS RESUME:\n\n{resume_text}"}
            ],
            temperature=0.1, # Lower temperature for extraction accuracy
            response_format={"type": "json_object"}
        )
        
        raw_json = response.choices[0].message.content.strip()
        
        # Robustly parse JSON to handle markdown wrappers
        profile_json = parse_llm_json(raw_json)
        
        if not profile_json:
            raise ValueError("Failed to parse valid JSON from LLM response.")
            
        # Save JSON locally for debugging
        os.makedirs("expert_jsons", exist_ok=True)
        try:
            candidate_name = profile_json.get("personal_info", {}).get("full_name", "Unknown_Candidate")
            # Remove invalid filename characters
            safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', candidate_name)
            file_path = os.path.join("expert_jsons", f"{safe_name}.json")
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(profile_json, f, indent=4)
            print(f"[DEBUG] Successfully saved candidate profile to {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to save JSON locally: {e}")

        print(f"[DEBUG] Extracted Candidate JSON: {json.dumps(profile_json, indent=2)}")
        print(f"[Parser] Successfully extracted profile for: {profile_json.get('personal_info', {}).get('full_name', 'Unknown')}")
        return profile_json
    except Exception as e:
        print(f"[ERROR] Profile extraction failed: {e}")
        # Return a clear error placeholder matching the nested schema
        return {
            "personal_info": {"full_name": "EXTRACTION_FAILED", "headline": "Extraction Error"},
            "experience": {"recent_roles": []},
            "skills": {"technical": []},
            "education": {"institutions": []}
        }
