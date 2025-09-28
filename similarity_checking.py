import logging
from typing import List, Union, Dict, Any

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Load pre-trained SBERT model (or choose any other suitable model)
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    logger.warning(f"Failed to load SentenceTransformer model: {e}")
    model = None


def _ensure_skill_list(x: Union[List[str], Dict[str, Any], None]) -> List[str]:
    """Normalize input to a list of skill strings.

    Accepts:
      - list of strings (returned as-is)
      - dict with keys like 'result' -> {'Technical Skills': [...]}
      - dict with 'Technical Skills' at top-level
      - None -> []
    """
    if not x:
        return []
    # If already a list of strings
    if isinstance(x, list):
        return [str(s).strip() for s in x if s]
    # If dict-like, try several common shapes
    if isinstance(x, dict):
        # NuMind outputs often put parsed fields under 'result'
        if 'result' in x and isinstance(x['result'], dict):
            return [str(s).strip() for s in x['result'].get('Technical Skills', []) if s]
        # Direct mapping
        if 'Technical Skills' in x:
            return [str(s).strip() for s in x.get('Technical Skills', []) if s]
        # If a JD-like dict
        if 'Skills Required' in x:
            return [str(s).strip() for s in x.get('Skills Required', []) if s]
    # Fallback: try to coerce to string and split by commas
    try:
        text = str(x)
        parts = [p.strip() for p in text.split(',') if p.strip()]
        return parts
    except Exception:
        return []


def extract_skills_from_resume(resume_data: Union[List[str], Dict[str, Any]]):
    """Extract the technical skills from the parsed resume or accept a skill list."""
    return _ensure_skill_list(resume_data)


def extract_skills_from_jd(jd_data: Union[List[str], Dict[str, Any]]):
    """Extract skills required from JD or accept a skill list."""
    return _ensure_skill_list(jd_data)


def calculate_skills_match(resume_skills: List[str], jd_skills: List[str]) -> float:
    """Calculate semantic match percentage between resume skills and JD skills using SBERT.

    Returns a score between 0 and 100. Handles empty lists and model errors gracefully.
    """
    # Normalize inputs
    resume_skills = [s for s in (resume_skills or []) if s]
    jd_skills = [s for s in (jd_skills or []) if s]

    if not resume_skills or not jd_skills:
        return 0.0

    if model is None:
        logger.warning("SBERT model not available, falling back to exact matching only.")
        # Fall back to simple exact match percentage
        return calculate_exact_match(jd_skills, resume_skills)

    try:
        # Embed skills using SBERT
        resume_embeddings = model.encode(resume_skills, convert_to_numpy=True)
        jd_embeddings = model.encode(jd_skills, convert_to_numpy=True)

        # Ensure embeddings have correct shape
        if len(resume_embeddings) == 0 or len(jd_embeddings) == 0:
            return 0.0

        # Calculate cosine similarity between all JD and resume skill pairs
        similarities = cosine_similarity(jd_embeddings, resume_embeddings)

        # Find the best match for each JD skill
        matches = []
        for i in range(similarities.shape[0]):
            best_match_score = float(similarities[i].max())
            matches.append(best_match_score)

        # Calculate the average similarity score as a match percentage
        avg_match_percentage = (sum(matches) / len(matches)) * 100 if matches else 0.0
        return avg_match_percentage
    except Exception as e:
        logger.exception(f"Error during semantic skill matching: {e}")
        # On error, fall back to exact matching
        return calculate_exact_match(jd_skills, resume_skills)


def calculate_exact_match(jd_skills: List[str], resume_skills: List[str]) -> float:
    """Calculate the exact match percentage between resume skills and JD skills."""
    jd_skills_set = set([s.lower().strip() for s in (jd_skills or []) if s])
    resume_skills_set = set([s.lower().strip() for s in (resume_skills or []) if s])

    if not jd_skills_set:
        return 0.0

    exact_matches = jd_skills_set.intersection(resume_skills_set)
    exact_match_percentage = (len(exact_matches) / len(jd_skills_set)) * 100

    return exact_match_percentage


def calculate_final_skills_match(jd_skills: List[str], resume_skills: List[str]) -> float:
    """Combine exact match and semantic match to calculate final match score."""
    exact_match = calculate_exact_match(jd_skills, resume_skills)
    semantic_match = calculate_skills_match(resume_skills, jd_skills)

    # Weight the exact and semantic match (can be adjusted based on preference)
    final_match_percentage = (exact_match * 0.4) + (semantic_match * 0.6)

    return final_match_percentage


def process_resume_and_jd(resume_data: Union[List[str], Dict[str, Any]], jd_data: Union[List[str], Dict[str, Any]]):
    """Process a resume and a job description, calculate skill matching score.

    Accepts either parsed dicts (with 'result' etc.) or raw lists of skills.
    Returns a dictionary with final_match_score and explanation. Never raises.
    """
    try:
        # Extract skills from both resume and JD
        resume_skills = extract_skills_from_resume(resume_data)
        jd_skills = extract_skills_from_jd(jd_data)

        # Calculate the final skills match percentage
        final_match_score = calculate_final_skills_match(jd_skills, resume_skills)
        final_match_score = float(final_match_score)

        explanation = f"Skills match: {final_match_score:.2f}% (combination of exact and semantic matching)"

        return {
            "final_match_score": final_match_score,
            "explanation": explanation,
            "score": final_match_score  # keep legacy 'score' key for compatibility
        }
    except Exception as e:
        logger.exception(f"Unhandled error in process_resume_and_jd: {e}")
        return {"final_match_score": 0.0, "explanation": "Error computing skill match", "error": str(e), "score": 0.0}

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
