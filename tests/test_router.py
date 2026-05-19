import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import Mock, patch

from module import router
from module.router import classify_task

class TestRouter(unittest.TestCase):
    def test_classify_coding(self):
        self.assertEqual(classify_task("fix this bug"), "coding")
        self.assertEqual(classify_task("write a script to scrape web"), "coding")
        self.assertEqual(classify_task("refactor the login function"), "coding")

    def test_classify_reasoning(self):
        self.assertEqual(classify_task("explain the architecture"), "reasoning")
        self.assertEqual(classify_task("optimize this algorithm"), "reasoning")
        self.assertEqual(classify_task("design a database schema"), "reasoning")

    def test_classify_fallback(self):
        self.assertEqual(classify_task("what is the capital of France?"), "fallback")
        self.assertEqual(classify_task("tell me a joke"), "fallback")

    @patch.object(router, "API_KEY", "test-key")
    @patch.object(router, "resolve_model_for_request", return_value={"id": "provider/model", "tier": "free"})
    @patch.object(router.requests, "post")
    def test_send_request_uses_resolved_model(self, post, resolve_model):
        response = Mock(status_code=200)
        response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
        post.return_value = response

        result = router.send_request("hello")

        self.assertEqual(result, "ok")
        self.assertEqual(post.call_args.kwargs["json"]["model"], "provider/model")

    @patch.object(router, "API_KEY", "test-key")
    @patch.object(router, "resolve_model_for_request", return_value=None)
    def test_send_request_reports_missing_model(self, resolve_model):
        self.assertIsNone(router.send_request("hello"))

if __name__ == '__main__':
    unittest.main()
