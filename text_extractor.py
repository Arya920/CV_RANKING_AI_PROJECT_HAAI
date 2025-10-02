# text_extractor.py

import pdfplumber
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file) -> str:
    """Extract text from a PDF file (Streamlit uploaded file object)."""
    # Ensure we read from the start of the file-like object
    try:
        file.seek(0)
    except Exception:
        pass
    try:
        text = ''
        with pdfplumber.open(BytesIO(file.read())) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
        return text.strip()
    except Exception as e:
        logger.exception(f"PDF extraction failed: {e}")
        return ''


def extract_text_from_txt(file) -> str:
    """Extract text from a plain text file (Streamlit uploaded file object)."""
    # Reset pointer to start in case file was read before
    try:
        file.seek(0)
    except Exception:
        pass
    try:
        raw = file.read()
        if isinstance(raw, bytes):
            text = raw.decode('utf-8', errors='ignore')
        else:
            text = str(raw)
        return text.strip()
    except Exception as e:
        logger.exception(f"TXT extraction failed: {e}")
        return ''


def extract_text_from_docx(file) -> str:
    """Extract text from a DOCX file (Streamlit uploaded file object) using python-docx."""
    try:
        from docx import Document
    except Exception as e:
        raise RuntimeError("python-docx is required to extract DOCX files. Install with `pip install python-docx`")

    # Reset pointer and read bytes
    try:
        file.seek(0)
    except Exception:
        pass

    doc = Document(BytesIO(file.read()))
    paragraphs = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(paragraphs).strip()