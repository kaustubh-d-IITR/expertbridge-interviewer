from pypdf import PdfReader
import json
# Cache Buster v4.5

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
        # Ensure it's valid JSON
        profile_json = json.loads(raw_json)
        print(f"[DEBUG] Extracted Candidate JSON: {json.dumps(profile_json, indent=2)}")
        print(f"[Parser] Successfully extracted profile for: {profile_json.get('full_name', 'Unknown')}")
        return profile_json
    except Exception as e:
        print(f"[ERROR] Profile extraction failed: {e}")
        # Return a minimal placeholder on failure using the new schema
        return {
            "full_name": "Candidate",
            "current_role": "Expert",
            "years_of_experience": "N/A",
            "top_skills": [],
            "industries": [],
            "key_project": "Not Specified",
            "key_experience": "Not Specified"
        }
