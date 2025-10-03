import streamlit as st
import re

# UI helper utilities for rendering candidate cards and extracting simple
# structured information from free-text model outputs. Kept intentionally
# lightweight because they are directly used by the Streamlit frontend.

def extract_rating(text: str) -> int:
    # Parse a rating out of the ranker LLM output.
    # Expected format in text: "Rating: <n>/10"
    # Returns integer rating (0 if not found).
    match = re.search(r'Rating:\s*(\d+)/10', text)
    return int(match.group(1)) if match else 0

def extract_name(filename: str) -> str:
    # Turn a file name into a human-friendly candidate name.
    # Examples: "john_doe_resume.pdf" -> "John Doe"
    # We avoid changing the original filename string itself and only
    # format a short display name for the UI.
    name_part = filename.split('.')[0].replace("_", " ").title()
    name_parts = name_part.strip().split()
    return " ".join(name_parts[:2]) if len(name_parts) >= 2 else name_part

def card(name: str, explanation: str, skill_info: dict = None, aggregate_score: float = None):
    """
    Render a candidate card in the Streamlit UI.

    Parameters
    - name: filename or identifier for the candidate
    - explanation: raw explanation text returned by the ranker LLM
    - skill_info: dict returned by the skill matcher (expects 'final_match_score')
    - aggregate_score: combined numeric score to display

    This function is defensive and will not raise if explanation parsing fails.
    """
    # Safe extraction of the numeric rating from the explanation text.
    try:
        rating = extract_rating(explanation or "")
    except Exception:
        rating = 0

    # Safe extraction of skill match score from skill_info.
    skill_score = 0.0
    if isinstance(skill_info, dict):
        try:
            skill_score = float(skill_info.get("final_match_score", 0.0))
        except Exception:
            skill_score = 0.0

    # Try to obtain a concise 'conclusion' area for display; otherwise show
    # the entire explanation text in the UI expander.
    conclusion_text = ""
    if explanation and isinstance(explanation, str):
        if "Conclusion:" in explanation:
            conclusion_text = explanation.split("Conclusion:")[-1].strip()
        else:
            conclusion_text = explanation.strip()

    # Normalize bullet formatting so the UI shows readable bullets.
    bullets = re.split(r'•|\n-', conclusion_text) if conclusion_text else []
    bullets = [b.strip("• \n-") for b in bullets if b.strip()]

    # Render the card in Streamlit
    with st.container():
        st.subheader(f"Candidate: {extract_name(name)}")
        st.markdown(f"**🧠 Experience Rating:** {rating*10:.2f}%")
        st.markdown(f"**🛠️ Skill Match:** {skill_score:.2f}%")

        if aggregate_score is not None:
            st.markdown(f"**🏁 Aggregate Score:** {aggregate_score:.2f}%")

        if bullets:
            with st.expander("📌 See Explanation"):
                for bullet in bullets:
                    st.markdown(f"- {bullet}")
        else:
            # show the raw explanation if bullets are not available
            with st.expander("📌 Explanation"):
                st.write(explanation or "No explanation available")
