import os
from utils import safe_json_loads
from pdfminer.high_level import extract_text
import docx

# Functions to extract text from PDF and DOCX files
def extract_text_from_pdf(file_path):
    """Extract raw text from a PDF using pdfminer."""
    return extract_text(file_path)

# Function to extract text from DOCX files
def extract_text_from_docx(file_path):
    """Extract raw text from a DOCX using python-docx."""
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

# Function to parse resume using LLM into structured JSON output
# Extracting multiple fields like Name, Contact, Skills, Education, Experience, etc.
# Aspect based extraction will result in better matching  
def parse_resume_with_llm(file_path, llm=None):
    """Parse resume into structured JSON using raw text + LLM."""
    suffix = os.path.splitext(file_path.name)[-1].lower()
    if suffix == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif suffix == ".docx":
        text = extract_text_from_docx(file_path)
    else:
        return {"error": "Unsupported format", "raw_file": file_path}

    if llm:
        prompt = f"""
        Extract the following information from this resume text:
        - Name
        - Contact info (email, phone if present)
        - Skills (list)
        - Education (degrees, universities)
        - Experience (roles, companies, years)
        - Certifications / Projects if present

        Return the result in JSON format. Ensure the braces are balanced.

        Resume text:
        {text[:3000]} 
        """
        response = llm(prompt)
        try:
            # return json.loads(response)
            return safe_json_loads(response)
        except:
            return {"error": "Failed to parse JSON", "raw_text": text[:1000]}
    else:
        return {"raw_text": text}

# Function to parse job description using LLM into structured JSON output
def parse_job_description(jd_text, llm=None):
    """Use LLM to extract structured requirements from JD."""
    if llm:
        prompt =f"""
        Extract thew following information from job description given. 
        1. Key requirements
        2. Must-have skills
        3. Years of experience
        4. Nice-to-have skills 
        Return output as JSON, template as:
           {{"key_requirements": ["..."], "must_have_skills": ["..."], "years_of_experience": "X years", "nice_to_have_skills": ["..."]}}
        Given job description: {jd_text}
        """
        response = llm(prompt)
        try:
            # return json.loads(response)
            return safe_json_loads(response)
        except Exception as e:
            return {"skills": jd_text.split(), "experience": "N/A"}
    else:
        return {"skills": jd_text.split(), "experience": "N/A"}
