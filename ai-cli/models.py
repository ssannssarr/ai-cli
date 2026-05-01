MODELS = {
    "coding": "openai/gpt-oss-120b:free",
    "reasoning": "openai/gpt-oss-20b:free",
    "fallback": "google/gemma-3-27b-it:free",
    "fallback2": "google/gemma-3-12b-it:free",
    "fallback3": "google/gemma-3-4b-it:free"
}

FALLBACK_ORDER = ["coding", "reasoning", "fallback", "fallback2", "fallback3"]

def get_model(task_type="reasoning"):
    return MODELS.get(task_type, MODELS["fallback"])
