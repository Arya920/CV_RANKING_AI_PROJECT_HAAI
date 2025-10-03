import logging
from typing import List, Union, Dict, Any

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


# This module provides helper utilities for extracting skill lists from
# structured outputs and computing a combined skill-match score using
# semantic embeddings (SBERT) with a safe fallback to exact matching.
# The functions are defensive: they return numeric scores and never raise
# (they log exceptions and fall back where appropriate).

# Load pre-trained SBERT model (or set to None if loading fails)
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    logger.warning(f"Failed to load SentenceTransformer model: {e}")
    model = None


def _ensure_skill_list(x: Union[List[str], Dict[str, Any], None]) -> List[str]:
    """
    Normalize a variety of possible skill representations into a list of strings.

    Accepts:
      - list[str]: returned as a cleaned list
      - dict (NuMind-like): will try common keys such as 'result' -> {'Technical Skills': [...]}
      - dict (JD-like): will check for 'Skills Required'
      - None: returns []

    The function is defensive and attempts a best-effort conversion.
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
    """Return a normalized list of skills extracted from resume data.

    Input can be a parsed resume dict, a list of skills, or raw text.
    """
    return _ensure_skill_list(resume_data)


def extract_skills_from_jd(jd_data: Union[List[str], Dict[str, Any]]):
    """Return a normalized list of required skills from a job description.

    Input may be a dict with key 'Skills Required' or a simple list.
    """
    return _ensure_skill_list(jd_data)


def calculate_skills_match(resume_skills: List[str], jd_skills: List[str]) -> float:
    """
    Compute a semantic match percentage between resume skills and JD skills.

    Uses SBERT embeddings and cosine similarity to compute how well each JD
    skill maps to the resume skill set. Returns a percentage in [0, 100].

    If the SBERT model is not available or an error occurs, the function
    falls back to `calculate_exact_match`.
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
    """
    Calculate the exact-match percentage between JD skills and resume skills.

    All comparisons are lower-cased and stripped to reduce trivial mismatches.
    Returns a float percentage in [0, 100].
    """
    jd_skills_set = set([s.lower().strip() for s in (jd_skills or []) if s])
    resume_skills_set = set([s.lower().strip() for s in (resume_skills or []) if s])

    if not jd_skills_set:
        return 0.0

    exact_matches = jd_skills_set.intersection(resume_skills_set)
    exact_match_percentage = (len(exact_matches) / len(jd_skills_set)) * 100

    return exact_match_percentage


def calculate_final_skills_match(jd_skills: List[str], resume_skills: List[str]) -> float:
    """
    Combine exact-match and semantic-match scores into a single final percentage.

    Default weights: exact 40% and semantic 60% (tunable).
    """
    exact_match = calculate_exact_match(jd_skills, resume_skills)
    semantic_match = calculate_skills_match(resume_skills, jd_skills)

    # Weight the exact and semantic match (can be adjusted based on preference)
    final_match_percentage = (exact_match * 0.4) + (semantic_match * 0.6)

    return final_match_percentage


def process_resume_and_jd(resume_data: Union[List[str], Dict[str, Any]], jd_data: Union[List[str], Dict[str, Any]]):
    """
    Top-level helper to take resume and JD inputs (various shapes), compute
    the final skills match percentage, and return a small result dict.

    Returns:
      {"final_match_score": float, "explanation": str, "score": float}

    This function never raises; on error it logs the exception and returns
    a zeroed score with an explanatory message.
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
