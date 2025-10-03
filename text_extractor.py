"""
Utility functions for extracting text from uploaded files.

This module provides three small helpers that accept a Streamlit
uploaded file-like object and attempt to return the text content.
On failure the functions return an empty string (or raise a RuntimeError
for a missing optional dependency in the DOCX case) so the calling
Streamlit UI can surface a friendly message.
"""

import pdfplumber
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file) -> str:
    """Extract text from a PDF file.

    Accepts a file-like object and attempts to read all pages using
    pdfplumber. Returns an empty string if extraction fails. The
    function is defensive about the file pointer position (resets to
    the start when possible).
    """
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
        # Log the exception for debugging but return empty string to the UI
        logger.exception(f"PDF extraction failed: {e}")
        return ''


def extract_text_from_txt(file) -> str:
    """Extract text from a plain text file.

    The function handles both bytes and str payloads from the uploaded
    file and decodes bytes with UTF-8 ignoring errors.
    """
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
    """Extract text from a DOCX file using python-docx.

    If python-docx is not installed the function raises a RuntimeError
    with an actionable install hint. On success returns the concatenated
    paragraphs as a single string.
    """
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