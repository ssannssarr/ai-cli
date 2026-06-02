import os
import tempfile
import unittest
from unittest.mock import patch

import main


class TestNaturalCommands(unittest.TestCase):
    def test_infer_analyze_repo(self):
        command = main.infer_builtin_command("analyze the repo")
        self.assertEqual(command, ("/analyze", []))

    def test_infer_analyze_repo_with_focus(self):
        command = main.infer_builtin_command("analyze the repository for architecture risks")
        self.assertEqual(command, ("/analyze", ["for architecture risks"]))

    def test_infer_explain_existing_file(self):
        command = main.infer_builtin_command("explain main.py")
        self.assertEqual(command, ("/explain", ["main.py"]))

    def test_infer_fix_existing_file(self):
        command = main.infer_builtin_command("please fix main.py")
        self.assertEqual(command, ("/fix", ["main.py"]))

    def test_infer_create_file_request(self):
        command = main.infer_builtin_command("create scripts/tool.py a small CLI for greeting users")
        self.assertEqual(command, ("/create", ["scripts/tool.py", "a small CLI for greeting users"]))

    def test_infer_tcp_scan(self):
        command = main.infer_builtin_command("scan localhost ports 22,80,443")
        self.assertEqual(command, ("/tcp", ["localhost", "-p", "22,80,443"]))

    def test_infer_model_list_free(self):
        command = main.infer_builtin_command("show free models")
        self.assertEqual(command, ("/model", ["list", "free"]))

    def test_infer_project_status(self):
        command = main.infer_builtin_command("project status")
        self.assertEqual(command, ("/project", ["status"]))

    def test_split_planner_steps(self):
        steps = main.split_planner_steps("explain main.py, then show free models; tell me what to use")
        self.assertEqual(steps, ["explain main.py", "show free models", "tell me what to use"])

    def test_build_execution_plan_for_multiple_local_steps(self):
        plan = main.build_execution_plan("analyze the repo then show free models")
        self.assertEqual(
            plan,
            [
                {"type": "local", "command": "/analyze", "args": [], "source": "analyze the repo"},
                {"type": "local", "command": "/model", "args": ["list", "free"], "source": "show free models"},
            ],
        )

    def test_build_execution_plan_mixes_local_and_ai_steps(self):
        plan = main.build_execution_plan("explain main.py then tell me if the design is good")
        self.assertEqual(plan[0]["type"], "local")
        self.assertEqual(plan[0]["command"], "/explain")
        self.assertEqual(plan[1]["type"], "ai")
        self.assertEqual(plan[1]["prompt"], "tell me if the design is good")

    def test_build_execution_plan_normalizes_followup_push(self):
        plan = main.build_execution_plan("generate readme then commit and push with message update docs")
        self.assertEqual(plan[0]["command"], "/readme")
        self.assertEqual(plan[1]["command"], "/github")
        self.assertEqual(plan[1]["args"], ["push", "update docs"])

    def test_validate_local_step_rejects_missing_file(self):
        is_valid, error = main.validate_local_step("/explain", ["missing-file.py"])
        self.assertFalse(is_valid)
        self.assertIn("file not found", error)

    def test_replan_failed_step_turns_local_step_into_ai(self):
        step = {"type": "local", "command": "/explain", "args": ["missing.py"], "source": "explain missing.py"}
        replanned = main.replan_failed_step(step, "file not found: missing.py")
        self.assertEqual(replanned["type"], "ai")
        self.assertIn("file not found", replanned["prompt"])
        self.assertIn("explain missing.py", replanned["prompt"])

    @patch.object(main, "execute_inferred_command")
    @patch.object(main, "send_request")
    def test_handle_command_prefers_inferred_local_tool(self, send_request, execute_inferred):
        main.handle_command("explain main.py")
        execute_inferred.assert_called_once_with("/explain", ["main.py"])
        send_request.assert_not_called()

    @patch.object(main, "get_active", return_value=None)
    @patch.object(main, "console")
    @patch.object(main, "send_request", return_value="answer")
    def test_handle_command_falls_back_to_ai(self, send_request, console, get_active):
        main.handle_command("tell me a joke")
        send_request.assert_called_once_with("tell me a joke", project=None)

    @patch.object(main, "get_active", return_value=None)
    @patch.object(main, "execute_plan")
    def test_handle_command_uses_planner_for_plain_text(self, execute_plan, get_active):
        main.handle_command("explain main.py then show free models")
        execute_plan.assert_called_once()

    @patch.object(main, "console")
    @patch.object(main, "execute_ai_step")
    @patch.object(main, "execute_inferred_command")
    def test_execute_plan_runs_steps_in_order(self, execute_inferred, execute_ai_step, console):
        plan = [
            {"type": "local", "command": "/explain", "args": ["main.py"], "source": "explain main.py"},
            {"type": "ai", "prompt": "summarize the explanation", "source": "summarize the explanation"},
        ]
        main.execute_plan(plan, project=None)
        execute_inferred.assert_called_once_with("/explain", ["main.py"])
        execute_ai_step.assert_called_once_with("summarize the explanation", None)

    @patch.object(main, "console")
    @patch.object(main, "execute_ai_step")
    def test_execute_plan_replans_failed_local_step(self, execute_ai_step, console):
        plan = [
            {"type": "local", "command": "/explain", "args": ["missing.py"], "source": "explain missing.py"},
        ]
        main.execute_plan(plan, project=None)
        prompt = execute_ai_step.call_args.args[0]
        self.assertIn("file not found", prompt)
        self.assertIn("explain missing.py", prompt)

    @patch.object(main, "console")
    @patch.object(main, "execute_ai_step")
    @patch.object(main, "execute_inferred_command", side_effect=RuntimeError("boom"))
    def test_execute_plan_replans_runtime_local_failure(self, execute_inferred, execute_ai_step, console):
        plan = [
            {"type": "local", "command": "/readme", "args": [], "source": "generate readme"},
        ]
        main.execute_plan(plan, project=None)
        prompt = execute_ai_step.call_args.args[0]
        self.assertIn("boom", prompt)
        self.assertIn("generate readme", prompt)

    def test_extract_existing_path_prefers_real_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "demo.py")
            with open(path, "w", encoding="utf-8") as f:
                f.write("print('hi')\n")

            current = os.getcwd()
            try:
                os.chdir(tmp)
                self.assertEqual(main.extract_existing_path("please explain demo.py"), "demo.py")
            finally:
                os.chdir(current)


if __name__ == "__main__":
    unittest.main()
