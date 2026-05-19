import os
import tempfile
import unittest
from unittest.mock import patch

import requests

from module import models


FREE_MODEL = {
    "id": "provider/free-model:free",
    "name": "Free Model",
    "architecture": {"output_modalities": ["text"]},
    "context_length": 8192,
    "pricing": {"prompt": "0", "completion": "0", "request": "0"},
    "expiration_date": None,
}

PAID_MODEL = {
    "id": "provider/paid-model",
    "name": "Paid Model",
    "architecture": {"output_modalities": ["text"]},
    "context_length": 32768,
    "pricing": {"prompt": "0.000001", "completion": "0.000002", "request": "0"},
    "expiration_date": None,
}

IMAGE_MODEL = {
    "id": "provider/image-model",
    "architecture": {"output_modalities": ["image"]},
    "pricing": {"prompt": "0", "completion": "0", "request": "0"},
}


class TestModels(unittest.TestCase):
    def test_classify_free_and_paid_models(self):
        self.assertEqual(models.classify_model(FREE_MODEL), "free")
        self.assertEqual(models.classify_model(PAID_MODEL), "paid")

    def test_filter_models_keeps_text_and_adds_tier(self):
        filtered = models.filter_models([PAID_MODEL, IMAGE_MODEL, FREE_MODEL])
        self.assertEqual([model["id"] for model in filtered], ["provider/free-model:free", "provider/paid-model"])
        self.assertEqual(filtered[0]["tier"], "free")
        self.assertEqual(filtered[1]["tier"], "paid")

    def test_cache_and_config_read_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = os.path.join(tmp, "models_cache.json")
            config_path = os.path.join(tmp, "config.json")
            with patch.object(models, "AI_CLI_DIR", tmp), patch.object(models, "CACHE_PATH", cache_path), patch.object(
                models, "CONFIG_PATH", config_path
            ):
                normalized = models.filter_models([FREE_MODEL])
                models.save_models_cache(normalized)
                self.assertEqual(models.load_models_cache()[0]["id"], "provider/free-model:free")

                saved = models.set_active_model(normalized[0])
                self.assertEqual(saved["id"], "provider/free-model:free")
                self.assertEqual(models.get_active_model()["tier"], "free")

    def test_resolve_model_falls_back_to_first_free_cached_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = os.path.join(tmp, "models_cache.json")
            config_path = os.path.join(tmp, "config.json")
            with patch.object(models, "AI_CLI_DIR", tmp), patch.object(models, "CACHE_PATH", cache_path), patch.object(
                models, "CONFIG_PATH", config_path
            ):
                models.save_models_cache(models.filter_models([FREE_MODEL, PAID_MODEL]))
                self.assertEqual(models.resolve_model_for_request()["id"], "provider/free-model:free")

    def test_missing_api_and_cache_reports_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = os.path.join(tmp, "models_cache.json")
            config_path = os.path.join(tmp, "config.json")
            with patch.object(models, "AI_CLI_DIR", tmp), patch.object(models, "CACHE_PATH", cache_path), patch.object(
                models, "CONFIG_PATH", config_path
            ), patch.object(models, "fetch_models", side_effect=requests.RequestException("offline")):
                with self.assertRaises(models.ModelRegistryError):
                    models.get_models()


if __name__ == "__main__":
    unittest.main()
