import os

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
APP_NAME = "ai-cli"
MAX_RETRIES = 3
TIMEOUT = 30
