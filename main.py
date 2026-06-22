import argparse
import os
import re
import shlex
import socket
import subprocess
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from module.chat import start_chat
from module.filesafe import safe_edit, explain_file, create_file_ai, add_to_file
from module.github import handle_github_command
from module.memory import add_to_history
from module.models import (
    ModelRegistryError,
    compact_model_name,
    find_model,
    get_active_model,
    list_models,
    price_summary,
    set_active_model,
)
from module.project import (
    auto_detect_project,
    get_active,
    handle_project_command,
    save_active,
)
from module.repoanalyze import build_repo_analysis_prompt
from module.readme import generate_readme
from module.router import send_request
from module.tcp import parse_ports, tcp_scan

console = Console()
HISTORY_PATH = os.path.expanduser("~/.ai-cli/history.txt")

COMMANDS = [
    ("/add", "/add <file> \"request\" - add a feature to a file"),
    ("/analyze", "/analyze [question] - analyze the repo using local file reads"),
    ("/ask", "/ask <question> - ask a one-off question"),
    ("/chat", "/chat - start continuous chat mode"),
    ("/create", "/create <file> \"desc\" - generate a new file"),
    ("/deepsearch", "/deepsearch <query> - run deep AI search"),
    ("/exit", "/exit - quit"),
    ("/explain", "/explain <file> - explain a file"),
    ("/fix", "/fix <file> - safely fix and improve a file"),
    ("/github", "/github init|push|status - GitHub helper commands"),
    ("/help", "/help - show command reference"),
    ("/model", "/model current|list|use|refresh - choose free or paid models"),
    ("/optimize", "/optimize <file> - optimize a file"),
    ("/project", "/project new|use|list|status|clear - project memory"),
    ("/readme", "/readme - generate a README"),
    ("/tcp", "/tcp <host> -p <ports> - scan TCP ports"),
]

PROMPT_STYLE = Style.from_dict(
    {
        "prompt": "ansigreen bold",
        "completion-menu.completion": "bg:#1f2937 #d1d5db",
        "completion-menu.completion.current": "bg:#16a34a #ffffff bold",
        "completion-menu.meta.completion": "bg:#111827 #9ca3af",
        "completion-menu.meta.completion.current": "bg:#15803d #ffffff",
        "scrollbar.background": "bg:#111827",
        "scrollbar.button": "bg:#4b5563",
    }
)


class SlashCommandCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if not text.startswith("/") or " " in text:
            return

        word = document.get_word_before_cursor(WORD=True)
        for command, description in COMMANDS:
            if command.startswith(word):
                yield Completion(
                    command,
                    start_position=-len(word),
                    display=command,
                    display_meta=description,
                )


PROMPT_SESSION = None


def get_prompt_session():
    global PROMPT_SESSION
    if PROMPT_SESSION is not None:
        return PROMPT_SESSION

    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    PROMPT_SESSION = PromptSession(
        history=FileHistory(HISTORY_PATH),
        completer=SlashCommandCompleter(),
        complete_while_typing=True,
        auto_suggest=AutoSuggestFromHistory(),
        enable_history_search=True,
        style=PROMPT_STYLE,
    )
    return PROMPT_SESSION

HELP_TEXT = """
[bold cyan]AI CLI - Command Reference[/bold cyan]

  [green]/fix file.py[/green]           -> Safely fix and improve a file
  [green]/explain file.py[/green]       -> Explain what a file does
  [green]/optimize file.py[/green]      -> Optimize a file for performance
  [green]/create file.py "desc"[/green] -> AI generates a new file
  [green]/add file.py "what"[/green]    -> AI adds feature to existing file
  [green]/analyze[/green]               -> Analyze the repository from local files
  [green]/ask your question[/green]     -> Ask anything directly
  [green]/chat[/green]                  -> Start continuous chat mode
  [green]/project new <name>[/green]    -> Create new project
  [green]/project use <name>[/green]    -> Load existing project
  [green]/project list[/green]          -> Show all projects
  [green]/project status[/green]        -> Show active project
  [green]/project clear[/green]         -> Unload project
  [green]/github init <name>[/green]    -> Create repo and push code
  [green]/github push <message>[/green] -> Commit and push changes
  [green]/github status[/green]         -> Show git status
  [green]/model current[/green]         -> Show selected OpenRouter model
  [green]/model list free[/green]       -> Show available free models
  [green]/model list paid[/green]       -> Show available paid models
  [green]/model use <model-id>[/green]  -> Save active model
  [green]/model refresh[/green]         -> Refresh OpenRouter model cache
  [green]/readme[/green]                -> Generate a README for the project
  [green]/deepsearch <query>[/green]    -> Perform a deep AI search
  [green]/tcp <host> -p 1-1024[/green]  -> TCP port scan on target
  [green]/help[/green]                  -> Show this menu
  [green]/exit[/green]                  -> Quit

[dim]Everything is confirmed before applying. Nothing changes without your approval.[/dim]
"""

