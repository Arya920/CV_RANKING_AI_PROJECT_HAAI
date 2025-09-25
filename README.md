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

### 1. Resume & JD Parsing
- **PDFs** → parsed using `pdfminer.six`
- **DOCX** → parsed using `python-docx`
- **LLM (Ollama/Hugging Face)** used to structure raw text into fields:
  - Name, Contact Info
  - Skills
  - Education
  - Experience
  - Projects / Certifications

### 2. Candidate–Job Matching
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
  - Compute similarity between resume and JD text
- LLM Scoring:
  - Llama 3 (via Ollama) or Phi-3 Mini (via Hugging Face fallback)
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

### 4. Streamlit Dashboard
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

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

Dependencies include:
- `streamlit`
- `langchain`
- `llama-index`
- `sentence-transformers`
- `transformers`
- `pdfminer.six`
- `python-docx`
- `pandas`
- `scikit-learn`

### 4. Install Ollama (Optional but Recommended)
Ollama lets you run LLMs **locally** (private, no API keys).

- Download: [https://ollama.com/download](https://ollama.com/download)
- Verify install:
  ```bash
  ollama --version
  ```
- Pull a model (e.g., Llama 3):
  ```bash
  ollama pull llama3
  ```
- Make sure Ollama service is running:
  ```bash
  ollama serve
  ```

### 5. Hugging Face Fallback (if no Ollama)
If Ollama is unavailable, the system falls back to a **lightweight Hugging Face model**:
- `microsoft/Phi-3-mini-4k-instruct` (3.8B → smaller & faster than 7B models)

---

## ▶️ Running the App
```bash
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📂 Project Structure
```
cv_sorting_llm/
│── app.py                 # Streamlit frontend
│── backend/
│   ├── parser_llm.py      # Resume parsing (pdfminer/docx + LLM)
│   ├── matcher.py         # Embedding + LLM scoring
│   ├── ranker.py          # Ranking logic
│   └── utils.py           # JSON safety helpers
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
