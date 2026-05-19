import requests
import time
import sys
from module.config import API_KEY, BASE_URL, MAX_RETRIES, TIMEOUT, APP_NAME
from module.models import MODELS, FALLBACK_ORDER
from module.memory import build_context

def classify_task(prompt):
    p = prompt.lower()
    if any(k in p for k in ["fix", "debug", "write code", "script", "refactor"]):
        return "coding"
    elif any(k in p for k in ["design", "architecture", "explain system", "optimize"]):
        return "reasoning"
    else:
        return "fallback"

def send_request(prompt, task_type=None, project=None):
    if not API_KEY:
        print("❌ Error: OPENROUTER_API_KEY not found in environment or .env file.")
        return None

    if not task_type:
        task_type = classify_task(prompt)

    # Inject project memory if active
    if project:
        context = build_context(project)
        prompt = f"[Project Context]\n{context}\n\n[User Request]\n{prompt}"

    # Deduplicate fallback order while keeping task_type first
    order = []
    seen = set()
    for m in [task_type] + FALLBACK_ORDER:
        if m in MODELS and m not in seen:
            order.append(m)
            seen.add(m)

    for model_key in order:
        model = MODELS[model_key]
        print(f"\n🤖 Using model: {model_key} → {model}")

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    BASE_URL,
                    headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "X-Title": APP_NAME,
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    timeout=TIMEOUT
                )

                if response.status_code == 200:
                    try:
                        data = response.json()
                        return data["choices"][0]["message"]["content"]
                    except (KeyError, IndexError, ValueError) as e:
                        print(f"❌ Failed to parse response from {model_key}: {e}")
                        break # Try next model

                elif response.status_code == 401:
                    print("❌ Unauthorized: Please check your API key.")
                    return None

                elif response.status_code in [429, 503]:
                    print(f"⚠️  Rate limited or Service Unavailable ({response.status_code}) on {model_key}. Attempt {attempt+1}/{MAX_RETRIES}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(2 * (attempt + 1)) # Exponential backoff
                    else:
                        print(f"⏭️  Switching from {model_key} due to persistent issues.")
                        break # Try next model

                else:
                    print(f"❌ Error {response.status_code} on attempt {attempt+1}")
                    time.sleep(1)

            except requests.exceptions.Timeout:
                print(f"⏱️  Timeout on {model_key}, attempt {attempt+1}")
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                print(f"❌ Request error: {e}")
                break # Try next model

    print("❌ All models failed.")
    return None
