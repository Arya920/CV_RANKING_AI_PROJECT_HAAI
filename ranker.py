from litellm import completion


# Wrapper around a local Ollama call. This module keeps the prompt
# definition centralized so the app can request experience-only scoring
# from the local model. The function returns the raw model text output
# (expected to contain a rating and a short explanation). The caller
# is responsible for parsing the returned string.
def get_rank_from_ollama(experience: str, jd: str) -> str:
    """
    Call the local Ollama model to obtain an experience-based rating and explanation.

    Parameters
    - experience: free-text summary of the candidate's experience
    - jd: the job description experience requirement (free text)

    Returns
    - str: the raw response content from the LLM. The prompt requests the
      format: "Experience Rating: <number>/10" and a "Conclusion:" section.

    Notes
    - Ollama is expected to run locally and be available at http://localhost:11434.
    - This function catches exceptions and returns a readable error string on failure.
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
        # Call Ollama model with the prompt. We return the raw textual content and
        # leave parsing responsibilities to the caller (for example, `components.extract_rating`).
        response = completion(
            model="ollama/llama3.2:3b",
            messages=[{"role": "user", "content": prompt}],
            api_base="http://localhost:11434"
        )
        return response.choices[0].message.content  # raw response
    except Exception as e:
        # Return an error string instead of raising to ensure the UI remains stable.
        return f"Error calling Ollama model: {e}"
