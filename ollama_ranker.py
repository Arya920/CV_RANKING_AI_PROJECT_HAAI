from litellm import completion

def get_rank_from_ollama(experience: str, skills: str, jd:str ) -> str:
    """
    Call local Ollama model to get ranking score + explanation.
    Assumes Ollama is running locally on port 11434.
    """

    prompt = (
            "You are a hiring assistant. Based on the candidate's experience and technical skills, "
            "and the job description below, give a score out of 10 for job fit and provide a short explanation.\n\n"
            "Format your answer strictly as:\n"
            "Rating: <number>/10\n"
            "Conclusion: <5 crisp factual bullet points, OR 1-2 short sentences covering exactly 5 key facts>\n\n"
            f"Resume:\nExperience: {experience}\n\nTechnical Skills: {skills}\n\n"
            f"Job Description:\n{jd}"
        )
    
    try:
        response = completion(
            model="ollama/llama3.2:3b",
            messages=[{"role": "user", "content": prompt}],
            api_base="http://localhost:11434"
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling Ollama model: {e}"



