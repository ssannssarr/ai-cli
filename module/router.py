import time

import requests

from module.config import API_KEY, APP_NAME, BASE_URL, MAX_RETRIES, TIMEOUT
from module.memory import build_context
from module.models import ModelRegistryError, resolve_model_for_request


def classify_task(prompt):
    p = prompt.lower()
    if any(k in p for k in ["fix", "debug", "write code", "script", "refactor"]):
        return "coding"
    if any(k in p for k in ["design", "architecture", "explain system", "optimize"]):
        return "reasoning"
    return "fallback"


def send_request(prompt, task_type=None, project=None):
    if not API_KEY:
        print("Error: OPENROUTER_API_KEY not found in environment or .env file.")
        return None

    task_type = task_type or classify_task(prompt)

    try:
        selected_model = resolve_model_for_request()
    except ModelRegistryError as e:
        print(f"Error: {e}")
        print("Run /model refresh or /model list free once you have network access.")
        return None

    if not selected_model:
        print("Error: No model configured and no free OpenRouter model is available.")
        print("Run /model list free, then /model use <model-id>.")
        return None

    if project:
        context = build_context(project)
        prompt = f"[Project Context]\n{context}\n\n[User Request]\n{prompt}"

    model_id = selected_model["id"]
    print(f"\nUsing model: {selected_model.get('tier', 'unknown')} -> {model_id} ({task_type})")

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                BASE_URL,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "X-Title": APP_NAME,
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": "You are a terminal AI assistant. Do not use any markdown formatting."},
                        {"role": "user", "content": prompt}
                    ],
                },
                timeout=TIMEOUT,
            )

            if response.status_code == 200:
                try:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                except (KeyError, IndexError, ValueError) as e:
                    print(f"Failed to parse response from {model_id}: {e}")
                    return None

            if response.status_code == 401:
                print("Unauthorized: Please check your API key.")
                return None

            if response.status_code in [429, 503]:
                print(
                    f"Rate limited or service unavailable ({response.status_code}). "
                    f"Attempt {attempt + 1}/{MAX_RETRIES}"
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 * (attempt + 1))
                continue

            print(f"Error {response.status_code} on attempt {attempt + 1}: {response.text[:300]}")
            time.sleep(1)

        except requests.exceptions.Timeout:
            print(f"Timeout on {model_id}, attempt {attempt + 1}")
            time.sleep(1)

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None

    print("All attempts failed.")
    return None
