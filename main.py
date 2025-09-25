import streamlit as st
from parser import parse_job_description, parse_resume_with_llm, extract_text_from_pdf
from matcher import compute_similarity, llm_match_score, init_llm, init_hf_llm
from ranker import rank_candidates
import time
import altair as alt

def draw_line():
    st.markdown(
        """
        <hr style="border:1px solid #FF4B4B; margin: 20px 0;">
        """,
        unsafe_allow_html=True
    )

def summarize_results(df):
    best_candidate = df.iloc[0]['Candidate']
    avg_fit = df['Overall Fit (0 - 10)'].mean()
    top3 = ", ".join(df.head(3)['Candidate'].tolist())
    return (
        f"📌 Average fit score: {avg_fit:.2f}\n"
        f"🏆 Best candidate: {best_candidate}\n"
        f"🔝 Top 3 candidates: {top3}"
    )

# Session State variables
# if 'RANK_CLICK' not in st.session_state:
#     st.session_state.RANK_CLICK  = False
if 'RANKED_RESULTS' not in st.session_state:
    st.session_state.RANKED_RESULTS  = None
if 'LLM_SWITCH' not in st.session_state:
    st.session_state.LLM_SWITCH  = True
if 'LAST_RANK_CLICK' not in st.session_state:
    st.session_state.LAST_RANK_CLICK  = False

col1, col2, col3 = st.columns([0.1,1,0.1])
with col2:
    st.title("📄 CV Ranking using LLMs")
st.markdown(
    """
    <hr style="border:2px solid #FF4B4B; margin: 20px 0;">
    """,
    unsafe_allow_html=True
)
st.markdown("##### **:red[Upload Multiple CV / Resumes - ]**")

uploaded_resumes = st.file_uploader("", type=["pdf", "docx"], accept_multiple_files=True)

draw_line()
st.markdown("##### **:red[Provide Job Description - ]**")
jd_input_mode = st.radio(
    "Choose how you want to enter JD:",
    ("Text", "Upload PDF")
)
if jd_input_mode == "Text":
    job_description = st.text_area("Paste job description")
elif jd_input_mode == "Upload PDF":
    jd_file = st.file_uploader("Upload job description", type=["pdf"])
    if jd_file is not None:
        job_description = extract_text_from_pdf(jd_file)
        st.write(job_description)
draw_line()
    

# Initialize LLM (Ollama with Llama 3 8B)
# llm = init_hf_llm("microsoft/Phi-3-mini-4k-instruct")


# if st.button("Run Sorting") and uploaded_resumes and job_description:

col1, col2, col3 = st.columns([0.7,1,0.1])
with col2:
    run_sorting = st.button("🚀 Rank CVs")



if run_sorting and job_description and uploaded_resumes and st.session_state.LLM_SWITCH:
    start_time = time.time()
    st.session_state.LAST_RANK_CLICK = False
    with st.spinner(" Processing... This may take a few minutes."):

        llm = init_llm(model_name="nuextract")
        jd_structured = parse_job_description(job_description, llm=llm)
        # st.text_area("Structured JD", value=str(jd_structured), height=200)
        results = []
        for file in uploaded_resumes:
            resume_data = parse_resume_with_llm(file, llm=llm)
            resume_text = " ".join(str(v) for v in resume_data.values() if v)
            print(resume_text)
            # st.text_area("Resume", value=str(resume_data), height=200)

            similarity = compute_similarity(resume_text, job_description)
            llm_result = llm_match_score(resume_data, jd_structured, llm=llm)
            print(llm_result)

            results.append({
                "Candidate": resume_data.get("name", file.name),
                "Name": resume_data.get("Name", file.name),
                "Similarity": similarity,
                "Overall Fit (0 - 10)": llm_result.get("overall_fit", similarity),
                "Explanation": llm_result.get("explanation", "N/A")
            })
        st.session_state.RANKED_RESULTS = rank_candidates(results)
        st.session_state.LAST_RANK_CLICK = True
    end_time = time.time()

if run_sorting and not st.session_state.LLM_SWITCH:
    st.session_state.LAST_RANK_CLICK = False
    candidates_data = [
        {
            "Candidate name": "Alice Johnson",
            "Similarity score": 0.82,
            "overall_fit": 0.85,
            "Explanation": "Strong experience in required technologies and relevant domain knowledge."
        },
        {
            "Candidate name": "Brian Smith",
            "Similarity score": 0.76,
            "overall_fit": 0.70,
            "Explanation": "Good technical skills but limited experience in leadership roles."
        },
         {
            "Candidate name": "Catherine Lee",
            "Similarity score": 0.91,
            "overall_fit": 0.92,
            "Explanation": "Excellent overall match with significant project management expertise."
        },
        {
            "Candidate name": "David Patel",
            "Similarity score": 0.68,
            "overall_fit": 0.65,
            "Explanation": "Moderate skill alignment, lacks direct experience in target industry."
        },
        {
            "Candidate name": "Emma Garcia",
            "Similarity score": 0.88,
            "overall_fit": 0.90,
            "Explanation": "Highly relevant experience and certifications make her a strong fit."
        }
    ]
    df = rank_candidates(candidates_data, by = "overall_fit")
    st.session_state.RANKED_RESULTS = df
    st.session_state.LAST_RANK_CLICK = True

if st.session_state.LAST_RANK_CLICK and not st.session_state.LLM_SWITCH:
    st.markdown("### 📊 CV Match Report")
    st.info("ℹ️ The below table lists all the candidates in decreasing order of their match. You can interactively sort, search & filter any column by clicking on the column header.")
    st.dataframe(st.session_state.RANKED_RESULTS)
    st.download_button("📥 Download dummy Report", st.session_state.RANKED_RESULTS.to_csv(index=False), "results.csv", "text/csv")
    toast = st.toast("✅ CVs ranked successful !")
    time.sleep(2)
    toast.empty()

if st.session_state.LAST_RANK_CLICK and st.session_state.LLM_SWITCH:
    st.markdown("### 📊 CV Match Report")
    st.info("ℹ️ The below table lists all the candidates in decreasing order of their match. You can interactively sort, search & filter any column by clicking on the column header.")
    st.dataframe(st.session_state.RANKED_RESULTS)
    st.download_button("📥 Download Report", st.session_state.RANKED_RESULTS.to_csv(index=False), "results.csv", "text/csv")

    chart = alt.Chart(st.session_state.RANKED_RESULTS).mark_bar().encode(
    x='Candidate',
    y='Overall Fit (0 - 10)',
    tooltip=['Candidate','Overall Fit (0 - 10)','Explanation']
    )
    st.altair_chart(chart, use_container_width=True)

    st.write(summarize_results(st.session_state.RANKED_RESULTS))

    toast = st.toast("✅ CVs ranked successful !")
    time.sleep(2)
    toast.empty()
    st.write(f"⏱️ Time taken: {(end_time - start_time)/60:.4f} minutes")

