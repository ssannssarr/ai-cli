import unittest
from unittest.mock import patch

import main


FREE_MODEL = {
    "id": "provider/free-model:free",
    "name": "Free Model",
    "tier": "free",
    "context_length": 8192,
    "pricing": {"prompt": "0", "completion": "0", "request": "0"},
}

PAID_MODEL = {
    "id": "provider/paid-model",
    "name": "Paid Model",
    "tier": "paid",
    "context_length": 32768,
    "pricing": {"prompt": "0.000001", "completion": "0.000002", "request": "0"},
}


class TestModelCommand(unittest.TestCase):
    @patch.object(main, "get_active_model", return_value=FREE_MODEL)
    @patch.object(main, "print_model_table")
    def test_model_current(self, print_table, get_active):
        main.handle_model_command(["current"])
        print_table.assert_called_once()

    @patch.object(main, "list_models", return_value=[FREE_MODEL])
    @patch.object(main, "print_model_table")
    def test_model_list_free(self, print_table, list_models):
        main.handle_model_command(["list", "free"])
        list_models.assert_called_once_with(tier="free")
        print_table.assert_called_once()

    @patch.object(main, "list_models", return_value=[FREE_MODEL])
    @patch.object(main, "find_model", return_value=FREE_MODEL)
    @patch.object(main, "set_active_model", return_value=FREE_MODEL)
    def test_model_use_free(self, set_active, find_model, list_models):
        main.handle_model_command(["use", "provider/free-model:free"])
        set_active.assert_called_once_with(FREE_MODEL)

    @patch.object(main, "list_models", return_value=[PAID_MODEL])
    @patch.object(main, "find_model", return_value=PAID_MODEL)
    @patch.object(main, "set_active_model", return_value=PAID_MODEL)
    def test_model_use_paid_requires_confirmation(self, set_active, find_model, list_models):
        main.handle_model_command(["use", "provider/paid-model"], confirm_func=lambda prompt: "no")
        set_active.assert_not_called()

        main.handle_model_command(["use", "provider/paid-model"], confirm_func=lambda prompt: "yes")
        set_active.assert_called_once_with(PAID_MODEL)

    @patch.object(main, "list_models", return_value=[FREE_MODEL, PAID_MODEL])
    def test_model_refresh(self, list_models):
        main.handle_model_command(["refresh"])
        list_models.assert_called_once_with(refresh=True)


if __name__ == "__main__":
    unittest.main()
