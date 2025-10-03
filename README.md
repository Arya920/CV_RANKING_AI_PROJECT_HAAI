# 📄 CV Sorting using LLMs

## 📌 Problem Description
Recruiters often face the challenge of manually scanning and ranking resumes against job descriptions (JDs).  
Traditional keyword-based systems (ATS) miss semantic matches and lack interpretability.  

**Objective**: Build an AI-powered resume sorter that:
- Parses resumes (PDF/DOCX) into structured data
- Extracts requirements from job descriptions
- Matches candidates to jobs using embeddings + LLMs
- Provides ranking with explanations and recruiter-friendly dashboard

---

## 🛠️ Solution Approach
The solution is a UI-driven LLM (Nuextract) powered webApp. The entire developement has been done in python as backend technology and frontend UI interface has been developed in 'Streamlit' - which is a python package for quick UI prototyping and medium scale applications.


### 1. Resume & JD Parsing
- **PDFs** → parsed using `pdfminer.six`
- **DOCX** → parsed using `python-docx`
- **LLM (Ollama)** used to structure raw text into fields:
  - Name, Contact Info
  - Skills
  - Education
  - Experience
  - Projects / Certifications

### 2. Candidate–Job Matching
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
  - Compute cosine similarity between resume and JD text
- LLM Scoring:
  - Nuextract (via Ollama) 
  - Outputs structured JSON with:
    ```json
    {
      "skills_match": 4.5,
      "experience_match": 3.8,
      "overall_fit": 4.2,
      "explanation": "Candidate has strong Python/ML skills, lacks cloud deployment."
    }
    ```

### 3. Ranking
- All candidate scores are aggregated into a Pandas DataFrame
- Sorted by `overall_fit` descending
- Includes:
  - Candidate name
  - Similarity score
  - Fit score
  - Explanation

### 4. Streamlit Charts & Visuals
- Upload resumes + JD
- Display ranked results in a table
- Visuals:
  - 📊 Candidate ranking bar chart
  - ⚖️ Skills vs. Experience scatter plot
  - 📈 Distribution of overall_fit
  - 🏆 Summary card (best candidate, average fit, top 3)

---

## ⚙️ Setup Instructions

### 1. Clone Repo
```bash
git clone <your_repo_url>
cd cv_sorting_llm
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate       # Windows
```

### 3. Install Python Dependencies from the requirements.txt file available in the repository
```bash
pip install -r requirements.txt
```


### 4. Install Ollama (Required as the primary LLM being use is run locally)
Ollama lets you run LLMs **locally** (private, no API keys).

- Download: [https://ollama.com/download](https://ollama.com/download)
- Verify install:
  ```bash
  ollama --version
  ```
- Pull a model:
  ```bash
  ollama pull nuextract
  ```
- Make sure Ollama service is running. Windows system may require a reboot before the service can be started:
  ```bash
  ollama serve
  ```

---

## ▶️ Running the App
```bash
streamlit run main.py
```

The Streamlit app shuld automatically open up in browser. If not, then open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📂 Project Structure
```
cv_sorting_llm/
│── main.py                 # Streamlit frontend and main driver python file: entry point
│── parser_llm.py      # Resume parsing (pdfminer/docx + LLM)
│── matcher.py         # Embedding + LLM scoring
│── ranker.py          # Ranking logic
│── utils.py           # JSON safety helpers
│── data/
│   ├── resumes/           # Sample resumes
│   ├── job_descriptions/  # Sample JDs
│── requirements.txt
│── README.md
```

---

## 📊 Example Analysis
1. **Ranking of candidates**
   - Bar chart of `overall_fit` scores
2. **Skills vs. Experience**
   - Scatter plot of `skills_match` vs. `experience_match`
3. **Fit Score Distribution**
   - Histogram of `overall_fit`
4. **Summary**
   - Average fit score across all candidates
   - Best candidate
   - Top 3 candidates list

---

## 🏁 General Flow

1. Recruiter uploads resumes (PDF/DOCX) and pastes job description.  
2. Resume parser → Extracts raw text → LLM structures fields.  
3. JD parser → Extracts skills/requirements using LLM.  
4. Embedding model computes baseline similarity.  
5. LLM computes detailed fit scores + explanations.  
6. DataFrame is built with all candidates’ scores.  
7. Streamlit dashboard displays:
   - Ranked list with explanations
   - Charts + summary insights

---

## ✅ Key Benefits
- More accurate than keyword-based ATS
- Semantic understanding of resumes & JDs
- Transparent scoring with explanations
- Fully local (privacy-friendly) with Ollama
- Recruiter-friendly Streamlit interface