LOCAL_TOOL_HINT = (
    "[dim]Plain English works too: 'analyze the repo', 'explain main.py', "
    "'scan localhost ports 22,80', 'list free models', 'project status'.[/dim]"
)


def draw_prompt_box(project):
    project_name = project["name"] if project else "none"
    model_name = compact_model_name(get_active_model())
    cwd = os.path.basename(os.getcwd()) or os.getcwd()
    status = f" ai-cli | project: {project_name} | model: {model_name} | cwd: {cwd} | /help "
    width = max(64, min(console.width, 110))
    inner_width = width - 2
    status_line = status[:inner_width].ljust(inner_width, "-")

    console.print(f"\n[bright_black]+{status_line}+[/bright_black]")
    console.print(
        "[bright_black]|[/bright_black] "
        "[dim]Type / to browse commands, Tab to complete, or ask naturally[/dim]"
    )
    user_input = get_prompt_session().prompt(
        HTML("<ansigreen><b>| ></b></ansigreen> "),
    )
    console.print(f"[bright_black]+{'-' * inner_width}+[/bright_black]")
    return user_input.strip()


def remember_exchange(project, user_text=None, assistant_text=None):
    if not project:
        return
    if user_text:
        add_to_history(project, "user", user_text)
    if assistant_text:
        add_to_history(project, "assistant", assistant_text)
    save_active()


def tokenize_natural_input(user_input):
    try:
        return shlex.split(user_input)
    except ValueError:
        return user_input.split()


def _strip_token(token):
    return token.strip().strip(".,:;!?()[]{}")


def extract_existing_path(user_input):
    quoted = re.findall(r'["\']([^"\']+)["\']', user_input)
    candidates = quoted + tokenize_natural_input(user_input)

    for candidate in candidates:
        token = _strip_token(candidate)
        if not token:
            continue
        expanded = os.path.expanduser(token)
        if os.path.exists(expanded):
            return token
    return None


def extract_fileish_token(user_input):
    for candidate in re.findall(r'[\w./~:-]+\.\w+', user_input):
        token = _strip_token(candidate)
        if token:
            return token
    return None


