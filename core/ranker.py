from litellm import completion

def get_rank_from_ollama(experience: str, jd: str) -> str:
    """
    Call local Ollama model to get ranking score and explanation based solely on experience.
    Assumes Ollama is running locally on port 11434.
    """

    prompt = (
        "You are a hiring assistant. Based on the candidate's experience "
        "and the job description's experience requirement, give a score out of 10 for job fit based on experience alone. "
        "Also, provide a short explanation of why this experience match score is given.\n\n"
        "Format your answer strictly as:\n"
        "Experience Rating: <number>/10\n"
        "Conclusion: <5 crisp factual bullet points, OR 1-2 short sentences covering exactly 5 key facts.\n\n"
        f"Resume Experience: {experience}\n\n"
        f"Job Experience Required: {jd}"
    )

    try:
        # Call Ollama model with the new prompt that only considers experience for ranking
        response = completion(
            model="ollama/llama3.2:3b",
            messages=[{"role": "user", "content": prompt}],
            api_base="http://localhost:11434"
        )
        return response.choices[0].message.content  # Return the raw response content
    except Exception as e:
        return f"Error calling Ollama model: {e}"
