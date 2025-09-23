import re
from typing import Dict, List
import requests
import time

class JobDescriptionParser:
    def __init__(self):
        self.connection_cache = {'tested': False, 'connected': False}
        
    def test_ollama_connection(self) -> bool:
        """Test Ollama connection with caching"""
        if self.connection_cache['tested']:
            return self.connection_cache['connected']
        
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            connected = response.status_code == 200
        except:
            connected = False
        
        self.connection_cache = {'tested': True, 'connected': connected}
        return connected
    
    def extract_requirements_simple(self, job_description: str) -> Dict:
        """Enhanced keyword-based extraction"""
        
        # Comprehensive skill lists
        technical_skills = [
            # Programming languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin',
            # Web technologies  
            'html', 'css', 'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'spring',
            # Databases
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 'nosql',
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform', 'ansible',
            # Data & ML
            'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'spark', 'hadoop', 'tableau',
            # Tools
            'git', 'jira', 'confluence', 'slack', 'linux', 'windows', 'bash', 'powershell'
        ]
        
        soft_skills = [
            'communication', 'leadership', 'teamwork', 'problem solving', 'analytical', 'creative',
            'management', 'presentation', 'agile', 'scrum', 'project management', 'collaboration',
            'mentoring', 'coaching', 'strategic thinking', 'decision making', 'adaptability',
            'time management', 'organizational', 'interpersonal', 'negotiation', 'customer service'
        ]
        
        job_text = job_description.lower()
        
        # Find skills with context
        found_skills = []
        
        # Check for technical skills
        for skill in technical_skills:
            patterns = [
                rf'\b{re.escape(skill)}\b',
                rf'\b{re.escape(skill)}\.js\b',
                rf'\b{re.escape(skill)}\.py\b'
            ]
            for pattern in patterns:
                if re.search(pattern, job_text, re.IGNORECASE):
                    found_skills.append(skill.title())
                    break
        
        # Check for soft skills
        for skill in soft_skills:
            if re.search(rf'\b{re.escape(skill)}\b', job_text, re.IGNORECASE):
                found_skills.append(skill.title())
        
        # Remove duplicates while preserving order
        found_skills = list(dict.fromkeys(found_skills))
        
        # Extract experience with multiple patterns
        experience = "Not specified"
        exp_patterns = [
            r'(\d+)[\+\-\s]*(?:to\s+\d+\s+)?years?\s+(?:of\s+)?experience',
            r'(\d+)\+?\s*years?\s+experience',
            r'minimum\s+(\d+)\s+years?',
            r'at\s+least\s+(\d+)\s+years?',
            r'(\d+)\s*-\s*\d+\s+years?'
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, job_text)
            if match:
                years = match.group(1)
                experience = f"{years}+ years required"
                break
        
        # Extract education
        education = "Not specified"
        if re.search(r'bachelor[\'s]*|b\.?s\.?|b\.?a\.?|undergraduate|degree', job_text):
            education = "Bachelor's degree"
        if re.search(r'master[\'s]*|m\.?s\.?|m\.?a\.?|graduate', job_text):
            education = "Master's degree preferred"
        if re.search(r'phd|ph\.?d\.?|doctorate', job_text):
            education = "PhD preferred"
        
        # Extract responsibilities
        responsibilities = []
        resp_patterns = [
            r'(?:responsibilities|duties|role|tasks):\s*(.{100,500})',
            r'you will[:\s]+(.{100,500})',
            r'responsibilities include[:\s]+(.{100,500})'
        ]
        
        for pattern in resp_patterns:
            match = re.search(pattern, job_description, re.IGNORECASE | re.DOTALL)
            if match:
                resp_text = match.group(1)
                # Split into individual responsibilities
                items = re.split(r'[•\-\*\n]\s*', resp_text)
                responsibilities = [item.strip().strip(',').strip('.') 
                                 for item in items if len(item.strip()) > 20][:4]
                break
        
        if not responsibilities:
            responsibilities = ["Perform duties as outlined in job description"]
        
        return {
            'required_skills': found_skills[:10],  # Top 10 skills
            'experience': experience,
            'education': education,
            'responsibilities': responsibilities
        }
    
    def extract_requirements_with_llm(self, job_description: str) -> Dict:
        """Extract using LLM with proper error handling"""
        
        if not self.test_ollama_connection():
            print("Ollama not connected, using simple extraction")
            return self.extract_requirements_simple(job_description)
        
        try:
            # Direct API call for reliability
            prompt = f"""Extract key information from this job description:

{job_description[:1500]}

Provide a structured analysis:

REQUIRED_SKILLS: List 6-8 most important technical and soft skills mentioned
EXPERIENCE: Years of experience required (be specific)  
EDUCATION: Education requirements
RESPONSIBILITIES: Key job duties (3-4 items)

Be concise and focus on clearly stated requirements."""

            payload = {
                "model": "llama3.1:8b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            }
            
            response = requests.post(
                "http://localhost:11434/api/generate", 
                json=payload, 
                timeout=15
            )
            
            if response.status_code != 200:
                raise Exception(f"API returned {response.status_code}")
            
            result_text = response.json().get('response', '')
            
            if not result_text or len(result_text.strip()) < 20:
                raise Exception("Empty or too short response")
            
            # Parse response
            requirements = {
                'required_skills': [],
                'experience': 'Not specified',
                'education': 'Not specified', 
                'responsibilities': []
            }
            
            lines = result_text.split('\n')
            for line in lines:
                line = line.strip()
                
                if line.startswith('REQUIRED_SKILLS:'):
                    skills_text = line.split(':', 1)[1].strip()
                    skills = [s.strip() for s in skills_text.split(',') if s.strip()]
                    requirements['required_skills'] = skills[:8]
                    
                elif line.startswith('EXPERIENCE:'):
                    requirements['experience'] = line.split(':', 1)[1].strip()
                    
                elif line.startswith('EDUCATION:'):
                    requirements['education'] = line.split(':', 1)[1].strip()
                    
                elif line.startswith('RESPONSIBILITIES:'):
                    resp_text = line.split(':', 1)[1].strip()
                    resp_items = [s.strip() for s in resp_text.split(',') if s.strip()]
                    requirements['responsibilities'] = resp_items[:4]
            
            # Validate results
            if len(requirements['required_skills']) < 2:
                raise Exception("Insufficient skills extracted")
            
            return requirements
            
        except Exception as e:
            print(f"LLM extraction failed: {e}, falling back to simple extraction")
            return self.extract_requirements_simple(job_description)
