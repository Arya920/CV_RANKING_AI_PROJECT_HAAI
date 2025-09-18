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
    rating = extract_rating(explanation)

    skill_score = skill_info["final_match_score"] if skill_info else 0

    # Split explanation content properly
    conclusion_text = ""
    if "Conclusion:" in explanation:
        conclusion_text = explanation.split("Conclusion:")[-1].strip()

    # Normalize bullet formatting
    bullets = re.split(r'•|\n-', conclusion_text)
    bullets = [b.strip("• \n-") for b in bullets if b.strip()]

    with st.container(border=True):
        st.subheader(f"**Candidate Name:** {extract_name(name)}")
        st.markdown(f"**🧠 Experience Rating:** {rating*10:.2f}%")
        st.markdown(f"**🛠️ Skill Match:** {skill_score:.2f}%")

        if aggregate_score is not None:
            st.markdown(f"**🏁 Aggregate Score:** {aggregate_score:.2f}%")

        with st.expander("📌 See Explanation"):
            for bullet in bullets:
                st.markdown(f"- {bullet}")
