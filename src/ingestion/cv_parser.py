from pypdf import PdfReader

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
