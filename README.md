AgenticRag — Resume Extraction + Local Model Ranking

Background

AgenticRag is a lightweight research / prototype project that demonstrates an end-to-end pipeline for extracting structured data from resumes and automatically scoring candidate-job fit locally. The project combines: (1) a third-party resume extraction API (NuMind) for structured parsing, (2) PDF/text extraction utilities, and (3) a local LLM (Ollama) driven ranker for scoring and brief explanation of fit.

Technical approach

- Extraction: PDFs and plain text resumes are converted to raw text using `text_extractor.py` (uses `pdfplumber` to parse PDF pages). For structured parsing the project uses the NuMind client in `extractor.py` with a declarative `schema` mapping to extract fields like personal information, education, experience, and skills.
- Local ranking: `ollama_ranker.py` demonstrates calling a locally hosted Ollama model (e.g., `ollama/llama3.2:3b`) via the `litellm` `completion` API to generate a rating and concise explanation of candidate-job fit.
- Glue logic / demo: `app.py` and `sample.py` (if present) are expected to orchestrate file input, call the text/structured extraction, and then call the ranker to produce a final score and short rationale.

Pipeline (stepwise)

1. Upload or supply a resume file (PDF or TXT).
2. Use `text_extractor.extract_text_from_pdf` or `text_extractor.extract_text_from_txt` to obtain raw resume text.
3. Call `extractor.extract_resume_data(text)` which sends the text to NuMind for structured extraction using the provided `schema`.
4. Optionally format the extracted `Experience` and `Technical Skills` fields into strings.
5. Call `ollama_ranker.get_rank_from_ollama(experience, skills, jd)` to get a `Rating: <n>/10` and `Conclusion:` output from the local LLM.
6. Present or store the combined structured data + ranking result.

Installation

Prerequisites
- Python 3.11 (recommended) or 3.10+
- A virtual environment (recommended)
- Local Ollama service running on port 11434 if you plan to use the local model ranking step
- NuMind API key (set as `NUMIND_API_KEY` in a `.env` file at project root)

Install dependencies

From the project root, create and activate a virtual environment and install packages. Example (PowerShell):

```powershell
# create venv
python -m venv agent\
# activate
.\agent\Scripts\Activate
# install
pip install -r requirements.txt
```

Note: This repository includes a pre-created `agent` virtual environment folder. You can instead use that interpreter, or create your own venv as shown.

Configuration
- Put your NuMind API key in `.env` as `NUMIND_API_KEY`. The project already contains an example `.env` file (do not commit secrets to version control).
- Ensure Ollama is running locally (see Ollama docs); the ranker expects it at `http://localhost:11434`.

Usage

Basic script flow (example)
- `text_extractor.extract_text_from_pdf(file)` — pass a Streamlit uploaded file or a file-like object to extract raw text.
- `extractor.extract_resume_data(text)` — returns a dictionary with the structured fields per the schema defined in `extractor.py`.
- `ollama_ranker.get_rank_from_ollama(experience, skills, jd)` — returns the model's rating/explanation string. Provide a job description string as `jd`.

Custom prompts

The project's prompt for the local LLM is defined in `ollama_ranker.py`. It instructs the model to return two lines: a `Rating: <number>/10` and a `Conclusion:` that is either exactly 5 bullet facts or 1-2 short sentences covering exactly 5 key facts.

If you want to change the format or the model's behavior, edit the `prompt` string in `ollama_ranker.get_rank_from_ollama`. Example customizations:
- Ask for a breakdown per skill, or per role.
- Return JSON instead of free text (helpful for programmatic parsing). Example JSON prompt suffix:
  "Return JSON with fields: rating (number), conclusions (array of 5 strings)."

Experimental results (notes)

- This is a prototype; quantitative evaluation was not included. Recommended experiments:
  - Human evaluation: Have recruiters rate model output for a sample of resumes and job descriptions to measure correlation with human judgments.
  - Precision of extraction: Compare `NuMind` extraction against hand-labeled ground truth for fields like dates, roles, and skills.
  - Ablation: Compare performance with/without local LLM scoring, or using different model sizes in Ollama.

Troubleshooting

- NuMind errors / API key: If `extractor.extract_resume_data` returns an error, confirm `NUMIND_API_KEY` is set in `.env` and exported into the environment. You can print `os.getenv('NUMIND_API_KEY')` to verify at runtime.
- PDF text extraction returns empty string: Some PDFs are scanned images; `pdfplumber` won’t extract text from images. Use OCR (e.g., `pytesseract`) to extract text from scanned PDFs.
- Ollama connection errors: Ensure the Ollama daemon is running and reachable at `http://localhost:11434`. If using a different host/port, update `ollama_ranker.py` `api_base`.
- Unexpected model output: The prompt enforces a format, but models can deviate. Consider requesting JSON output or adding stronger format checks and a parsing layer.

Security and privacy

