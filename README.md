# CV Sorting using LLMs (HPPCS[02])

## Project Title

CV Sorting using LLMs (HPPCS[02])

## Abstract

This project implements a prototype pipeline for automated CV sorting and ranking that combines structured extraction with local LLM-based scoring. The system accepts resumes (PDF/DOCX/TXT) via a Streamlit UI (`app.py`), extracts raw text (using `pdfplumber` and `python-docx`), and—when the user supplies an API key—calls NuMind to produce schema-driven structured output (Experience, Technical Skills, Education). Skill similarity between resumes and the job description is computed using Sentence-BERT embeddings with an exact-match fallback. A local LLM (Ollama via `litellm`) rates candidate experience and provides a short explanation. The final aggregate score blends the experience rating and the skill-match percentage to produce an explainable ranking. The implementation emphasizes modularity, privacy (local LLM scoring), and robust fallbacks so the demo remains usable if external services are unavailable.

## 1. Introduction

### Context and background

Recruiters face heavy manual effort screening many CVs; automated triage can save time and standardize initial filtering.

### Motivation

Build an explainable, modular prototype that demonstrates trade-offs between vendor structured extractors and locally-run LLM reasoning.

## 2. Problem Statement

Given a job description and a set of CVs, automatically extract relevant fields and rank candidates by fit (experience + skills) in an explainable manner while minimizing unnecessary data exposure.

## 3. Objectives

- Provide a Streamlit UI for resume and JD uploads (`app.py`).
- Extract structured data from resumes (Experience, Technical Skills) using NuMind.
- Compute semantic skill similarity using Sentence-BERT and combine it with an experience rating from a local LLM.
- Produce an explainable ranked output and require runtime API-key control for third-party extraction.

## 4. Methodology

### Tools & Technologies

- Python 3.11, Streamlit
- `pdfplumber`, `python-docx` (text extraction)
- NuMind (structured extractor) — runtime API key via `structured_data_extractor.py`
- Sentence-Transformers (`all-MiniLM-L6-v2`) + `scikit-learn` (cosine similarity)
- Ollama (local LLM) via `litellm`
- Supporting libraries: `numpy`, `pandas`, `logging`

### Workflow (conceptual)

1. User uploads resumes and the job description in the Streamlit app.
2. Raw text is extracted from the files.
3. If the user provides a NuMind API key, text is structured via the NuMind schema.
4. Skills are normalized; semantic similarity is computed with SBERT; exact matching is a fallback.
5. A local LLM rates experience; the system combines experience score and skill-match percentage into an aggregate score.

### Models (choice & justification)

- **NuMind (structured extractor)** — specialized at schema-driven extraction (names, experience, skills). Returns structured JSON that simplifies downstream processing and reduces brittle parsing.
- **Ollama (local LLM)** — used to score experience and generate concise explanations. Running locally improves privacy and allows offline evaluation.

Using both models separates responsibilities: NuMind for reliable structured extraction, Ollama for reasoning and explanation.

## 5. System Design & Implementation

### Architecture

The ASCII diagram below is placed in a fenced code block so it renders exactly on GitHub and other Markdown viewers.

```
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
     | (Ollama)       |         | (cards, scores)|
     +----------------+         +----------------+
```

### Modules & responsibilities

- `text_extraction_from_pdf.py` — robust PDF/TXT/DOCX extraction (pdfplumber, python-docx). Returns empty string on failure and logs errors.
- `structured_data_extractor.py` — NuMind wrapper: `set_numind_api_key`, `extract_resume_data`, `extract_jd_data`. Returns controlled error objects when unconfigured.
- `similarity_checking.py` — normalizes skills and computes combined exact + semantic match (SBERT + cosine similarity). Exposes `process_resume_and_jd` returning `final_match_score` and `explanation`.
- `ranker.py` — calls local Ollama (via `litellm.completion`) with a strict prompt to obtain an experience rating and explanation.
- `components.py` — UI helpers for candidate cards and rating parsing.
- `app.py` — Streamlit orchestration, input validation, progress UI, and final ranking display.

## 6. Results & Analysis

### Key findings

- Semantic embeddings (SBERT) improve matching recall over strict exact matching by capturing synonyms and related phrases.
- NuMind simplifies downstream processing by providing structured fields but requires explicit user configuration (API key).
- Local LLM scoring yields human-readable explanations; enforcing a prompt format makes parsing more reliable.

### Example outputs

The Streamlit UI displays ranked candidate cards containing:

- Experience Rating (converted to percentage)
- Skill Match (%)
- Aggregate Score (weighted combination)
- Expandable explanation (from the local LLM)

See `app.py` and `components.py` for the exact rendering and prompt used by the ranker.

## 7. Conclusion & Future Work

### Summary

This repository contains a modular prototype that combines vendor-structured extraction and local LLM scoring to generate explainable CV rankings. The design balances extraction accuracy with privacy and fallbacks.

### Future work

- Add OCR fallback (Tesseract/pytesseract) for scanned PDFs.
- Enforce JSON output from the ranking LLM for deterministic parsing.
- Add unit tests and a small labeled dataset for evaluation.
- Investigate running an open-source extractor locally to eliminate the external dependency.

## 8. References

- NuMind: https://numind.ai
- Ollama: https://ollama.ai
- litellm: https://github.com/abidlabs/litellm
- Sentence Transformers: https://www.sbert.net/
- pdfplumber: https://github.com/jsvine/pdfplumber
- python-docx: https://python-docx.readthedocs.io/

---

### Acknowledgement

Student: Arya Chakraborty

### Notes for submission

- Replace the Abstract placeholder with a 150–250 word summary before submission.
- Use Times New Roman, 12pt, 1.5 line spacing for the final PDF and keep the report within 3 pages.
