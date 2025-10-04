"""
Streamlit front-end for AstraMatch (resume ↔ job-description matcher).

This module provides the Streamlit UI and orchestration for uploading
resumes and a job description, invoking text extraction, structured
extraction (NuMind), similarity matching, and a local LLM-based ranker.

Key behaviors:
- The NuMind API key must be provided in the sidebar at runtime.
- Resumes may be PDF or DOCX. Extraction functions return empty strings
    on failure and the UI will skip files with no extractable text.
- All user-visible errors are handled and presented as warnings/messages
    in the Streamlit UI; exceptions are not propagated to end users.
"""

import streamlit as st
import os
import json
from datetime import datetime
import time

from text_extractor import extract_text_from_pdf, extract_text_from_txt
from structured_data_extractor import extract_resume_data, extract_jd_data
from structured_data_extractor import set_numind_api_key
from ranker import get_rank_from_ollama
from similarity_checking import process_resume_and_jd
from components import card, extract_rating

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
    /* Header styles */
    .headerTitle {
        color: #0f172a; /* slate-900 */
        font-weight: 700;
        font-size: 2.1rem;
        margin: 0;
        letter-spacing: -0.5px;
        font-family: Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
    }

    .tagline {
        color: #475569; /* slate-500 */
        font-size: 1.05rem;
        margin-top: 0.4rem;
        margin-bottom: 1.6rem;
        line-height: 1.45;
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
    st.markdown("""
    <div style='text-align: center;'>
      <h1 class='headerTitle'>AstraMatch</h1>
      <p class='tagline'>Precision candidate matching — fast, private, and tailored to your job requirements.</p>
    </div>
    """, unsafe_allow_html=True)

# --- Sidebar: NuMind API Key ---
with st.sidebar.expander("NuMind API Key (required for structured extraction)", expanded=True):
    st.write("Provide your NuMind API key so the app can call the extraction API.\nYou can paste the key or upload a small .txt file containing the key.")
    api_key_input = st.text_input("Paste NuMind API Key", value="", type="password")
    api_key_file = st.file_uploader("Or upload a .txt file with the key", type=["txt"], key="api_key_file")

    api_key_set = False
    if api_key_file is not None:
        try:
            api_key_candidate = api_key_file.getvalue().decode('utf-8').strip()
            if api_key_candidate:
                api_key_set = set_numind_api_key(api_key_candidate)
        except Exception:
            api_key_set = False

    if api_key_input:
        api_key_set = set_numind_api_key(api_key_input)

    if api_key_set:
        st.success("NuMind API key configured")
        st.session_state.numind_configured = True
    else:
        st.info("NuMind API key not configured. Structured extraction will be disabled until you provide a key.")
        st.session_state.numind_configured = False

    # Debug toggle
    debug_mode = st.checkbox("Show debug logs (verbose)", value=False)
    st.session_state.debug_mode = bool(debug_mode)

# --- File Upload Section ---
st.markdown("""<div class="stCard">""", unsafe_allow_html=True)

# Create three columns for better spacing
col1, col2, col3 = st.columns([1, 0.2, 1])

with col1:
    st.markdown("""<div class="uploadSection">""", unsafe_allow_html=True)
    st.markdown("### 📄 Resume Upload")
    st.markdown("Upload up to 10 resumes in PDF format")
    resumes = st.file_uploader(
        "Choose resume files",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        help="Maximum 5 resumes allowed"
    )
    if resumes:
        st.info(f"📁 {len(resumes)} resume(s) uploaded")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("""<div class="uploadSection">""", unsafe_allow_html=True)
    st.markdown("### 📝 Job Description")
    
    jd_text = None
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
if resumes and len(resumes) > 10:
    st.warning("You can upload a maximum of 10 resumes.")
    resumes = resumes[:10]

# Initialize the application class
class DocumentProcessor:
    """Small helper class to encapsulate resume and JD processing.

    This class keeps helper methods together so the UI code is easier to
    follow and unit-testable. Methods do not raise errors to the UI; they
    return None on failure which the caller treats as a skipped file.
    """
    def __init__(self):
        """Initialize a DocumentProcessor.

        Attributes:
            max_resumes (int): maximum number of resumes to process.
        """
        self.max_resumes = 10
        
    def process_resume(self, resume_file):
        """Extract plain text and structured data from a single resume file.

        Inputs:
            resume_file: a Streamlit uploaded file-like object with `.name`.

        Behavior:
            - Detects PDF vs DOCX by filename suffix and dispatches to the
              appropriate extractor.
            - Returns a dict with keys 'filename', 'text', and 'extracted'
              on success. Returns None on any failure so the UI can skip it.
        """
        try:
            # Choose extractor by file extension
            name_lower = getattr(resume_file, 'name', '').lower()
            # reset file pointer before reading
            try:
                resume_file.seek(0)
            except Exception:
                pass

            if name_lower.endswith('.pdf'):
                try:
                    text = extract_text_from_pdf(resume_file)
                except Exception as e:
                    st.warning(f"⚠️ Skipped {getattr(resume_file, 'name', 'unknown')} - PDF extraction error: {e}")
                    return None
            elif name_lower.endswith('.docx'):
                try:
                    from text_extractor import extract_text_from_docx
                    text = extract_text_from_docx(resume_file)
                except RuntimeError as e:
                    # Missing python-docx dependency
                    st.warning(f"⚠️ Skipped {getattr(resume_file, 'name', 'unknown')} - DOCX extraction not available: {e}")
                    return None
                except Exception as e:
                    st.warning(f"⚠️ Skipped {getattr(resume_file, 'name', 'unknown')} - DOCX extraction error: {e}")
                    return None
            else:
                st.warning(f"⚠️ Skipped {getattr(resume_file, 'name', 'unknown')} - Unsupported file type")
                return None

            if not text or not str(text).strip():
                st.warning(f"⚠️ Skipped {getattr(resume_file, 'name', 'unknown')} - No extractable text found in the file.")
                return None

            # Call structured extractor
            try:
                result = extract_resume_data(text)
            except Exception as e:
                st.warning(f"⚠️ Skipped {getattr(resume_file, 'name', 'unknown')} - Structured extraction raised an error: {e}")
                return None

            # If extraction returned an error dict, show it to the user
            if isinstance(result, dict) and result.get('error'):
                st.warning(f"⚠️ Skipped {getattr(resume_file, 'name', 'unknown')} - {result.get('error')}")
                # show raw result in debug mode
                if st.session_state.get('debug_mode'):
                    st.debug(result)
                return None

            # Show debug info when enabled
            if st.session_state.get('debug_mode'):
                try:
                    snippet = (text[:500] + '...') if len(text) > 500 else text
                    st.info(f"Debug: Extracted text snippet for {getattr(resume_file, 'name', 'unknown')}:\n{snippet}")
                except Exception:
                    pass
                try:
                    st.info(f"Debug: Structured extraction output for {getattr(resume_file, 'name', 'unknown')}: {str(result)[:1000]}")
                except Exception:
                    pass

            # Success
            return {
                "filename": resume_file.name,
                "text": text,
                "extracted": result
            }
        except Exception as e:
            return None

    def process_jd(self, jd_text: str):
        """Process the provided job description text via NuMind.

        The function expects raw JD text and returns a dict with extracted
        fields or None if processing failed. The NuMind wrapper may return
        a dict with an `error` key; in that case this function returns None
        to indicate failure to the caller.

        Returned dict keys on success:
            - text: the raw JD text
            - experience: extracted experience requirement or a default string
            - skills: list of extracted skills
            - raw_data: the full structured output from NuMind
        """
        try:
            jd_data = extract_jd_data(jd_text)

            # jd_data may be a dict with 'error' or an object with .result
            if isinstance(jd_data, dict):
                if jd_data.get('error'):
                    return None
                # If dict contains 'result' mapping, use it
                jd_result = jd_data.get('result', jd_data)
            else:
                # obj-like
                jd_result = getattr(jd_data, 'result', None)

            if not jd_result:
                return None

            return {
                "text": jd_text,
                "experience": jd_result.get('Experience Required', "Not provided"),
                "skills": jd_result.get('Skills Required', []),
                "raw_data": jd_result
            }
        except Exception as e:
            # Swallow errors and return None so the UI can show a friendly message
            return None

processor = DocumentProcessor()

# Analysis Section
analyze_col1, analyze_col2, analyze_col3 = st.columns([1, 2, 1])
with analyze_col2:
    analyze_button = st.button(
        "🚀 Analyze and Rank Candidates",
        help="Start the analysis process",
        use_container_width=True
    )

if analyze_button:
    # Ensure NuMind is configured before running extraction
    if not st.session_state.get('numind_configured', False):
        st.warning("Provide the NuMind API Key in the sidebar before analyzing.")
    elif not resumes:
        st.error("⚠️ Please upload at least one resume to analyze.")
    elif not jd_text or not str(jd_text).strip():
        st.error("⚠️ Please provide a job description for analysis.")
    else:
        # Progress bar and status
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Initialize counters
        total_steps = len(resumes) + 3
        current_step = 0
        rankings = []
        
        try:
            # Process resumes
            extracted_resumes = []
            status_text.text("📂 Processing resumes...")
            
            for i, resume in enumerate(resumes[:processor.max_resumes]):
                try:
                    resume_data = processor.process_resume(resume)
                    if resume_data:
                        extracted_resumes.append(resume_data)
                    else:
                        st.warning(f"⚠️ Skipped {resume.name} - Could not process PDF.")
                except Exception as e:
                    st.warning(f"⚠️ Error processing {resume.name}")
                    continue
                
                current_step = i + 1
                progress_bar.progress(current_step / total_steps)
                status_text.text(f"📂 Processing resume {i+1} of {len(resumes)}")
            
            if not extracted_resumes:
                st.error("❌ No valid resumes could be processed.")
                st.stop()
            
            # Process job description
            try:
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                status_text.text("📄 Processing job description...")
                
                jd_result = processor.process_jd(jd_text)
                if not jd_result:
                    st.error("❌ Failed to process job description.")
                    st.stop()
                
                jd_experience = jd_result["experience"]
                jd_skills = jd_result["skills"]
                st.session_state.jd_experience = jd_experience
                
            except Exception as e:
                st.error("❌ Error processing job description.")
                st.stop()
            
            # Rank candidates
            current_step += 1
            progress_bar.progress(current_step / total_steps)
            status_text.text("🧠 Analyzing candidates...")
            
            for resume_data in extracted_resumes:
                try:
                    result_data = resume_data["extracted"].result if hasattr(resume_data["extracted"], 'result') else {}
                    
                    experience = result_data.get("Experience", "Not provided")
                    name = result_data.get("name", resume_data["filename"])
                    resume_skills = result_data.get("Technical Skills", [])
                    
                    response = get_rank_from_ollama(
                        experience=experience,
                        jd=jd_experience
                    )
                    
                    skill_match_result = {}
                    skill_score_out_of_100 = 0
                    
                    if jd_skills:
                        try:
                            skill_match_result = process_resume_and_jd(resume_skills, jd_skills)
                            # process_resume_and_jd returns keys 'final_match_score' and 'score'
                            if isinstance(skill_match_result, dict):
                                skill_score_out_of_100 = skill_match_result.get("score", skill_match_result.get("final_match_score", 0))
                                # ensure final_match_score key exists for UI
                                if "final_match_score" not in skill_match_result:
                                    skill_match_result["final_match_score"] = skill_score_out_of_100
                            else:
                                # unexpected return type
                                skill_match_result = {"final_match_score": 0.0, "explanation": "Unexpected skill matcher output"}
                                skill_score_out_of_100 = 0
                        except Exception as e:
                            # Log and continue gracefully
                            import logging
                            logging.exception(f"Skill matching failed for {name}: {e}")
                            st.warning(f"⚠️ Error matching skills for {name}")
                            skill_match_result = {"final_match_score": 0.0, "explanation": "Error computing skill match", "error": str(e)}
                            skill_score_out_of_100 = 0
                    
                    experience_score = extract_rating(response) * 10
                    aggregate_score = (experience_score * 0.4) + (skill_score_out_of_100 * 0.6)
                    
                    rankings.append({
                        "name": name,
                        "score_and_explanation": response,
                        "skill_match_result": skill_match_result,
                        "aggregate_score": aggregate_score
                    })
                except Exception as e:
                    st.warning(f"⚠️ Error analyzing candidate {resume_data['filename']}")
                    continue
            
            if not rankings:
                st.error("❌ No candidates could be ranked.")
                st.stop()
            
            rankings.sort(key=lambda x: x["aggregate_score"], reverse=True)
            
            progress_bar.progress(1.0)
            st.success("✅ Analysis completed successfully!")
            
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
            # After rendering the final output to the UI, persist a human-readable
            # summary to a local file named `output.txt` in the project root.
            try:
                output_path = os.path.join(os.getcwd(), "output.txt")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write("AstraMatch - Analysis Output\n")
                    f.write("Final Rankings:\n")
                    for i, rank in enumerate(rankings, start=1):
                        f.write(f"{i}. Name: {rank.get('name')}\n")
                        f.write(f"   Aggregate Score: {rank.get('aggregate_score')}\n")
                        # Skill match summary
                        skill_info = rank.get('skill_match_result') or {}
                        final_score = skill_info.get('final_match_score', skill_info.get('score', 'N/A'))
                        f.write(f"   Skill Match Score: {final_score}\n")
                        explanation = skill_info.get('explanation') or skill_info.get('message') or ''
                        if explanation:
                            f.write(f"   Skill Match Explanation: {explanation}\n")
                        # Include the LLM's score/explanation block
                        sa = rank.get('score_and_explanation')
                        if sa:
                            # sa might be an object or string; coerce to string safely
                            try:
                                sa_text = str(sa)
                            except Exception:
                                sa_text = "(unavailable)"
                            f.write(f"   Experience Rating / Explanation:\n{sa_text}\n")
                        f.write("\n")
                st.success(f"✅ Results saved to output.txt")
            except Exception as e:
                st.warning(f"⚠️ Could not save results to disk: {e}")
                
        except Exception as e:
            st.error("❌ An unexpected error occurred during analysis.")
            st.stop()

