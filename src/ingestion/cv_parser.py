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
        messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": f"EXTRACT FROM THIS RESUME:\n\n{resume_text}"}
        ]
        
        raw_text = ""
        try:
            # ATTEMPT 1: Standard GPT-4o configuration
            try:
                response = brain_instance.client.chat.completions.create(
                    model=brain_instance.deployment_name,
                    messages=messages,
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                raw_text = response.choices[0].message.content
            except Exception as api_err:
                print(f"[Parser] Standard call failed: {api_err}. Retrying in minimal compatibility mode...")
                # ATTEMPT 2: O1 / Reasoning model compatibility (No temp, no response_format)
                response = brain_instance.client.chat.completions.create(
                    model=brain_instance.deployment_name,
                    messages=messages
                )
                raw_text = response.choices[0].message.content

            # CLEANING: Strip Markdown backticks
            cleaned_text = re.sub(r'^```(?:json)?\n?|```$', '', raw_text.strip(), flags=re.MULTILINE).strip()
            
            profile_json = json.loads(cleaned_text)
            
            # Save JSON locally for debugging
            os.makedirs("expert_jsons", exist_ok=True)
            try:
                candidate_name = profile_json.get("personal_info", {}).get("full_name", "Unknown_Candidate")
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
            
        except Exception as final_e:
            print(f"[ERROR] LLM Evaluation/Parsing failed final wrapper: {final_e}")
            raise final_e
            
    except Exception as e:
        print(f"[ERROR] Profile extraction failed: {e}")
        # Return a clear error placeholder matching the nested schema
        return {
            "personal_info": {"full_name": "EXTRACTION_FAILED", "headline": f"Error: {str(e)}"},
            "experience": {"recent_roles": []},
            "skills": {"technical": []},
            "education": {"institutions": []}
        }
