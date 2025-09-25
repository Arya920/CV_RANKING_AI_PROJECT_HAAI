import os
import json
import re
from pdfminer.high_level import extract_text
import docx
# from pyresparser import ResumeParser

# def parse_resume(file_path):
#     """Extract structured info from resume."""
#     data = ResumeParser(file_path).get_extracted_data()
#     return data

def safe_json_loads(response: str):
    """
    Extract and parse the first valid JSON object from a response string.
    """
    try:
        start = response.find("{")
        if start == -1:
            return {"error": "No JSON object found", "raw_response": response}

        # Balance braces to capture only the first full JSON object
        depth = 0
        for i, ch in enumerate(response[start:], start=start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    json_str = response[start:i+1]
                    return json.loads(json_str)

        return {"error": "Unbalanced braces", "raw_response": response}
    except Exception as e:
        return {"error": str(e), "raw_response": response}

def extract_text_from_pdf(file_path):
    """Extract raw text from a PDF using pdfminer."""
    return extract_text(file_path)

def extract_text_from_docx(file_path):
    """Extract raw text from a DOCX using python-docx."""
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

def parse_resume_with_llm(file_path, llm=None):
    """Parse resume into structured JSON using raw text + LLM."""
    print(file_path)
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
            print(response)
            return safe_json_loads(response)
        except:
            return {"error": "Failed to parse JSON", "raw_text": text[:1000]}
    else:
        return {"raw_text": text}


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
        print(response)
        try:
            # return json.loads(response)
            return safe_json_loads(response)
        except Exception as e:
            print(str(e))
            return {"skills": jd_text.split(), "experience": "N/A"}
    else:
        return {"skills": jd_text.split(), "experience": "N/A"}
