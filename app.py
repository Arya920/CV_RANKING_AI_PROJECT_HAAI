import streamlit as st
import os
import json
from text_extractor import extract_text_from_pdf, extract_text_from_txt
from extractor import extract_resume_data
from ollama_ranker import get_rank_from_ollama
from datetime import datetime

st.set_page_config(page_title="Resume & JD Analyzer", layout="centered")
st.title("📄 Resume & JD Information Extractor and Ranker")


# Upload multiple resumes (max 5)
resumes = st.file_uploader(
    "Upload Resumes (PDF, up to 5)",
    type=["pdf"],
    accept_multiple_files=True
)

if len(resumes) > 5:
    st.warning("Please upload maximum 5 resumes only.")
    resumes = resumes[:5]

# Upload single Job Description TXT
jd_file = st.file_uploader("Upload Job Description (JD) (TXT)", type=["txt"])

# Initialize session state keys if not present
if "extracted_resumes" not in st.session_state:
    st.session_state.extracted_resumes = []

if "extracted_jd" not in st.session_state:
    st.session_state.extracted_jd = None

# ANALYZE BUTTON
if st.button("Analyze"):
    if not resumes:
        st.error("Please upload at least one Resume.")
    elif not jd_file:
        st.error("Please upload the Job Description (JD).")
    else:
        st.info("Extracting and processing resumes...")

        # Extract JD text
        jd_text = extract_text_from_txt(jd_file)
        if not jd_text.strip():
            st.error("Failed to extract text from JD TXT file.")
        else:
            st.session_state.extracted_jd = jd_text
            st.success("JD text extracted.")

        # Extract each resume
        extracted_resumes = []
        for idx, resume in enumerate(resumes, 1):
            st.info(f"Extracting Resume {idx}: {resume.name}")
            text = extract_text_from_pdf(resume)
            if not text.strip():
                st.warning(f"Resume {resume.name} extraction failed.")
                continue
            result = extract_resume_data(text)
            extracted_resumes.append({
                "filename": resume.name,
                "text": text,
                "extracted": result
            })
            st.success(f"Resume {resume.name} extracted.")

        st.session_state.extracted_resumes = extracted_resumes

        # Save JSON files for resumes
        os.makedirs("data", exist_ok=True)
        for r in extracted_resumes:
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{r['filename'].replace(' ', '_')}.json"
            with open(os.path.join("data", filename), "w", encoding="utf-8") as f:
                json.dump(r["extracted"].model_dump(), f, indent=2)
        st.success("All extracted resume data saved to the 'data/' folder.")

# Display extracted resumes if present in session state
if st.session_state.extracted_resumes:
    st.header("Extracted Resume Data")
    for r in st.session_state.extracted_resumes:
        st.subheader(f"{r['filename']}")
        st.json(r["extracted"])

# Display extracted JD if present
if st.session_state.extracted_jd:
    st.header("Extracted Job Description Text")
    st.text_area("JD Text", st.session_state.extracted_jd, height=200)

if st.session_state.extracted_resumes and st.session_state.extracted_jd:
    if st.button("Find Rank"):
        st.info("Ranking resumes based on JD...")
        rankings = []
        for r in st.session_state.extracted_resumes:
            extracted_data = r["extracted"].model_dump()
            result_data = extracted_data.get("result", {})
            experience = result_data.get("Experience", "Not provided")
            skills = result_data.get("Technical Skills", "Not provided")

            print("experience Info:",experience)
            print("skills Info:", skills)

            # prompt = (
            #             "You are a hiring assistant. Based on the candidate's experience and technical skills, "
            #             "and the job description below, give a score out of 10 for job fit and provide a short explanation.\n\n"
            #             "Format your answer strictly as:\n"
            #             "Rating: <number>/10\n"
            #             "Conclusion: <5 crisp factual bullet points, OR 1-2 short sentences covering exactly 5 key facts>\n\n"
            #             f"Resume:\nExperience: {experience}\n\nTechnical Skills: {skills}\n\n"
            #             f"Job Description:\n{st.session_state.extracted_jd}"
            #         )


            response = get_rank_from_ollama(experience=experience, skills=skills, jd=st.session_state.extracted_jd)

            name = extracted_data.get("name", r["filename"])

            rankings.append({
                "name": name,
                "score_and_explanation": response
            })

        st.header("Ranking Results")
        for rank in rankings:
            st.subheader(rank["name"])
            st.write(rank["score_and_explanation"])
