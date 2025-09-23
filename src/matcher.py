from typing import Dict, Any, List
import requests
import re
import random

class CandidateMatcher:
    def __init__(self):
        self.skill_categories = {
            'programming': ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 'go'],
            'web_frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'express'],
            'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes'],
            'tools': ['git', 'jenkins', 'jira', 'linux', 'windows'],
            'data_science': ['pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'tableau'],
            'soft_skills': ['leadership', 'communication', 'teamwork', 'problem solving', 'project management']
        }
    
    def categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """Categorize skills by type"""
        categorized = {category: [] for category in self.skill_categories}
        
        for skill in skills:
            skill_lower = skill.lower()
            for category, category_skills in self.skill_categories.items():
                if any(cat_skill in skill_lower for cat_skill in category_skills):
                    categorized[category].append(skill)
                    break
        
        return categorized
    
    def analyze_experience_level(self, resume_text: str) -> Dict[str, Any]:
        """Analyze experience level from resume text"""
        text_lower = resume_text.lower()
        
        # Count experience indicators
        years_mentioned = len(re.findall(r'\b\d+\s*(?:\+|\-|\s)*years?\b', text_lower))
        job_titles = len(re.findall(r'\b(?:senior|lead|principal|manager|director|architect)\b', text_lower))
        companies = len(re.findall(r'\b(?:inc|corp|ltd|llc|company|technologies)\b', text_lower))
        
        # Estimate experience level
        experience_score = min(100, (years_mentioned * 15) + (job_titles * 20) + (companies * 10))
        
        level = "Entry Level"
        if experience_score >= 80:
            level = "Senior Level"
        elif experience_score >= 50:
            level = "Mid Level"
        
        return {
            'score': experience_score,
            'level': level,
            'years_mentioned': years_mentioned,
            'senior_titles': job_titles
        }
    
    def generate_detailed_feedback(self, resume_data: Dict[str, Any], job_requirements: Dict[str, Any], match_scores: Dict[str, int]) -> Dict[str, str]:
        """Generate personalized feedback for each candidate"""
        
        resume_skills = [skill.lower().strip() for skill in resume_data.get('skills', [])]
        required_skills = [skill.lower().strip() for skill in job_requirements.get('required_skills', [])]
        
        # Find specific matches and gaps
        matched_skills = []
        missing_skills = []
        
        for req_skill in required_skills:
            found_match = False
            for resume_skill in resume_skills:
                if req_skill in resume_skill or resume_skill in req_skill:
                    matched_skills.append(req_skill.title())
                    found_match = True
                    break
            
            if not found_match:
                missing_skills.append(req_skill.title())
        
        # Categorize skills
        resume_categorized = self.categorize_skills(resume_data.get('skills', []))
        
        # Analyze experience
        experience_analysis = self.analyze_experience_level(resume_data.get('raw_text', ''))
        
        # Generate personalized strengths
        strengths = []
        
        if match_scores['skills_score'] >= 80:
            strengths.append(f"Excellent technical fit with {len(matched_skills)} key skills matching: {', '.join(matched_skills[:4])}.")
        elif match_scores['skills_score'] >= 60:
            strengths.append(f"Good technical foundation with skills in: {', '.join(matched_skills[:3])}.")
        elif match_scores['skills_score'] >= 30:
            strengths.append(f"Some relevant skills including: {', '.join(matched_skills[:2])}.")
        else:
            strengths.append("Basic qualifications present.")
        
        # Add specific skill category strengths
        for category, skills in resume_categorized.items():
            if skills and category != 'soft_skills':
                if len(skills) >= 3:
                    strengths.append(f"Strong {category.replace('_', ' ')} expertise ({len(skills)} skills).")
                elif len(skills) >= 1:
                    strengths.append(f"Experience with {category.replace('_', ' ')}: {', '.join(skills[:2])}.")
        
        # Add experience-based strengths
        if experience_analysis['score'] >= 70:
            strengths.append(f"{experience_analysis['level']} candidate with solid professional background.")
        elif experience_analysis['senior_titles'] > 0:
            strengths.append("Leadership experience indicated by senior role titles.")
        
        # Generate personalized gaps
        gaps = []
        
        if missing_skills:
            if len(missing_skills) <= 2:
                gaps.append(f"Would benefit from developing: {', '.join(missing_skills)}.")
            else:
                gaps.append(f"Key areas for development: {', '.join(missing_skills[:3])} and {len(missing_skills)-3} others.")
        
        if match_scores['experience_score'] < 60:
            gaps.append("Could benefit from more industry-specific experience.")
        
        if match_scores['skills_score'] < 50:
            gaps.append("Significant skill development needed to meet job requirements.")
        
        # Add specific improvement suggestions
        weak_categories = [cat for cat, skills in resume_categorized.items() if not skills and cat != 'soft_skills']
        if weak_categories:
            gaps.append(f"Consider strengthening {weak_categories[0].replace('_', ' ')} skills.")
        
        if not gaps:
            gaps.append("Strong overall profile with minimal gaps identified.")
        
        return {
            'strengths': ' '.join(strengths),
            'gaps': ' '.join(gaps)
        }
    
    def calculate_match_simple(self, resume_data: Dict[str, Any], job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced simple matching with detailed feedback"""
        
        resume_skills = [skill.lower().strip() for skill in resume_data.get('skills', [])]
        required_skills = [skill.lower().strip() for skill in job_requirements.get('required_skills', [])]
        resume_text = resume_data.get('raw_text', '').lower()
        
        # Enhanced skills matching
        direct_matches = set()
        partial_matches = set()
        
        # Skill mapping for better matching
        skill_mappings = {
            'javascript': ['js', 'node', 'react', 'angular'],
            'python': ['django', 'flask', 'pandas'],
            'sql': ['mysql', 'postgresql', 'database'],
            'machine learning': ['ml', 'ai', 'tensorflow', 'pytorch'],
            'aws': ['amazon web services', 'ec2', 's3'],
            'docker': ['containerization', 'containers']
        }
        
        for req_skill in required_skills:
            # Direct match
            if req_skill in resume_skills:
                direct_matches.add(req_skill)
                continue
            
            # Partial match in text
            if req_skill in resume_text:
                partial_matches.add(req_skill)
                continue
            
            # Check skill mappings
            for main_skill, variants in skill_mappings.items():
                if req_skill == main_skill:
                    for variant in variants:
                        if variant in resume_text or any(variant in rs for rs in resume_skills):
                            partial_matches.add(req_skill)
                            break
        
        total_matches = len(direct_matches | partial_matches)
        skills_score = min(100, int((total_matches / max(1, len(required_skills))) * 100)) if required_skills else 60
        
        # Experience analysis
        experience_analysis = self.analyze_experience_level(resume_text)
        experience_score = experience_analysis['score']
        
        # Overall score calculation
        overall_score = int((skills_score * 0.6) + (experience_score * 0.4))
        
        # Prepare match scores for feedback generation
        match_scores = {
            'skills_score': skills_score,
            'experience_score': experience_score,
            'overall_score': overall_score
        }
        
        # Generate detailed, personalized feedback
        feedback = self.generate_detailed_feedback(resume_data, job_requirements, match_scores)
        
        return {
            'filename': resume_data.get('filename', 'Unknown'),
            'skills_score': skills_score,
            'experience_score': experience_score,
            'overall_score': overall_score,
            'strengths': feedback['strengths'],
            'gaps': feedback['gaps']
        }
    
    def calculate_match_with_llm(self, resume_data: Dict[str, Any], job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """LLM-based matching with enhanced prompting"""
        
        try:
            # Prepare detailed candidate profile
            candidate_skills = resume_data.get('skills', [])[:8]
            candidate_text = resume_data.get('experience', '')[:400]
            filename = resume_data.get('filename', 'Unknown')
            
            # Prepare job requirements
            job_skills = job_requirements.get('required_skills', [])[:8]
            job_experience = job_requirements.get('experience', '')
            
            # Enhanced prompt for better analysis
            prompt = f"""Analyze this specific candidate for the job role:

CANDIDATE: {filename}
Technical Skills: {', '.join(candidate_skills)}
Experience Summary: {candidate_text}

JOB REQUIREMENTS:
Required Skills: {', '.join(job_skills)}
Experience Needed: {job_experience}

Provide a detailed, personalized analysis:

SKILLS_SCORE: [0-100 - rate technical skill match]
EXPERIENCE_SCORE: [0-100 - rate experience level match]
OVERALL_SCORE: [0-100 - overall job fit]
STRENGTHS: [Specific strengths of THIS candidate - mention actual skills/experience they have]
GAPS: [Specific areas THIS candidate needs to improve - be specific about missing skills]

Focus on what makes THIS candidate unique. Be specific and detailed about their individual profile."""

            payload = {
                "model": "llama3.1:8b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,  # Lower temperature for more consistent analysis
                    "max_tokens": 400,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=20
            )
            
            if response.status_code != 200:
                raise Exception(f"API call failed with status {response.status_code}")
            
            result_text = response.json().get('response', '')
            
            if not result_text or len(result_text.strip()) < 50:
                raise Exception("LLM response too short or empty")
            
            # Parse LLM response
            match_result = {
                'filename': filename,
                'skills_score': 50,
                'experience_score': 50,
                'overall_score': 50,
                'strengths': 'LLM analysis completed',
                'gaps': 'Review feedback above'
            }
            
            lines = result_text.split('\n')
            for line in lines:
                line = line.strip()
                
                if line.startswith('SKILLS_SCORE:'):
                    try:
                        score = int(re.search(r'\d+', line).group())
                        match_result['skills_score'] = min(100, max(0, score))
                    except:
                        pass
                
                elif line.startswith('EXPERIENCE_SCORE:'):
                    try:
                        score = int(re.search(r'\d+', line).group())
                        match_result['experience_score'] = min(100, max(0, score))
                    except:
                        pass
                
                elif line.startswith('OVERALL_SCORE:'):
                    try:
                        score = int(re.search(r'\d+', line).group())
                        match_result['overall_score'] = min(100, max(0, score))
                    except:
                        pass
                
                elif line.startswith('STRENGTHS:'):
                    text = line.split(':', 1)[1].strip()
                    if text and len(text) > 10:
                        match_result['strengths'] = text
                
                elif line.startswith('GAPS:'):
                    text = line.split(':', 1)[1].strip()
                    if text and len(text) > 10:
                        match_result['gaps'] = text
            
            # Validate that we got meaningful results
            if (match_result['strengths'] == 'LLM analysis completed' or 
                len(match_result['strengths']) < 20):
                raise Exception("LLM didn't provide detailed feedback")
            
            return match_result
            
        except Exception as e:
            print(f"LLM matching failed for {resume_data.get('filename', 'Unknown')}: {e}")
            return self.calculate_match_simple(resume_data, job_requirements)
