# app.py

import streamlit as st
import os
import json
from datetime import datetime
import time

from core.text_extraction_from_pdf import extract_text_from_pdf, extract_text_from_txt
from core.structured_data_extractor import extract_resume_data, extract_jd_data
from core.ranker import get_rank_from_ollama
from core.similarity_checking import process_resume_and_jd
from ui.components import card, extract_rating

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="Smart Resume-JD Matcher",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main container styling */
    .main > div {
        padding: 2rem 3rem;
    }
    
    /* Card-like containers */
    .stCard {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
    }
    
    /* Headers and text */
    h1 {
        color: #1a237e;
        font-weight: 600;
        margin-bottom: 1.5rem;
    }
    
    .subtitle {
        color: #424242;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* File upload area */
    .uploadSection {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #1a237e;
        color: white;
        padding: 0.5rem 2rem;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #283593;
    }
</style>
""", unsafe_allow_html=True)

# Header Section
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("🎯 Smart Resume & JD Matcher")
    st.markdown(
        """<p class='subtitle'>
        Transform your hiring process with AI-powered resume screening. 
        Upload resumes and job descriptions to find the perfect match.
        </p>""", 
        unsafe_allow_html=True
    )

# --- File Upload Section ---
st.markdown("""<div class="stCard">""", unsafe_allow_html=True)

# Create three columns for better spacing
col1, col2, col3 = st.columns([1, 0.2, 1])

with col1:
    st.markdown("""<div class="uploadSection">""", unsafe_allow_html=True)
    st.markdown("### 📄 Resume Upload")
    st.markdown("Upload up to 5 resumes in PDF format")
    resumes = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        help="Maximum 5 resumes allowed"
    )
    if resumes:
        st.info(f"📁 {len(resumes)} resume(s) uploaded")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("""<div class="uploadSection">""", unsafe_allow_html=True)
    st.markdown("### 📝 Job Description")
    
    jd_option = st.radio(
        "Choose input method:",
        ("Upload a file", "Write your own JD"),
        key="jd_input_method"
    )

    if jd_option == "Upload a file":
        jd_file = st.file_uploader(
            "Upload TXT file",
            type=["txt"],
            help="Upload job description in text format"
        )
        if jd_file:
            with st.spinner("Processing job description..."):
                jd_text = extract_text_from_txt(jd_file)
                if not jd_text.strip():
                    st.error("❌ Failed to extract text from job description.")
                    st.stop()
                else:
                    st.success("✅ Job description processed")
    else:
        st.markdown("Enter your job description below:")
        jd_text = st.text_area(
            "Job Description",
            height=200,
            placeholder="Enter the complete job description here...",
            help="Include key requirements, responsibilities, and qualifications"
        )
        if jd_text.strip():
            st.success("✅ Job description received")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Add a divider and analyze button section
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("""<div class="stCard" style="text-align: center;">""", unsafe_allow_html=True)

# Limit resumes to 5
if resumes and len(resumes) > 5:
    st.warning("You can upload a maximum of 5 resumes.")
    resumes = resumes[:5]

# Analysis Section
analyze_col1, analyze_col2, analyze_col3 = st.columns([1, 2, 1])
with analyze_col2:
    analyze_button = st.button(
        "🚀 Analyze and Rank Candidates",
        help="Start the analysis process",
        use_container_width=True
    )

if analyze_button:
    if not resumes:
        st.error("⚠️ Please upload at least one resume to analyze.")
    elif not jd_text:
        st.error("⚠️ Please provide a job description for analysis.")
    else:
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Initialize counters
        total_steps = len(resumes) + 3  # Resumes + JD + Analysis + Ranking
        current_step = 0
        
        # Spinner: Resume Extraction
        extracted_resumes = []
        status_text.text("📂 Processing resumes...")
        progress_bar.progress(current_step / total_steps)
        for i, resume in enumerate(resumes):
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
            
            # Update progress
            current_step = i + 1
            progress_bar.progress(current_step / total_steps)
            status_text.text(f"📂 Processing resume {i+1} of {len(resumes)}...")

        # Extract JD data and save it to session
        current_step += 1
        progress_bar.progress(current_step / total_steps)
        status_text.text("📄 Processing job description...")
        
        jd_data = extract_jd_data(jd_text)
        if hasattr(jd_data, 'error'):
            st.error("❌ Failed to extract job description data.")
            st.stop()

        # Extract JD Skills and Experience
        jd_experience = jd_data.result.get('Experience Required', "Not provided")
        jd_skills = jd_data.result.get('Skills Required', [])
        
        # Show extracted JD info in an expander
        with st.expander("📋 Job Description Analysis"):
            st.markdown("### Key Requirements")
            if jd_skills:
                st.write("**Required Skills:**")
                st.write(", ".join(jd_skills))
            if jd_experience != "Not provided":
                st.write("**Required Experience:**")
                st.write(jd_experience)
        
        st.session_state.extracted_jd = jd_data.result
        st.session_state.jd_experience = jd_experience

        print(f"JD Experience: {st.session_state.jd_experience}")
        print(f"JD Skills: {jd_skills}")

        if not extracted_resumes:
            st.error("❌ No valid resumes extracted.")
            st.stop()

        # Save resumes to session
        st.session_state.extracted_resumes = extracted_resumes

        # Ranking via LLM
        rankings = []
        current_step += 1
        progress_bar.progress(current_step / total_steps)
        status_text.text("🧠 Analyzing candidates...")
        
        for i, r in enumerate(st.session_state.extracted_resumes):
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

        # ✅ Final progress update
        current_step += 1
        progress_bar.progress(1.0)
        st.success("✅ All resumes ranked successfully!")

        time.sleep(1)
        progress_bar.empty()
        status_text.empty()

        st.header("🏆 Final Candidate Rankings")
        for rank in rankings:
            card(
                rank["name"],
                rank["score_and_explanation"],
                skill_info=rank["skill_match_result"],
                aggregate_score=rank["aggregate_score"]
            )

