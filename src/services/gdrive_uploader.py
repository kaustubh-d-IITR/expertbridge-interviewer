import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Target Folder ID
GDRIVE_FOLDER_ID = "1zkd0ygPpnZX7ZFwSS7gvYuFtyTMZ-0QV"
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_gdrive_service():
    """Authenticates and returns the Google Drive service."""
    creds = None
    
    # Check for Streamlit Secrets / Env Variable first (for Cloud deployment)
    if "GDRIVE_CREDENTIALS_JSON" in os.environ:
        try:
            creds_info = json.loads(os.environ["GDRIVE_CREDENTIALS_JSON"])
            creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        except Exception as e:
            print(f"[GDrive Error] Failed to parse GDRIVE_CREDENTIALS_JSON: {e}")
            return None
    else:
        # Fallback to local file for development by searching for the pattern
        import glob
        files = glob.glob("expertbridge-audio-uploader-*.json")
        if files:
            creds = service_account.Credentials.from_service_account_file(files[0], scopes=SCOPES)
        else:
            print("[GDrive Error] No credentials found!")
            return None

    try:
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"[GDrive Error] Failed to build service: {e}")
        return None

def upload_to_gdrive(file_path: str, candidate_name: str, turn_number: int, speaker: str):
    """
    Uploads an audio file to the specific Google Drive folder.
    speaker should be 'Candidate' or 'AI'.
    """
    try:
        service = get_gdrive_service()
        if not service: return False

        safe_name = candidate_name.replace(" ", "_")
        file_name = f"{safe_name}_Turn_{turn_number}_{speaker}.wav"
        if file_path.endswith(".mp3"):
            file_name = f"{safe_name}_Turn_{turn_number}_{speaker}.mp3"

        file_metadata = {
            'name': file_name,
            'parents': [GDRIVE_FOLDER_ID]
        }
        
        mimetype = 'audio/wav' if file_name.endswith('.wav') else 'audio/mpeg'
        media = MediaFileUpload(file_path, mimetype=mimetype, resumable=True)
        
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"[GDrive Success] Uploaded {file_name} with ID: {file.get('id')}")
        return True
    except Exception as e:
        print(f"[GDrive Error] Failed to upload {file_path}: {e}")
        return False
