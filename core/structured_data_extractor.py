# extractor.py

import os
from dotenv import load_dotenv
from numind import NuMind

# Load API key from .env file
load_dotenv()
api_key = os.getenv("NUMIND_API_KEY")
client = NuMind(api_key=os.environ["NUMIND_API_KEY"])


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
        output = client.extract(template=schema1, input_text=text)
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
        output = client.extract(template=schema2, input_text=text)
        return output
    except Exception as e:
        return {"error": str(e)}



