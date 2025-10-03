"""
Wrapper utilities for calling the NuMind structured extraction client.

This module intentionally avoids auto-loading API keys from the environment
— the application must call `set_numind_api_key` at runtime to initialize
the client. All extraction functions return well-formed dicts and will
return an `{"error": ...}` mapping when the client is not configured or
an exception occurs.
"""

import os
from dotenv import load_dotenv
from numind import NuMind

# Do NOT auto-load API key from environment. Require the user to provide it at runtime.
_api_key = None
_client = None


def set_numind_api_key(key: str) -> bool:
    """
    Initialize the NuMind client at runtime using the provided API key.

    Returns True if the client was initialized successfully, False otherwise.
    The function does not raise; callers can check `is_numind_configured()`.
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
    """Return True if the NuMind client is currently configured."""
    return _client is not None


def extract_resume_data(text: str) -> dict:
    """
    Send raw resume text to NuMind and return structured JSON per the schema.

    On failure or if the client is not configured the function returns a
    dictionary containing an `error` key.
    """
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
    """
    Send raw job-description text to NuMind and return structured fields.

    Returns a dict or an `{"error": ...}` mapping on failure.
    """
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



