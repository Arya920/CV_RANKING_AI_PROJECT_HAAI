from sentence_transformers import SentenceTransformer, util
import ollama
import json
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# Load embedding model once
embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# llm = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.2")

def safe_json_loads(response: str):
    """
    Extract and parse the first valid JSON object from a response string.
    """
    try:
        start = response.find("{")
        if start == -1:
            return {"error": "No JSON object found", "raw_response": response}

        # Balance braces to capture only the first full JSON object
        depth = 0
        for i, ch in enumerate(response[start:], start=start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    json_str = response[start:i+1]
                    return json.loads(json_str)

        return {"error": "Unbalanced braces", "raw_response": response}
    except Exception as e:
        return {"error": str(e), "raw_response": response}

def init_hf_llm(model_id="microsoft/Phi-3-mini-4k-instruct"):
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto")
    gen = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=512)

    def llm(prompt):
        response = gen(prompt)[0]['generated_text']
        return response
    return llm

def compute_similarity(resume_text, jd_text):
    """Compute cosine similarity between resume & JD."""
    embeddings = embedder.encode([resume_text, jd_text], convert_to_tensor=True)
    return util.pytorch_cos_sim(embeddings[0], embeddings[1]).item()

def init_llm(model_name="llama3"):
    """Initialize Ollama model."""
    def llm(prompt):
        response = ollama.chat(model=model_name, messages=[{"role": "user", "content": prompt}])
        return response['message']['content']
    return llm

def llm_match_score(resume_structured, jd_structured, llm=None):
    """Ask LLM for a detailed score & explanation."""
    if not llm:
        return {"fit_score": 0.5, "explanation": "Dummy score, no LLM connected."}
    
    prompt = f"""
    Compare this resume and job description.
    Resume: {resume_structured}
    Job Description: {jd_structured}

    Score the match from (0 to 10) and explain why.
    Return JSON like:
    {{
        "skills_match": <float>,
        "experience_match": <float>,
        "overall_fit": <float>,
        "explanation": "<string>"
    }}
    """
    response = llm(prompt)
    try:
        print(response)
        return safe_json_loads(response)
    except Exception as e:
        print(str(e))
        return {"overall_fit": 0.5, "explanation": response}
