# text_extractor.py

import pdfplumber
from io import BytesIO

def extract_text_from_pdf(file) -> str:
    """Extract text from a PDF file (Streamlit uploaded file object)."""
    text = ''
    with pdfplumber.open(BytesIO(file.read())) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + '\n'
    return text.strip()

def extract_text_from_txt(file) -> str:
    """Extract text from a plain text file (Streamlit uploaded file object)."""
    # Reset pointer to start in case file was read before
    file.seek(0)
    text = file.read().decode('utf-8')
    return text.strip()