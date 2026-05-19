try:
    import readline
except ImportError:
    pass

import sys
import shlex
import subprocess
import os
from rich.console import Console
from rich.panel import Panel
from module.router import send_request
from module.filesafe import safe_edit, explain_file, create_file_ai, add_to_file
from module.project import (
    handle_project_command, get_active,
    save_active, auto_detect_project
)
from module.memory import add_to_history
from module.github import handle_github_command
from module.chat import start_chat
from module.readme import generate_readme
from module.tcp import tcp_scan, parse_ports

console = Console()

HELP_TEXT = """
[bold cyan]AI CLI — Command Reference[/bold cyan]

  [green]/fix file.py[/green]           → Safely fix and improve a file
  [green]/explain file.py[/green]       → Explain what a file does
  [green]/optimize file.py[/green]      → Optimize a file for performance
  [green]/create file.py "desc"[/green] → AI generates a new file
  [green]/add file.py "what"[/green]    → AI adds feature to existing file
  [green]/ask your question[/green]     → Ask anything directly
  [green]/chat[/green]                  → Start continuous chat mode
  [green]/project new <name>[/green]    → Create new project
  [green]/project use <name>[/green]    → Load existing project
  [green]/project list[/green]          → Show all projects
  [green]/project status[/green]        → Show active project
  [green]/project clear[/green]         → Unload project
  [green]/github init <name>[/green]    → Create repo and push code
  [green]/github push <message>[/green] → Commit and push changes
  [green]/github status[/green]         → Show git status
  [green]/readme[/green]                → Generate a README for the project
  [green]/deepsearch <query>[/green]    → Perform a deep AI search
  [green]/help[/green]                  → Show this menu
  [green]/exit[/green]                  → Quit
  [green]/tcp <host> -p 1-1024[/green]  → TCP port scan on target 

[dim]Everything is confirmed before applying. Nothing changes without your approval.[/dim]
"""

def handle_command(user_input):
    if not user_input.startswith("/"):
        project = get_active()
        console.print("\n🧠 Thinking...")
        result = send_request(user_input, project=project)
        if result:
            console.print(Panel(result, title="💬 Answer", border_style="green"))
            if project:
                add_to_history(project, "user", user_input)
                add_to_history(project, "assistant", result)
                save_active()
        return

    try:
        parts = shlex.split(user_input)
    except ValueError as e:
        console.print(f"[red]Error parsing command: {e}[/red]")
        return

    cmd = parts[0].lower()
    args = parts[1:]
    project = get_active()

    if cmd == "/fix":
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

    elif cmd == "/readme":
        console.print("\n🧠 Generating README...")
        result = generate_readme()
        if result:
            console.print(Panel(result, title="📄 README", border_style="magenta"))
            if project:
                add_to_history(project, "assistant", result)
                save_active()

    elif cmd == "/ask":
        if not args:
            console.print("[red]Usage: /ask your question here[/red]")
            return
        question = " ".join(args)
        console.print("\n🧠 Thinking...")
        result = send_request(question, project=project)
        if result:
            console.print(Panel(result, title="💬 Answer", border_style="green"))
            if project:
                add_to_history(project, "user", question)
                add_to_history(project, "assistant", result)
                save_active()

    elif cmd == "/deepsearch":
        if not args:
            console.print("[red]Usage: /deepsearch <query>[/red]")
        else:
            query = " ".join(args)
            console.print("\n🧠 Running deep search...")
            script_path = os.path.expanduser("~/ai-cli/ai-cli/search.py")
            try:
                completed = subprocess.run(
                    [sys.executable, script_path, query],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                output = completed.stdout.strip()
                if output:
                    console.print(Panel(output, title="🔎 Deep Search Results", border_style="blue"))
                    if project:
                        add_to_history(project, "assistant", output)
                        save_active()
                else:
                    console.print("[yellow]No results returned from deep search.[/yellow]")
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Deep search failed: {e.stderr.strip()}[/red]")

    elif cmd == "/tcp":
        # Use argparse for clean sub‑argument parsing
        import argparse
        scan_parser = argparse.ArgumentParser(prog="/scan", add_help=False)
        scan_parser.add_argument("host", help="Target hostname or IP")
        scan_parser.add_argument("-p", "--ports", default="1-1000", help="Ports (e.g., 80,1-1024,22,443)")
        scan_parser.add_argument("-t", "--timeout", type=float, default=1.0, help="Timeout in seconds")
        scan_parser.add_argument("-w", "--workers", type=int, default=100, help="Concurrent threads")
        try:
            scan_args = scan_parser.parse_args(args)
        except SystemExit:
            # argparse prints its own error; we just continue
            return

        host = scan_args.host
        try:
            ports = parse_ports(scan_args.ports)
        except ValueError as e:
            console.print(f"[red]Error parsing ports: {e}[/red]")
            return

        console.print(f"\n🔎 Scanning {host} on {len(ports)} port(s) with timeout {scan_args.timeout}s...")
        open_ports = tcp_scan(host, ports, scan_args.timeout, scan_args.workers)

        if open_ports:
            console.print("\n[bold green]Open ports:[/bold green]")
            for port in open_ports:
                # Quick banner grab (optional)
                try:
                    with socket.create_connection((host, port), timeout=1.0) as sock:
                        sock.settimeout(1.0)
                        banner = sock.recv(1024).decode(errors="ignore").strip()
                except Exception:
                    banner = "open"
                console.print(f"  [cyan]{port}/tcp[/cyan]   {banner}")
        else:
            console.print("[yellow]No open ports found.[/yellow]")
    elif cmd == "/help":
        console.print(Panel(HELP_TEXT, border_style="cyan"))

    elif cmd == "/exit":
        save_active()
        console.print("[yellow] ~K Goodbye![/yellow]")
        sys.exit(0)





    else:
        console.print(f"[red]Unknown command: {cmd}. Type /help for assistance.[/red]")

def main():
    console.print(Panel(
        "[bold green]🤖 Codex CLI Ready[/bold green]\nType [cyan]/help[/cyan] for commands or just ask anything.",
        border_style="green"
    ))

    auto_detect_project()

    while True:
        try:
            project = get_active()
            label = f"[{project['name']}]" if project else ""
            user_input = input(f"\n{label}> ").strip()
            if not user_input:
                continue
            handle_command(user_input)

        except KeyboardInterrupt:
            save_active()
            console.print("\n[yellow]👋 Goodbye![/yellow]")
            sys.exit(0)

if __name__ == "__main__":
    main()
