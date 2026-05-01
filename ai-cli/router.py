import requests
import time
from config import API_KEY, BASE_URL, MAX_RETRIES, TIMEOUT, APP_NAME
from models import MODELS, FALLBACK_ORDER
from memory import build_context

def classify_task(prompt):
    p = prompt.lower()
    if any(k in p for k in ["fix", "debug", "write code", "script", "refactor"]):
        return "coding"
    elif any(k in p for k in ["design", "architecture", "explain system", "optimize"]):
        return "reasoning"
    else:
        return "fallback"

def send_request(prompt, task_type=None, project=None):
    if not task_type:
        task_type = classify_task(prompt)

    # Inject project memory if active
    if project:
        context = build_context(project)
        prompt = f"[Project Context]\n{context}\n\n[User Request]\n{prompt}"

    order = [task_type] + [m for m in FALLBACK_ORDER if m != task_type]

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
                    return response.json()["choices"][0]["message"]["content"]

                elif response.status_code in [429, 503]:
                    print(f"⚠️  Rate limited on {model_key}. Waiting 5s before switching...")
                    time.sleep(5)
                    break

                else:
                    print(f"❌ Error {response.status_code} on attempt {attempt+1}")
                    time.sleep(2)

            except requests.exceptions.Timeout:
                print(f"⏱️  Timeout on {model_key}, attempt {attempt+1}")
                time.sleep(2)

            except requests.exceptions.ConnectionError:
                print("❌ No internet connection.")
                return None

    print("❌ All models failed.")
    return None
