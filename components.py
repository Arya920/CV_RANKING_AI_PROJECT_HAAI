import streamlit as st
import re

def extract_rating(text: str) -> int:
    match = re.search(r'Rating:\s*(\d+)/10', text)
    return int(match.group(1)) if match else 0

def extract_name(filename: str) -> str:
    # Extract name without extension and format nicely
    name_part = filename.split('.')[0].replace("_", " ").title()
    name_parts = name_part.strip().split()
    return " ".join(name_parts[:2]) if len(name_parts) >= 2 else name_part

def card(name: str, explanation: str, skill_info: dict = None, aggregate_score: float = None):
    # Safe extraction
    try:
        rating = extract_rating(explanation or "")
    except Exception:
        rating = 0

    skill_score = 0.0
    if isinstance(skill_info, dict):
        try:
            skill_score = float(skill_info.get("final_match_score", 0.0))
        except Exception:
            skill_score = 0.0

    # Split explanation content properly, fallback to whole explanation
    conclusion_text = ""
    if explanation and isinstance(explanation, str):
        if "Conclusion:" in explanation:
            conclusion_text = explanation.split("Conclusion:")[-1].strip()
        else:
            conclusion_text = explanation.strip()

    # Normalize bullet formatting
    bullets = re.split(r'•|\n-', conclusion_text) if conclusion_text else []
    bullets = [b.strip("• \n-") for b in bullets if b.strip()]

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