- This project sends resumes to NuMind (a third-party service). Treat resume data as sensitive and ensure you have consent or use anonymized samples for testing.
- Don’t commit API keys to source control. Use `.env` and your environment to store secrets.

Next steps and improvements

- Add a simple Streamlit or FastAPI frontend that wires file uploads, runs the pipeline, and displays structured results + rating.
- Add unit tests for `text_extractor` and a mocked `extractor` client and `ollama_ranker`.
- Switch LLM output to JSON for more robust downstream parsing.
- Add OCR fallback for image PDFs.

License

This project is provided as-is for research and prototyping.

Acknowledgements

- NuMind API for extraction
- Ollama and `litellm` for local model inference

Contact

Maintainer: Arya Chakraborty
Email: (see `.env` or project contact)

CV Sorting using LLMs (HPPCS[02])

Project Title
CV Sorting using LLMs (HPPCS[02])

Abstract
[~180 words]
This project implements a prototype pipeline for automated CV sorting and ranking that combines structured extraction with local LLM-based scoring. The system accepts resumes (PDF/DOCX/TXT) via a Streamlit UI (`app.py`), extracts raw text (using `pdfplumber` and `python-docx`), and—when the user supplies an API key—calls NuMind to produce schema-driven structured output (Experience, Technical Skills, Education). Skill similarity between resumes and the job description is computed using Sentence-BERT embeddings with an exact-match fallback. A local LLM (Ollama via `litellm`) rates candidate experience and provides a short explanation. The final aggregate score blends the experience rating and the skill-match percentage to produce an explainable ranking. The implementation emphasizes modularity, privacy (local LLM scoring), and robust fallbacks so the demo remains usable if external services are unavailable.

1. Introduction
• Context and background
  - Recruiters face heavy manual effort screening many CVs; automated triage can save time and standardize initial filtering.
• Motivation
  - Build an explainable, modular prototype that demonstrates trade-offs between vendor structured extractors and locally-run LLM reasoning.

2. Problem Statement
• Clear articulation
  - Given a job description and a set of CVs, automatically extract relevant fields and rank candidates by fit (experience + skills) in an explainable manner while minimizing unnecessary data exposure.

3. Objectives
• Main goals
  - Provide a Streamlit UI for resume and JD uploads (`app.py`).
  - Extract structured data from resumes (Experience, Technical Skills) using NuMind.
  - Compute semantic skill similarity using Sentence-BERT and combine it with an experience rating from a local LLM.
  - Produce an explainable ranked output and require runtime API-key control for third-party extraction.

4. Methodology
• Tools and technologies used
  - Python 3.11, Streamlit (UI)
  - `pdfplumber`, `python-docx` for text extraction
  - NuMind (structured extractor) — runtime API key via `structured_data_extractor.py`
  - Sentence-Transformers (`all-MiniLM-L6-v2`) for embeddings, `scikit-learn` for cosine similarity
  - Ollama (local LLM) via `litellm` for experience scoring
  - Supporting libs: `numpy`, `pandas`, logging

• Workflow / conceptual framework
  1. User uploads resumes and the job description in the Streamlit app.
  2. Raw text is extracted from the files.
  3. If the user provides a NuMind API key, text is structured via the NuMind schema.
  4. Skills are normalized; semantic similarity is computed with SBERT; exact matching is a fallback.
  5. A local LLM rates experience; the system combines experience score and skill-match percentage into an aggregate score.

Choice and justification of models (at least two LLMs)
• NuMind (vendor LLM / structured extractor): specialized at schema extraction; returns structured JSON that simplifies downstream processing and reduces parsing brittleness.
• Ollama local LLM: provides flexible experience-based scoring and natural-language explanations while running locally to preserve privacy. Using both separates extraction (structured) from reasoning (scoring) and leverages each model's strengths.

5. System Design / Implementation
• Architecture (ASCII diagram)

  +----------------+     +-------------------+     +-------------------+
  | Streamlit UI   | --> | Text Extractors    | --> | Structured Extract|
  | (`app.py`)     |     | (pdfplumber, docx) |     | (NuMind via API)  |
  +----------------+     +-------------------+     +-------------------+
            |                       |                      |
            |                       v                      v
            |                 +-----------+         +-------------------+
            |                 | Similarity| <-----> | Embedding Model   |
            |                 | Module    |         | (SBERT)           |
            |                 +-----------+         +-------------------+
            |                       |
            v                       v
     +----------------+         +----------------+
     | Local LLM Rank |         | Results UI     |
     | (Ollama)       |         | (cards, scores) |
     +----------------+         +----------------+

• Modules and functionality
  - `text_extraction_from_pdf.py`: robust PDF/TXT/DOCX extraction with logging and pointer resets.
  - `structured_data_extractor.py`: NuMind wrapper exposing `set_numind_api_key`, `extract_resume_data`, `extract_jd_data` and returning explicit error dicts when unconfigured.
  - `similarity_checking.py`: SBERT-based semantic matching with exact-match fallback; function `process_resume_and_jd` returns final_match_score and explanation.
