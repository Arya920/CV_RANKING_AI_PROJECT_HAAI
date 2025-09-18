from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load pre-trained SBERT model (or choose any other suitable model)
model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_skills_from_resume(resume_data):
    """
    Extract the technical skills from the parsed resume.
    Args:
        resume_data (dict): Parsed resume JSON.
    Returns:
        list: List of technical skills.
    """
    return resume_data["result"].get("Technical Skills", [])

def extract_skills_from_jd(jd_data):
    """
    Extract the skills required from the parsed job description.
    Args:
        jd_data (dict): Parsed JD JSON.
    Returns:
        list: List of required skills.
    """
    return jd_data.get("Skills Required", [])

def calculate_skills_match(resume_skills, jd_skills):
    """
    Calculate semantic match percentage between resume skills and JD skills using SBERT.
    Args:
        resume_skills (list): List of skills from the resume.
        jd_skills (list): List of skills from the JD.
    Returns:
        float: Match percentage between 0-100.
    """
    # Embed skills using SBERT
    resume_embeddings = model.encode(resume_skills)
    jd_embeddings = model.encode(jd_skills)

    # Calculate cosine similarity between all JD and resume skill pairs
    similarities = cosine_similarity(jd_embeddings, resume_embeddings)

    # Find the best match for each JD skill
    matches = []
    for i in range(len(jd_skills)):
        best_match_idx = similarities[i].argmax()
        best_match_score = similarities[i][best_match_idx]
        matches.append(best_match_score)

    # Calculate the average similarity score as a match percentage
    if len(matches) > 0:
        avg_match_percentage = (sum(matches) / len(matches)) * 100
    else:
        avg_match_percentage = 0  # No matches

    return avg_match_percentage

def calculate_exact_match(jd_skills, resume_skills):
    """
    Calculate the exact match percentage between resume skills and JD skills.
    Args:
        jd_skills (list): List of skills from the JD.
        resume_skills (list): List of skills from the resume.
    Returns:
        float: Exact match percentage between 0-100.
    """
    jd_skills_set = set(jd_skills)
    resume_skills_set = set(resume_skills)

    exact_matches = jd_skills_set.intersection(resume_skills_set)
    exact_match_percentage = (len(exact_matches) / len(jd_skills_set)) * 100 if len(jd_skills_set) > 0 else 0

    return exact_match_percentage

def calculate_final_skills_match(jd_skills, resume_skills):
    """
    Combine exact match and semantic match to calculate final match score.
    Args:
        jd_skills (list): List of skills from the JD.
        resume_skills (list): List of skills from the resume.
    Returns:
        float: Combined match percentage between 0-100.
    """
    exact_match = calculate_exact_match(jd_skills, resume_skills)
    semantic_match = calculate_skills_match(resume_skills, jd_skills)

    # Weight the exact and semantic match (can be adjusted based on preference)
    final_match_percentage = (exact_match * 0.4) + (semantic_match * 0.6)

    return final_match_percentage

# Main function to process resumes and JD
def process_resume_and_jd(resume_data, jd_data):
    """
    Process a resume and a job description, calculate skill matching score.
    Args:
        resume_data (dict): Parsed resume JSON.
        jd_data (dict): Parsed JD JSON.
    Returns:
        dict: Final match score and explanation.
    """
    # Extract skills from both resume and JD
    resume_skills = extract_skills_from_resume(resume_data)
    jd_skills = extract_skills_from_jd(jd_data)

    # Calculate the final skills match percentage
    final_match_score = calculate_final_skills_match(jd_skills, resume_skills)
    final_match_score = float(final_match_score)
    
    # You can also use the SBERT model to generate a more detailed explanation if needed
    explanation = f"Skills match: {final_match_score:.2f}% (combination of exact and semantic matching)"

    return {
        "final_match_score": final_match_score,
        "explanation": explanation
    }

# Example usage:

# Parse resume and JD (This is just an example; replace with actual parsed data)
# resume_data = {
#   "result": {
#     "Technical Skills": [
#       "R", "Python", "SQL","ML", "Hadoop", "Hive", "Tableau", "Git", "AWS", "SPSS", "SAS","Natural Language Processing"
#     ]
#   }
# }

# jd_data = {
#   "Skills Required": [
#     "Python", "R", "Machine Learning", "Data Science", "Hadoop", "AWS", "SQL", "NLP"
#   ]
# }

# # Process the resume and JD
# result = process_resume_and_jd(resume_data, jd_data)

# print(result)
