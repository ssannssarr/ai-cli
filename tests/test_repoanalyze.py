import os
import tempfile
import unittest

from module import repoanalyze


class TestRepoAnalyze(unittest.TestCase):
    def test_collect_repo_context_reads_text_files_without_gitignore_filtering(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, ".gitignore"), "w", encoding="utf-8") as f:
                f.write("secret.txt\n")
            with open(os.path.join(tmp, "secret.txt"), "w", encoding="utf-8") as f:
                f.write("top secret\n")
            os.mkdir(os.path.join(tmp, ".git"))
            with open(os.path.join(tmp, ".git", "HEAD"), "w", encoding="utf-8") as f:
                f.write("ref: refs/heads/main\n")

            result = repoanalyze.collect_repo_context(root=tmp, max_total_chars=5000)

            self.assertIn("--- FILE: .gitignore ---", result["context"])
            self.assertIn("--- FILE: secret.txt ---", result["context"])
            self.assertNotIn("--- FILE: .git/HEAD ---", result["context"])

    def test_build_repo_analysis_prompt_includes_request_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "app.py"), "w", encoding="utf-8") as f:
                f.write("print('hi')\n")

            prompt, repo = repoanalyze.build_repo_analysis_prompt("Focus on risks", root=tmp)

            self.assertIn("Focus on risks", prompt)
            self.assertIn("Files read:", prompt)
            self.assertEqual(repo["files_read"], 1)


if __name__ == "__main__":
    unittest.main()
