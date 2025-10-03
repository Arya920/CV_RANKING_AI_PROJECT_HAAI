from sentence_transformers import SentenceTransformer, util
import ollama
from utils import safe_json_loads
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# Load embedding model once
embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')



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
    Compare this resume and job description given below. Find how well they match on key aspects like skills, experience, and overall fit.
    Resume: {resume_structured}
    Job Description: {jd_structured}

    Score the match from (0 to 1) and explain why.
    Return the scores and explanation in JSON like:
    {{
        "skills_match": <float>,
        "experience_match": <float>,
        "overall_fit": <float>,
        "explanation": "<string>"
    }}
    """
    response = llm(prompt)
    try:
        return safe_json_loads(response)
    except Exception as e:
        return {"overall_fit": 0.5, "explanation": response}
