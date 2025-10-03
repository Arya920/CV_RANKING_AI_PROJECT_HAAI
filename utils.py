import json

# Function to safely extract JSON from LLM response. Making sure braces are balanced.
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