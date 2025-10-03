# Importing all the required Python packages and modules
import streamlit as st
from parser import parse_job_description, parse_resume_with_llm, extract_text_from_pdf
from matcher import compute_similarity, llm_match_score, init_llm, init_hf_llm
from ranker import rank_candidates
import time
import altair as alt
import warnings

# Suppressing warnings for cleaner output
warnings.filterwarnings("ignore")

# Streamlit function for drawing a horizontal line
def draw_line():
    st.markdown(
        """
        <hr style="border:1px solid #FF4B4B; margin: 20px 0;">
        """,
        unsafe_allow_html=True
    )
# Function to summarize results and provide high level statistics
def summarize_results(df):
    best_candidate = df.iloc[0]['Candidate']
    avg_fit = df['Overall Fit'].mean()
    top3 = ", ".join(df.head(3)['Candidate'].tolist())
    return (
        f"📌 Average fit score: {avg_fit:.2f}\n"
        f"🏆 Best candidate: {best_candidate}\n"
        f"🔝 Top 3 candidates: {top3}"
    )

# Function to compute overall fit score as a weighted average of various LLM metrics
def compute_overall_fit(similarity, result):
    """Compute overall fit as a weighted average of similarity, skills, experience match and LLM overall_fit."""
    similarity_weight = 0.5
    skills_weight = 0.2
    experience_weight = 0.2
    overall_weight = 0.1
    return (result.get("skills_match", 0.2) * skills_weight) + (result.get("experience_match", 0.2) * experience_weight) + (similarity * similarity_weight) + (result.get("overall_fit", 0.2) * overall_weight)


# Streamlit Session State variables - required to maintain state across user interactions
if 'RANKED_RESULTS' not in st.session_state:
    st.session_state.RANKED_RESULTS  = None
if 'LLM_SWITCH' not in st.session_state:
    st.session_state.LLM_SWITCH  = True
if 'LAST_RANK_CLICK' not in st.session_state:
    st.session_state.LAST_RANK_CLICK  = False
if 'start_time' not in st.session_state:
    st.session_state.start_time  = None
if 'end_time' not in st.session_state:
    st.session_state.end_time  = None


# Streamlit App UI code starts here
col1, col2, col3 = st.columns([0.1,1,0.1])
with col2:
    st.title("📄 CV Ranking using LLMs")
st.markdown(
    """
    <hr style="border:2px solid #FF4B4B; margin: 20px 0;">
    """,
    unsafe_allow_html=True
)
# Streamlit code for resume file uploaders and browser 
st.markdown("##### **:red[Upload Multiple CV / Resumes - ]**")
uploaded_resumes = st.file_uploader("", type=["pdf", "docx"], accept_multiple_files=True)
draw_line()
# Streamlit code for Job Description input (text area or PDF upload)
st.markdown("##### **:red[Provide Job Description - ]**")
jd_input_mode = st.radio(
    "Choose how you want to enter JD:",
    ("Text", "Upload PDF")
)
if jd_input_mode == "Text":
    job_description = st.text_area("Paste job description", "")
elif jd_input_mode == "Upload PDF":
    jd_file = st.file_uploader("Upload job description", type=["pdf"])
    if jd_file is not None:
        job_description = extract_text_from_pdf(jd_file)
draw_line()
# Streamlit code for 'Run' button and ranking logic
col1, col2, col3 = st.columns([0.7,1,0.1])
with col2:
    run_sorting = st.button("🚀 Rank CVs")

# Initialize LLMs and run the ranking logic when 'Run' button is clicked and the resumes have been uploaded and job description has been specified
if run_sorting and job_description and uploaded_resumes and st.session_state.LLM_SWITCH:
    st.session_state.start_time = time.time()
    st.session_state.LAST_RANK_CLICK = False
    with st.spinner(" Processing... This may take a few minutes."):
        # Using Nuextract LLM for parsing and matching
        llm = init_llm(model_name="nuextract")
        jd_structured = parse_job_description(job_description, llm=llm)
        results = []
        for file in uploaded_resumes:
            resume_data = parse_resume_with_llm(file, llm=llm)
            resume_text = " ".join(str(v) for v in resume_data.values() if v)
            # Compute overall similarity score using sentence-transformers/all-MiniLM-L6-v2
            similarity = compute_similarity(resume_text, job_description)
            # Get detailed aspect based fit score and explanation from the LLM nuextract
            llm_result = llm_match_score(resume_data, jd_structured, llm=llm)
            print(llm_result)
            # Bundle the results for each resume in a list of dictionaries to convert to a dataframe later
            results.append({
                "Candidate": resume_data.get("name", file.name),
                "Name": resume_data.get("Name", file.name),
                "Similarity": similarity,
                "Skills Match": llm_result.get("skills_match", similarity),
                "Experience Match": llm_result.get("experience_match", similarity),
                "Overall Fit": compute_overall_fit(similarity, llm_result),
                "Explanation": llm_result.get("explanation", "N/A")
            })
        st.session_state.RANKED_RESULTS = rank_candidates(results)
        st.session_state.LAST_RANK_CLICK = True
    st.session_state.end_time = time.time()
    toast = st.toast("✅ CVs ranked successful !")
    time.sleep(2)
    toast.empty()


if st.session_state.LAST_RANK_CLICK and st.session_state.LLM_SWITCH:
    draw_line()
    st.markdown("### 📊 CV Match Report")
    st.info("ℹ️ The below table lists all the candidates in decreasing order of their match. You can interactively sort, search & filter any column by clicking on the column header.")
    st.dataframe(st.session_state.RANKED_RESULTS)
    st.download_button("📥 Download Report", st.session_state.RANKED_RESULTS.to_csv(index=False), "results.csv", "text/csv")
    draw_line()
    st.markdown("### 📈 Visuals & Summary")
    chart = alt.Chart(st.session_state.RANKED_RESULTS).mark_bar().encode(
    x='Candidate',
    y='Overall Fit',
    tooltip=['Candidate','Overall Fit','Explanation']
    )
    st.altair_chart(chart, use_container_width=True)
    st.write(summarize_results(st.session_state.RANKED_RESULTS))
    st.write(f"⏱️ Time taken: {(st.session_state.end_time - st.session_state.start_time)/60:.4f} minutes")

