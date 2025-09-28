# extractor.py

import os
from dotenv import load_dotenv
from numind import NuMind

# Do NOT auto-load API key from environment. Require the user to provide it at runtime.
_api_key = None
_client = None


def set_numind_api_key(key: str) -> bool:
    """Set the NuMind API key at runtime and init the client.

    Returns True if client initialized successfully, False otherwise.
    """
    global _api_key, _client
    try:
        if not key or not key.strip():
            return False
        _api_key = key.strip()
        _client = NuMind(api_key=_api_key)
        return True
    except Exception as e:
        # Leave _client as None on failure
        _client = None
        return False


def is_numind_configured() -> bool:
    """Return True if the NuMind client is configured."""
    return _client is not None


def extract_resume_data(text: str) -> dict:
    """Extract structured resume data from raw text using NuMind."""
    schema1 = {
        "Personal_Information": {
            "First Name": "verbatim-string",
            "Last Name": "verbatim-string",
            "Address": "verbatim-string",
            "Phone_Number": "verbatim-string",
            "Email": "verbatim-string",
            "Website": "verbatim-string"
        },
        "Education": [
            {
                "Degree": "verbatim-string",
                "Institution": "verbatim-string",
                "Year": "integer"
            }
        ],
        "Experience": [
            {
                "Position": "verbatim-string",
                "Company": "verbatim-string",
                "Location": "verbatim-string",
                "Start_Date": "date-time",
                "End_Date": "date-time"
            }
        ],
        "Technical Skills": [
            "string"
        ],
        "Soft Skills": [
            "string"
        ]
    }
    try:
        if _client is None:
            return {"error": "NuMind client not configured. Please provide API key in the application sidebar."}
        output = _client.extract(template=schema1, input_text=text)
        return output
    except Exception as e:
        return {"error": str(e)}
    
def extract_jd_data(text: str) -> dict:
    """Extract structured job description data from raw text using NuMind."""
    schema2 = {
        "Job Title": "verbatim-string",
        "Experience Required": "string",
        "Skills Required": [
            "string"
        ]
    }
    try:
        if _client is None:
            return {"error": "NuMind client not configured. Please provide API key in the application sidebar."}
        output = _client.extract(template=schema2, input_text=text)
        return output
    except Exception as e:
        return {"error": str(e)}



