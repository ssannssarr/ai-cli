import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../ai-cli')))

import unittest
from router import classify_task

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

if __name__ == '__main__':
    unittest.main()
