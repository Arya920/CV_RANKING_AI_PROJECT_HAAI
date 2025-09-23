import streamlit as st
import os
import sys
import tempfile
from pathlib import Path
import time
import traceback

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from resume_parser import ResumeParser
from job_parser import JobDescriptionParser
from matcher import CandidateMatcher
import pandas as pd

def main():
    st.set_page_config(page_title="CV Sorting using LLMs", page_icon="📄", layout="wide")
    
    st.title("📄 CV Sorting using LLMs")
    st.markdown("**Automated Resume Ranking System powered by Large Language Models**")
    
    # Initialize components
    @st.cache_resource
    def load_components():
        return ResumeParser(), JobDescriptionParser(), CandidateMatcher()
    
    resume_parser, job_parser, matcher = load_components()
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Instructions")
        st.markdown("""
        1. **Enter Job Description**: Paste the job posting
        2. **Upload Resumes**: Upload PDF or DOCX files  
        3. **Process**: Click to analyze and rank
        4. **Review Results**: See detailed rankings
        5. **Download**: Export as CSV
        """)
        
        st.header("ℹ️ System Status")
        ollama_status = job_parser.test_ollama_connection()
        
        if ollama_status:
            st.success("🟢 Ollama: Connected")
        else:
            st.warning("🟡 Ollama: Offline (using basic analysis)")
        
        # Processing mode
        st.header("⚙️ Settings")
        processing_mode = st.selectbox(
            "Analysis Mode",
            ["Smart Analysis (LLM)", "Fast Analysis (Keywords)"],
            index=0 if ollama_status else 1
        )
        
        debug_mode = st.checkbox("Debug Mode", help="Show detailed processing information")
    
    # Main interface
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("1️⃣ Job Description")
        job_description = st.text_area(
            "Enter job requirements:",
            height=300,
            placeholder="""Example:
Software Developer - Python

Requirements:
- 3+ years Python experience
- Knowledge of Django, Flask
- Experience with SQL databases
- Strong problem-solving skills
- Bachelor's degree preferred

Responsibilities:
- Develop web applications
- Write clean, maintainable code
- Collaborate with team members"""
        )
    
    with col2:
        st.header("2️⃣ Upload Resumes")
        uploaded_files = st.file_uploader(
            "Choose resume files:",
            accept_multiple_files=True,
            type=['pdf', 'docx'],
            help="Upload PDF or DOCX files (max 5MB each)"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} files ready")
            for i, file in enumerate(uploaded_files):
                st.write(f"{i+1}. **{file.name}**")
    
    # Processing
    st.header("3️⃣ Process & Rank")
    
    if st.button("🚀 Analyze and Rank Candidates", type="primary"):
        if not job_description.strip():
            st.error("❌ Please enter a job description")
            return
        
        if not uploaded_files:
            st.error("❌ Please upload at least one resume")
            return
        
        # Processing
        start_time = time.time()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Parse job description
        status_text.text("🔍 Analyzing job requirements...")
        try:
            use_llm = "Smart Analysis" in processing_mode and ollama_status
            if use_llm:
                job_requirements = job_parser.extract_requirements_with_llm(job_description)
            else:
                job_requirements = job_parser.extract_requirements_simple(job_description)
            
            if debug_mode:
                st.write("**Debug - Job Requirements:**", job_requirements)
            
            progress_bar.progress(20)
            
        except Exception as e:
            st.error(f"Error parsing job description: {e}")
            if debug_mode:
                st.code(traceback.format_exc())
            return
        
        # Step 2: Process resumes
        results = []
        total_files = len(uploaded_files)
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"📄 Processing {uploaded_file.name} ({i+1}/{total_files})")
            
            temp_path = None
            try:
                # Save uploaded file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    temp_path = tmp_file.name
                
                # Parse resume
                resume_data = resume_parser.parse_resume(temp_path)
                resume_data['filename'] = uploaded_file.name  # Force correct filename
                
                if debug_mode:
                    st.write(f"**Debug - {uploaded_file.name}:**")
                    st.write("Skills found:", resume_data.get('skills', []))
                
                # Calculate match
                if use_llm:
                    match_result = matcher.calculate_match_with_llm(resume_data, job_requirements)
                else:
                    match_result = matcher.calculate_match_simple(resume_data, job_requirements)
                
                match_result['filename'] = uploaded_file.name  # Ensure filename is correct
                results.append(match_result)
                
                if debug_mode:
                    st.write("Match result:", match_result)
                
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                if debug_mode:
                    st.code(traceback.format_exc())
                
                # Add error result
                results.append({
                    'filename': uploaded_file.name,
                    'skills_score': 0,
                    'experience_score': 0,
                    'overall_score': 0,
                    'strengths': f'Processing error: {str(e)}',
                    'gaps': 'Could not analyze due to error'
                })
            
            finally:
                # Cleanup
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
            
            # Update progress
            progress_bar.progress(20 + int((i + 1) / total_files * 80))
        
        # Step 3: Sort and display results
        total_time = time.time() - start_time
        status_text.text(f"✅ Complete! Processed in {total_time:.1f} seconds")
        
        # Sort by overall score
        results = sorted(results, key=lambda x: x.get('overall_score', 0), reverse=True)
        
        # Display results
        st.header("4️⃣ Ranking Results")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        scores = [r['overall_score'] for r in results if r['overall_score'] > 0]
        
        with col1:
            st.metric("Total Candidates", len(results))
        with col2:
            avg_score = sum(scores) / len(scores) if scores else 0
            st.metric("Average Score", f"{avg_score:.1f}")
        with col3:
            st.metric("Top Score", max(scores) if scores else 0)
        with col4:
            qualified = len([s for s in scores if s >= 70])
            st.metric("Qualified (≥70%)", qualified)
        
        # Individual results
        for i, result in enumerate(results):
            rank_icon = ["🥇", "🥈", "🥉"][i] if i < 3 else "📄"
            
            with st.expander(
                f"{rank_icon} #{i+1}: {result['filename']} - {result['overall_score']}/100",
                expanded=(i < 2)
            ):
                # Scores
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Skills Match", f"{result['skills_score']}/100")
                    st.progress(result['skills_score'] / 100)
                
                with col2:
                    st.metric("Experience Match", f"{result['experience_score']}/100") 
                    st.progress(result['experience_score'] / 100)
                
                with col3:
                    st.metric("Overall Score", f"{result['overall_score']}/100")
                    st.progress(result['overall_score'] / 100)
                
                # Feedback
                st.write("**💪 Strengths:**", result.get('strengths', 'None identified'))
                st.write("**📈 Improvement Areas:**", result.get('gaps', 'None identified'))
        
        # Export
        st.header("5️⃣ Export Results")
        
        df = pd.DataFrame([
            {
                'Rank': i + 1,
                'Candidate': result['filename'],
                'Overall_Score': result['overall_score'],
                'Skills_Score': result['skills_score'], 
                'Experience_Score': result['experience_score'],
                'Strengths': result.get('strengths', ''),
                'Gaps': result.get('gaps', '')
            }
            for i, result in enumerate(results)
        ])
        
        csv_data = df.to_csv(index=False)
        st.download_button(
            "📥 Download CSV Report",
            csv_data,
            file_name=f"cv_analysis_{int(time.time())}.csv",
            mime="text/csv"
        )
        
        st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()
