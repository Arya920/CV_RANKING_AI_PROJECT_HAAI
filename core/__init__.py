# core/__init__.py

from .ranker import get_rank_from_ollama
from .text_extraction_from_pdf import extract_text_from_pdf, extract_text_from_txt
from .structured_data_extractor import extract_resume_data, extract_jd_data  # if this is a helper function
from .similarity_checking import (
    extract_skills_from_resume,
    extract_skills_from_jd,
    calculate_skills_match,
    calculate_exact_match
)
# Optional: If there are global configurations or common imports, you can include them here.