def extract_host(user_input):
    patterns = [
        r"(?:scan|check|probe)\s+([a-zA-Z0-9][a-zA-Z0-9.-]*(?:\.[a-zA-Z]{2,})?|localhost|\d{1,3}(?:\.\d{1,3}){3})",
        r"(?:host|server|target)\s+([a-zA-Z0-9][a-zA-Z0-9.-]*(?:\.[a-zA-Z]{2,})?|localhost|\d{1,3}(?:\.\d{1,3}){3})",
    ]
    for pattern in patterns:
        match = re.search(pattern, user_input, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_ports(user_input):
    match = re.search(r"ports?\s+([0-9,\-\s]+)", user_input, flags=re.IGNORECASE)
    if not match:
        return None
    ports = re.sub(r"\s+", "", match.group(1))
    return ports or None


def infer_file_command(user_input, lowered):
    path = extract_existing_path(user_input)

    if any(keyword in lowered for keyword in ("explain", "describe this file", "what does")) and path:
        return ("/explain", [path])

    if any(keyword in lowered for keyword in ("optimize", "improve performance", "speed up")) and path:
        return ("/optimize", [path])

    if any(keyword in lowered for keyword in ("fix", "debug", "repair")) and path:
        return ("/fix", [path])

    if "add " in lowered and path:
        before, _, after = user_input.partition(path)
        request = (before + after).strip(" ,.")
        request = re.sub(r"(?i)^add\b", "", request).strip(" ,.")
        request = re.sub(r"(?i)\bto\b$", "", request).strip(" ,.")
        if request:
            return ("/add", [path, request])

    create_keywords = ("create", "generate", "make")
    if any(keyword in lowered for keyword in create_keywords):
        path = extract_fileish_token(user_input)
        if path:
            description = re.sub(rf'(?i)\b{re.escape(path)}\b', "", user_input, count=1).strip(" ,.")
            description = re.sub(r"(?i)^(create|generate|make)\s+", "", description).strip(" ,.")
            description = re.sub(r"(?i)^file\s+", "", description).strip(" ,.")
            if description:
                return ("/create", [path, description])

    return None


def infer_model_command(user_input, lowered):
    if "model" not in lowered and not any(term in lowered for term in ("free models", "paid models")):
        return None

    if any(term in lowered for term in ("current model", "active model", "which model")):
        return ("/model", ["current"])
    if any(term in lowered for term in ("refresh models", "update models", "sync models")):
        return ("/model", ["refresh"])
    if "free model" in lowered or "free models" in lowered:
        if any(term in lowered for term in ("list", "show", "available", "what are")):
            return ("/model", ["list", "free"])
    if "paid model" in lowered or "paid models" in lowered:
        if any(term in lowered for term in ("list", "show", "available", "what are")):
            return ("/model", ["list", "paid"])

    match = re.search(
        r"(?:use|switch to|set)\s+(?:model\s+)?([a-zA-Z0-9._/-]+(?::[a-zA-Z0-9._-]+)?)",
        user_input,
        flags=re.IGNORECASE,
    )
    if match and "/" in match.group(1):
        return ("/model", ["use", match.group(1)])

    return None


def infer_project_command(user_input, lowered):
    if "project" not in lowered:
        return None

    if any(term in lowered for term in ("project status", "active project", "current project")):
        return ("/project", ["status"])
    if any(term in lowered for term in ("list projects", "show projects", "saved projects")):
        return ("/project", ["list"])
    if any(term in lowered for term in ("clear project", "unload project", "close project")):
        return ("/project", ["clear"])

    create_match = re.search(r"(?:create|new)\s+project\s+([^\s]+)", user_input, flags=re.IGNORECASE)
    if create_match:
        return ("/project", ["new", create_match.group(1)])

    use_match = re.search(r"(?:use|load|open|switch to)\s+project\s+([^\s]+)", user_input, flags=re.IGNORECASE)
    if use_match:
        return ("/project", ["use", use_match.group(1)])

    return None


def infer_github_command(user_input, lowered):
    if not any(term in lowered for term in ("github", "git status", "repo status", "commit and push", "push")):
        return None

    if any(term in lowered for term in ("github status", "git status", "repo status")):
        return ("/github", ["status"])

    init_match = re.search(r"(?:init|initialize|create)\s+(?:github\s+)?repo(?:sitory)?\s+([^\s]+)", user_input, flags=re.IGNORECASE)
    if init_match:
        return ("/github", ["init", init_match.group(1)])

    push_match = re.search(
        r"(?:push|commit and push)(?:\s+(?:to\s+github)?)?(?:\s+with\s+message)?\s+(.+)",
        user_input,
        flags=re.IGNORECASE,
    )
    if push_match and "push" in lowered:
        message = push_match.group(1).strip().strip("\"'")
        if message and message.lower() not in {"to github", "github"}:
            return ("/github", ["push", message])
        return ("/github", ["push"])

    return None


def infer_tcp_command(user_input, lowered):
    if not any(term in lowered for term in ("scan", "port", "tcp")):
        return None

    host = extract_host(user_input)
    if not host:
        return None

    args = [host]
    ports = extract_ports(user_input)
    if ports:
        args.extend(["-p", ports])
    return ("/tcp", args)


def split_planner_steps(user_input):
    text = user_input.strip()
    if not text:
        return []

    parts = re.split(
        r"\s*(?:,?\s+then\s+|,?\s+and\s+then\s+|;\s*|\s*->\s*|\n+)\s*",
        text,
        flags=re.IGNORECASE,
    )
    steps = []
    for part in parts:
        cleaned = part.strip(" ,.")
        if not cleaned:
            continue
        steps.append(cleaned)
    return steps or [text]


def normalize_followup_step(step, previous_step):
    lowered = step.lower()
    previous_lowered = previous_step.lower() if previous_step else ""

    if "readme" in previous_lowered and lowered.startswith("commit and push"):
        return f"github {step}"
    if "project" in previous_lowered and lowered in {"status", "clear", "list"}:
        return f"project {step}"
    if "model" in previous_lowered and any(token in lowered for token in ("current", "refresh", "free", "paid", "use ")):
        return f"model {step}"
    return step


def build_execution_plan(user_input):
    raw_steps = split_planner_steps(user_input)
    if len(raw_steps) <= 1:
        command = infer_builtin_command(user_input)
        if command:
            return [{"type": "local", "command": command[0], "args": command[1], "source": user_input}]
        return [{"type": "ai", "prompt": user_input, "source": user_input}]

    plan = []
    previous_step = None
    for raw_step in raw_steps:
        step = normalize_followup_step(raw_step, previous_step)
        inferred = infer_builtin_command(step)
        if inferred:
            plan.append({"type": "local", "command": inferred[0], "args": inferred[1], "source": raw_step})
        else:
            plan.append({"type": "ai", "prompt": step, "source": raw_step})
        previous_step = step
    return plan


def print_execution_plan(plan):
    if len(plan) <= 1:
        return

    console.print("\n[cyan]Plan:[/cyan]")
    for index, step in enumerate(plan, start=1):
        if step["type"] == "local":
            rendered = " ".join([step["command"]] + [shlex.quote(arg) for arg in step["args"]])
            console.print(f"  {index}. local -> {rendered}")
        else:
            console.print(f"  {index}. ai -> {step['prompt']}")


def handle_repo_analysis(args, project):
    request = " ".join(args).strip() if args else ""
    prompt, repo = build_repo_analysis_prompt(request)
    console.print(
        f"\n[cyan]Analyzing repository from local files...[/cyan] "
        f"({repo['files_read']} files, {repo['total_chars']} chars)"
    )
    result = send_request(prompt, task_type="reasoning", project=project)
    if result:
        console.print(Panel(result, title="Repository Analysis", border_style="green"))
        original_request = request or "analyze the repo"
        remember_exchange(project, original_request, result)


def validate_local_step(command, args):
    if command in {"/fix", "/optimize", "/explain", "/add"}:
        if not args:
            return False, "missing file path"
        path = os.path.expanduser(args[0])
        if not os.path.exists(path):
            return False, f"file not found: {args[0]}"
        return True, None

    if command == "/create":
        if len(args) < 2:
            return False, "missing file path or description"
        return True, None

    if command == "/tcp":
        if not args:
            return False, "missing host"
        try:
            port_spec = "1-1000"
            if "-p" in args:
                port_spec = args[args.index("-p") + 1]
            parse_ports(port_spec)
        except (IndexError, ValueError) as exc:
            return False, f"invalid tcp arguments: {exc}"
        return True, None

    return True, None


def replan_failed_step(step, error):
    source = step.get("source") or step.get("prompt") or ""
    if step["type"] == "local":
        prompt = (
            f"The local tool plan for this request failed: {error}.\n"
            f"User request: {source}\n"
            "Handle the request directly and explain any limitation briefly."
        )
    else:
        prompt = source
    return {"type": "ai", "prompt": prompt, "source": source, "replanned_from_error": error}


def execute_local_step(step):
    is_valid, error = validate_local_step(step["command"], step["args"])
    if not is_valid:
        return False, error

    try:
        execute_inferred_command(step["command"], step["args"])
    except Exception as exc:
        return False, str(exc)

    return True, None


def execute_ai_step(prompt, project):
    console.print("\n[cyan]Thinking...[/cyan]")
    result = send_request(prompt, project=project)
    if result:
        console.print(Panel(result, title="Answer", border_style="green"))
        remember_exchange(project, prompt, result)


def execute_plan(plan, project):
    print_execution_plan(plan)
    for step in plan:
        if step["type"] == "local":
            success, error = execute_local_step(step)
            if success:
                continue

            console.print(f"[yellow]Step failed, replanning:[/yellow] {error}")
            replanned = replan_failed_step(step, error)
            execute_ai_step(replanned["prompt"], project)
        else:
            execute_ai_step(step["prompt"], project)


def infer_builtin_command(user_input):
    lowered = user_input.lower().strip()

    if any(
        phrase in lowered
        for phrase in ("analyze the repo", "analyze repo", "analyze the repository", "analyze repository")
    ):
        request = re.sub(
            r"(?i)\banalyze\s+(?:the\s+)?repo(?:sitory)?\b",
            "",
            user_input,
            count=1,
        ).strip(" ,.")
        return ("/analyze", [request] if request else [])
    if lowered in {"help", "show help", "open help", "what can you do"}:
        return ("/help", [])
    if lowered in {"exit", "quit", "close ai-cli"}:
        return ("/exit", [])
    if lowered in {"chat", "start chat", "open chat"}:
        return ("/chat", [])
    if any(term in lowered for term in ("generate readme", "create readme", "write readme", "make readme")):
        return ("/readme", [])
    if lowered.startswith("deep search ") or lowered.startswith("deepsearch "):
        query = user_input.split(" ", 2)[-1].strip()
        return ("/deepsearch", [query]) if query else None

    for infer in (
        infer_file_command,
        infer_model_command,
        infer_project_command,
        infer_github_command,
        infer_tcp_command,
    ):
        command = infer(user_input, lowered)
        if command:
            return command

    return None


def execute_inferred_command(command, args):
    rendered = " ".join([command] + [shlex.quote(arg) for arg in args])
    console.print(f"\n[cyan]Using local tool:[/cyan] {rendered}")
    execute_slash_command(command, args)


def handle_deepsearch(args, project):
    if not args:
        console.print("[red]Usage: /deepsearch <query>[/red]")
        return

    query = " ".join(args)
    console.print("\n[cyan]Running deep search...[/cyan]")
    script_path = os.path.join(os.path.dirname(__file__), "module", "search.py")

    try:
        completed = subprocess.run(
            [sys.executable, script_path, query],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as e:
        stderr = getattr(e, "stderr", "") or str(e)
        console.print(f"[red]Deep search failed: {stderr.strip()}[/red]")
        return

    output = completed.stdout.strip()
    if not output:
        console.print("[yellow]No results returned from deep search.[/yellow]")
        return

    console.print(Panel(output, title="Deep Search Results", border_style="blue"))
    remember_exchange(project, assistant_text=output)


def handle_tcp(args):
    scan_parser = argparse.ArgumentParser(prog="/tcp", add_help=False)
    scan_parser.add_argument("host", help="Target hostname or IP")
    scan_parser.add_argument("-p", "--ports", default="1-1000", help="Ports, e.g. 80,1-1024,22,443")
    scan_parser.add_argument("-t", "--timeout", type=float, default=1.0, help="Timeout in seconds")
    scan_parser.add_argument("-w", "--workers", type=int, default=100, help="Concurrent threads")

    try:
        scan_args = scan_parser.parse_args(args)
    except SystemExit:
        return

    try:
        ports = parse_ports(scan_args.ports)
    except ValueError as e:
        console.print(f"[red]Error parsing ports: {e}[/red]")
        return

    console.print(
        f"\n[cyan]Scanning {scan_args.host} on {len(ports)} port(s) "
        f"with timeout {scan_args.timeout}s...[/cyan]"
    )
    open_ports = tcp_scan(scan_args.host, ports, scan_args.timeout, scan_args.workers)

    if not open_ports:
        console.print("[yellow]No open ports found.[/yellow]")
        return

    console.print("\n[bold green]Open ports:[/bold green]")
    for port in open_ports:
        try:
            with socket.create_connection((scan_args.host, port), timeout=1.0) as sock:
                sock.settimeout(1.0)
                banner = sock.recv(1024).decode(errors="ignore").strip()
        except Exception:
            banner = "open"
        console.print(f"  [cyan]{port}/tcp[/cyan]   {banner}")


def print_model_table(models, title):
    table = Table(title=title)
    table.add_column("Model ID", style="cyan", overflow="fold")
    table.add_column("Tier", style="green")
    table.add_column("Context", justify="right")
    table.add_column("Pricing", style="dim", overflow="fold")

    for model in models[:25]:
        context = str(model.get("context_length") or "unknown")
        table.add_row(model["id"], model.get("tier", "unknown"), context, price_summary(model))

    console.print(table)
    if len(models) > 25:
        console.print(f"[dim]Showing 25 of {len(models)} models. Use the model ID with /model use <model-id>.[/dim]")


def handle_model_command(args, confirm_func=input):
    subcmd = args[0].lower() if args else "current"

    if subcmd == "current":
        active = get_active_model()
        if not active:
            console.print("[yellow]No active model selected. Run /model list free.[/yellow]")
            return
        print_model_table([active], "Active Model")
        return

    if subcmd == "refresh":
        try:
            models = list_models(refresh=True)
        except ModelRegistryError as e:
            console.print(f"[red]{e}[/red]")
            return
        console.print(f"[green]Model cache refreshed: {len(models)} text models available.[/green]")
        return

    if subcmd == "list":
        tier = args[1].lower() if len(args) > 1 else "free"
        if tier not in {"free", "paid"}:
            console.print("[red]Usage: /model list free|paid[/red]")
            return
        try:
            models = list_models(tier=tier)
        except ModelRegistryError as e:
            console.print(f"[red]{e}[/red]")
            return
        if not models:
            console.print(f"[yellow]No {tier} models found. Try /model refresh.[/yellow]")
            return
        print_model_table(models, f"{tier.title()} OpenRouter Models")
        return

    if subcmd == "use":
        if len(args) < 2:
            console.print("[red]Usage: /model use <model-id>[/red]")
            return
        model_id = args[1]
        try:
            models = list_models()
        except ModelRegistryError as e:
            console.print(f"[red]{e}[/red]")
            return
        model = find_model(model_id, models)
        if not model:
            console.print(f"[red]Model not found: {model_id}. Try /model refresh.[/red]")
            return
        if model.get("tier") == "paid":
            answer = confirm_func(
                f"This is a paid model ({price_summary(model)}). Save it as active? (yes/no): "
            ).strip().lower()
            if answer != "yes":
                console.print("[yellow]Cancelled.[/yellow]")
                return
        saved = set_active_model(model)
        console.print(f"[green]Active model saved:[/green] {saved['id']} ({saved.get('tier', 'unknown')})")
        return

    console.print("""[cyan]Model commands:
  /model current
  /model list free
  /model list paid
  /model use <model-id>
  /model refresh[/cyan]""")


def execute_slash_command(cmd, args):
    project = get_active()

    if cmd == "/analyze":
        handle_repo_analysis(args, project)

    elif cmd == "/fix":
        if not args:
            console.print("[red]Usage: /fix <filename>[/red]")
        else:
            safe_edit(args[0], "Fix all bugs and improve this code.")

    elif cmd == "/optimize":
        if not args:
            console.print("[red]Usage: /optimize <filename>[/red]")
        else:
            safe_edit(args[0], "Optimize this code for performance and readability.")

    elif cmd == "/explain":
        if not args:
            console.print("[red]Usage: /explain <filename>[/red]")
        else:
            explain_file(args[0])

    elif cmd == "/create":
        if len(args) < 2:
            console.print('[red]Usage: /create <filename> "description"[/red]')
        else:
            create_file_ai(args[0], args[1])

    elif cmd == "/add":
        if len(args) < 2:
            console.print('[red]Usage: /add <filename> "what to add"[/red]')
        else:
            add_to_file(args[0], args[1])

    elif cmd == "/chat":
        start_chat()

    elif cmd == "/project":
        save_active()
        handle_project_command(" ".join(args))

    elif cmd == "/github":
        handle_github_command(" ".join(args))

    elif cmd == "/model":
        handle_model_command(args)

    elif cmd == "/readme":
        console.print("\n[cyan]Generating README...[/cyan]")
        result = generate_readme()
        if result:
            console.print(Panel(result, title="README", border_style="magenta"))
            remember_exchange(project, assistant_text=result)

    elif cmd == "/ask":
        if not args:
            console.print("[red]Usage: /ask your question here[/red]")
            return
        question = " ".join(args)
        console.print("\n[cyan]Thinking...[/cyan]")
        result = send_request(question, project=project)
        if result:
            console.print(Panel(result, title="Answer", border_style="green"))
            remember_exchange(project, question, result)

    elif cmd == "/deepsearch":
        handle_deepsearch(args, project)

    elif cmd == "/tcp":
        handle_tcp(args)

    elif cmd == "/help":
        console.print(Panel(HELP_TEXT, border_style="cyan"))

    elif cmd == "/exit":
        save_active()
        console.print("[yellow]Goodbye![/yellow]")
        sys.exit(0)

    else:
        console.print(f"[red]Unknown command: {cmd}. Type /help for assistance.[/red]")


def handle_command(user_input):
    project = get_active()

    if not user_input.startswith("/"):
        plan = build_execution_plan(user_input)
        execute_plan(plan, project)
        return

    try:
        parts = shlex.split(user_input)
    except ValueError as ve:
        console.print(f"[red]Error parsing command: {ve}[/red]")
        return

    cmd = parts[0].lower()
    args = parts[1:]
    execute_slash_command(cmd, args)


def main():
    console.print(
        Panel(
            "[bold green]AI-CLI Ready[/bold green]\n"
            "Type [cyan]/help[/cyan] for commands or ask naturally to trigger local tools.",
            border_style="green",
        )
    )
    console.print(LOCAL_TOOL_HINT)

    auto_detect_project()

    while True:
        try:
            user_input = draw_prompt_box(get_active())
            if not user_input:
                continue
            handle_command(user_input)

        except (KeyboardInterrupt,EOFError):
            save_active()
            console.print("\n[yellow]Goodbye![/yellow]")
            sys.exit(0)


if __name__ == "__main__":
    main()
