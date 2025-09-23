import PyPDF2
import docx
import re
from typing import Dict, List, Any
import pdfplumber
import os

class ResumeParser:
    def __init__(self):
        # Comprehensive skill patterns
        self.skill_patterns = {
            'programming': r'\b(python|java|javascript|typescript|js|c\+\+|c#|php|ruby|go|rust|swift|kotlin|scala)\b',
            'web_frameworks': r'\b(react|angular|vue|django|flask|spring|express|laravel|rails|nodejs|node\.js)\b',
            'databases': r'\b(sql|mysql|postgresql|mongodb|redis|sqlite|oracle|cassandra|elasticsearch)\b',
            'cloud_devops': r'\b(aws|azure|gcp|docker|kubernetes|jenkins|terraform|ansible|git|gitlab|github)\b',
            'data_science': r'\b(pandas|numpy|scikit-learn|tensorflow|pytorch|spark|hadoop|tableau|powerbi|r\b|matlab)\b',
            'mobile': r'\b(android|ios|react native|flutter|xamarin|swift|kotlin)\b',
            'soft_skills': r'\b(leadership|communication|teamwork|problem solving|analytical|creative|management|agile|scrum)\b'
        }
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using pdfplumber"""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
        return text
    
    def extract_text_from_docx(self, docx_path: str) -> str:
        """Extract text from DOCX"""
        text = ""
        try:
            doc = docx.Document(docx_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            print(f"Error reading DOCX {docx_path}: {e}")
        return text
    
    def extract_skills_comprehensive(self, text: str) -> List[str]:
        """Extract skills using comprehensive patterns"""
        text_lower = text.lower()
        found_skills = set()  # Use set to avoid duplicates
        
        # Apply each skill category pattern
        for category, pattern in self.skill_patterns.items():
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                # Clean up the match and add to skills
                skill = match.strip().title()
                if skill.lower() in ['r', 'js']:  # Special cases
                    skill = skill.upper()
                elif skill.lower() == 'node.js':
                    skill = 'Node.js'
                elif skill.lower() == 'c++':
                    skill = 'C++'
                elif skill.lower() == 'c#':
                    skill = 'C#'
                found_skills.add(skill)
        
        # Additional manual skill detection
        manual_skills = [
            'Project Management', 'Leadership', 'Team Leadership', 
            'Problem Solving', 'Analytical Thinking', 'Communication',
            'Agile', 'Scrum', 'DevOps', 'CI/CD', 'API Development'
        ]
        
        for skill in manual_skills:
            if skill.lower() in text_lower:
                found_skills.add(skill)
        
        return sorted(list(found_skills))
    
    def extract_experience_detailed(self, text: str) -> str:
        """Extract detailed experience information"""
        # Try to find experience sections
        experience_patterns = [
            r'(?:EXPERIENCE|WORK EXPERIENCE|EMPLOYMENT|PROFESSIONAL EXPERIENCE)(.*?)(?=EDUCATION|SKILLS|PROJECTS|CERTIFICATIONS|$)',
            r'(?:WORK HISTORY|CAREER HISTORY|EMPLOYMENT HISTORY)(.*?)(?=EDUCATION|SKILLS|PROJECTS|$)'
        ]
        
        for pattern in experience_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                experience_text = match.group(1)
                # Clean and limit the text
                experience_text = re.sub(r'\s+', ' ', experience_text.strip())
                return experience_text[:800]  # Increased limit for more context
        
        # Fallback: look for job titles and companies
        job_title_pattern = r'\b(?:Senior|Lead|Principal|Manager|Director|Developer|Engineer|Analyst|Specialist|Coordinator)\s+\w+'
        titles = re.findall(job_title_pattern, text, re.IGNORECASE)
        
        if titles:
            return f"Roles include: {', '.join(titles[:3])}. " + text[:400]
        
        return text[:600]  # Return more text for better analysis
    
    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """Enhanced parsing function"""
        try:
            if file_path.endswith('.pdf'):
                text = self.extract_text_from_pdf(file_path)
            elif file_path.endswith('.docx'):
                text = self.extract_text_from_docx(file_path)
            else:
                raise ValueError("Unsupported file format")
            
            if not text or len(text.strip()) < 50:
                raise ValueError("Could not extract meaningful text from file")
            
            # Extract comprehensive information
            skills = self.extract_skills_comprehensive(text)
            experience = self.extract_experience_detailed(text)
            
            return {
                'raw_text': text,
                'skills': skills,
                'experience': experience,
                'file_path': file_path,
                'filename': os.path.basename(file_path),
                'text_length': len(text),
                'skills_count': len(skills)
            }
            
        except Exception as e:
            print(f"Error parsing resume {file_path}: {e}")
            return {
                'raw_text': '',
                'skills': [],
                'experience': 'Could not extract experience information',
                'file_path': file_path,
                'filename': os.path.basename(file_path),
                'text_length': 0,
                'skills_count': 0
            }
