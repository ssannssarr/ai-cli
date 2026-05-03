MODELS = {
    "coding": "openai/gpt-oss-120b:free",
    "reasoning": "openai/gpt-oss-20b:free",
    "fallback": "openai/gpt-oss-120b:free",
    "fallback2": "openai/gpt-oss-120b:free",
    "fallback3": "openai/gpt-oss-120b:free"
}

FALLBACK_ORDER = ["coding", "reasoning", "fallback", "fallback2", "fallback3"]

def get_model(task_type="reasoning"):
    return MODELS.get(task_type, MODELS["fallback"])