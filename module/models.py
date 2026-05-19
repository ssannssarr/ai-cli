import json
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import requests

from module.config import API_KEY, TIMEOUT

MODELS_URL = "https://openrouter.ai/api/v1/models"
AI_CLI_DIR = os.path.expanduser("~/.ai-cli")
CACHE_PATH = os.path.join(AI_CLI_DIR, "models_cache.json")
CONFIG_PATH = os.path.join(AI_CLI_DIR, "config.json")


class ModelRegistryError(Exception):
    pass


def ensure_config_dir():
    os.makedirs(AI_CLI_DIR, exist_ok=True)


def price_value(value):
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def price_summary(model):
    pricing = model.get("pricing") or {}
    prompt = pricing.get("prompt", "0")
    completion = pricing.get("completion", "0")
    request = pricing.get("request", "0")
    return f"prompt={prompt}, completion={completion}, request={request}"


def classify_model(model):
    pricing = model.get("pricing") or {}
    paid_fields = ("prompt", "completion", "request")
    if all(price_value(pricing.get(field)) == 0 for field in paid_fields):
        return "free"
    return "paid"


def is_expired(model):
    expiration = model.get("expiration_date")
    if not expiration:
        return False
    try:
        expires = datetime.fromisoformat(str(expiration).replace("Z", "+00:00"))
    except ValueError:
        return False
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return expires <= datetime.now(timezone.utc)


def is_text_model(model):
    architecture = model.get("architecture") or {}
    output = architecture.get("output_modalities") or []
    return "text" in output


def normalize_model(model):
    return {
        "id": model.get("id", ""),
        "name": model.get("name") or model.get("id", ""),
        "tier": classify_model(model),
        "context_length": model.get("context_length")
        or (model.get("top_provider") or {}).get("context_length"),
        "pricing": model.get("pricing") or {},
        "description": model.get("description", ""),
    }


def filter_models(models):
    normalized = []
    for model in models:
        if not model.get("id") or not is_text_model(model) or is_expired(model):
            continue
        normalized.append(normalize_model(model))
    return sorted(normalized, key=lambda item: (item["tier"] != "free", item["id"]))


def fetch_models():
    headers = {}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    response = requests.get(MODELS_URL, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    data = response.json()
    return filter_models(data.get("data", []))


def save_models_cache(models):
    ensure_config_dir()
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump({"fetched_at": datetime.now(timezone.utc).isoformat(), "models": models}, f, indent=2)


def load_models_cache():
    if not os.path.exists(CACHE_PATH):
        return []
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("models", [])


def get_models(refresh=False):
    if refresh:
        try:
            models = fetch_models()
        except requests.RequestException as e:
            raise ModelRegistryError(f"Could not fetch OpenRouter models: {e}") from e
        save_models_cache(models)
        return models

    cached = load_models_cache()
    if cached:
        return cached

    try:
        models = fetch_models()
    except requests.RequestException as e:
        raise ModelRegistryError(f"Could not fetch OpenRouter models: {e}") from e
    save_models_cache(models)
    return models


def list_models(tier=None, refresh=False):
    models = get_models(refresh=refresh)
    if tier:
        models = [model for model in models if model.get("tier") == tier]
    return models


def find_model(model_id, models=None):
    models = models if models is not None else get_models()
    return next((model for model in models if model.get("id") == model_id), None)


def load_cli_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cli_config(config):
    ensure_config_dir()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def set_active_model(model):
    config = load_cli_config()
    config["model"] = {
        "id": model["id"],
        "name": model.get("name", model["id"]),
        "tier": model.get("tier", "unknown"),
        "context_length": model.get("context_length"),
        "pricing": model.get("pricing", {}),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    save_cli_config(config)
    return config["model"]


def get_active_model():
    return load_cli_config().get("model")


def compact_model_name(model):
    if not model:
        return "none"
    model_id = model.get("id", "")
    short_id = model_id.split("/")[-1] if "/" in model_id else model_id
    tier = model.get("tier", "unknown")
    return f"{tier}/{short_id}" if short_id else "none"


def resolve_model_for_request():
    active = get_active_model()
    if active and active.get("id"):
        return active

    free_models = list_models(tier="free")
    if not free_models:
        return None
    return free_models[0]
