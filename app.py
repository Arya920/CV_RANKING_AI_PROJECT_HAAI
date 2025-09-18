# app.py

import streamlit as st
import os
import json
from datetime import datetime

from core.text_extraction_from_pdf import extract_text_from_pdf, extract_text_from_txt
from core.structured_data_extractor import extract_resume_data, extract_jd_data
from core.ranker import get_rank_from_ollama
from core.similarity_checking import process_resume_and_jd
from ui.components import card, extract_rating

# --- Streamlit Page Config ---
st.set_page_config(page_title="Smart Resume-JD Matcher", layout="centered")
st.title("🤖 Smart Resume & JD Matcher")

st.markdown("""
<style>
    .stExpander > div > div {
        background-color: #1f2937 !important;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(
    """
    Upload multiple **resumes (PDF)** and one **job description (TXT)**.  
    Our local AI engine will extract, analyze, and rank the best candidates.
    """,
    help="Supports up to 5 PDF resumes and one job description in .txt format."
)

# --- File Upload ---
with st.container():
    col1, col2 = st.columns(2)

    with col1:
        resumes = st.file_uploader("📄 Upload Resumes", type=["pdf"], accept_multiple_files=True)

    with col2:
        # --- Job Description Input --- 
        jd_option = st.radio(
            "Choose Job Description Input Method",
            ("Upload a file", "Write your own JD")
        )

        if jd_option == "Upload a file":
            jd_file = st.file_uploader("📝 Upload Job Description", type=["txt"])
            if jd_file:
                # JD extraction when file is uploaded
                with st.spinner("📄 Extracting JD..."):
                    jd_text = extract_text_from_txt(jd_file)
                    if not jd_text.strip():
                        st.error("❌ Failed to extract text from JD.")
                        st.stop()
        elif jd_option == "Write your own JD":
            jd_text = st.text_area("📝 Write your Job Description Here", height=300)
            if not jd_text.strip():
                st.warning("Please write a Job Description to proceed.")

# Limit resumes to 5
if resumes and len(resumes) > 5:
    st.warning("You can upload a maximum of 5 resumes.")
    resumes = resumes[:5]

# --- Single Button ---
if st.button("🚀 Analyze and Rank Candidates"):
    print("starting analysis...")
    if not resumes:
        st.error("Please upload at least one resume.")
    elif not jd_text:
        st.error("Please upload a job description.")
    else:
        # Spinner: Resume Extraction
        extracted_resumes = []
        with st.spinner("📂 Extracting resumes and running NuExtract..."):
            for resume in resumes:
                text = extract_text_from_pdf(resume)
                if not text.strip():
                    st.warning(f"⚠️ Skipped {resume.name} - Empty or failed PDF.")
                    continue

                result = extract_resume_data(text)
                extracted_resumes.append({
                    "filename": resume.name,
                    "text": text,
                    "extracted": result
                })

        # Extract JD data and save it to session
        with st.spinner("📄 Extracting JD Data..."):
            jd_data = extract_jd_data(jd_text)
            if hasattr(jd_data, 'error'):
                st.error("❌ Failed to extract JD data.")
                st.stop()

        # Extract JD Skills and Experience
        jd_experience = jd_data.result.get('Experience Required', "Not provided")
        jd_skills = jd_data.result.get('Skills Required', [])
        
        st.session_state.extracted_jd = jd_data.result
        st.session_state.jd_experience = jd_experience

        print(f"JD Experience: {st.session_state.jd_experience}")
        print(f"JD Skills: {jd_skills}")

        if not extracted_resumes:
            st.error("❌ No valid resumes extracted.")
            st.stop()

        # Save resumes to session
        st.session_state.extracted_resumes = extracted_resumes

        # Spinner: Ranking via LLM
        rankings = []
        with st.spinner("🧠 Running Ollama model for ranking..."):
            for r in st.session_state.extracted_resumes:
                extracted_data = r["extracted"]
                result_data = extracted_data.result if hasattr(extracted_data, 'result') else {}

                # Extract experience from resume
                experience = result_data.get("Experience", "Not provided")
                name = extracted_data.result.get("name", r["filename"])

                # Call Ollama model (pass only experience data)
                response = get_rank_from_ollama(
                    experience=experience,
                    jd=st.session_state.jd_experience
                )
                print(f"Response for {name}: {response}")

                # Extract skills from resume to compute similarity
                resume_skills = result_data.get("Technical Skills", [])

                # Check if JD skills are missing or empty before calling process_resume_and_jd
                if jd_skills:
                    # Call the function to get skill match similarity
                    skill_match_result = process_resume_and_jd(
                        {"result": {"Technical Skills": resume_skills}},
                        {"Skills Required": jd_skills}
                    )
                    print(f"Skill Match for {name}: {skill_match_result}")
                    skill_score_out_of_100 = skill_match_result["final_match_score"]
                else:
                    skill_match_result = {"final_match_score": 0, "explanation": "No JD skills provided."}
                    skill_score_out_of_100 = 0

                # Extract experience score (already out of 10)
                experience_score = extract_rating(response) *10

                # Combine into aggregate score (give more weight to skills)
                aggregate_score = (experience_score * 0.4) + (skill_score_out_of_100 * 0.6)
                

                # Store ranking
                rankings.append({
                    "name": name,
                    "score_and_explanation": response,
                    "skill_match_result": skill_match_result,
                    "aggregate_score": aggregate_score
                })


        # Sort and Display Rankings
        # Sort and Display Rankings by aggregate score
        rankings.sort(key=lambda x: x["aggregate_score"], reverse=True)

        st.success("✅ All resumes ranked successfully!")

        st.header("🏆 Final Candidate Rankings")
        for rank in rankings:
            card(
                rank["name"],
                rank["score_and_explanation"],
                skill_info=rank["skill_match_result"],
                aggregate_score=rank["aggregate_score"]
            )

