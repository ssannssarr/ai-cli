import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from memory import (
    create_project, load_project, save_project,
    list_projects, add_to_history, build_context
)

console = Console()

# Active project state
current_project = {"data": None}

def get_active():
    return current_project["data"]

def set_active(project):
    current_project["data"] = project

def save_active():
    p = get_active()
    if p:
        save_project(p["name"], p)

def handle_project_command(args):
    parts = args.strip().split(" ", 1)
    subcmd = parts[0].lower() if parts else ""
    name = parts[1].strip() if len(parts) > 1 else ""

    if subcmd == "new":
        if not name:
            console.print("[red]Usage: /project new <name>[/red]")
            return
        p = create_project(name)
        set_active(p)
        console.print(f"[green]✅ Project '{name}' created and loaded.[/green]")

    elif subcmd == "use":
        if not name:
            console.print("[red]Usage: /project use <name>[/red]")
            return
        p = load_project(name)
        if not p:
            console.print(f"[red]❌ Project '{name}' not found. Use /project new {name}[/red]")
            return
        set_active(p)
        console.print(f"[green]✅ Project '{name}' loaded.[/green]")
        _show_project_summary(p)

    elif subcmd == "list":
        projects = list_projects()
        if not projects:
            console.print("[yellow]No projects found.[/yellow]")
            return
        table = Table(title="📁 Saved Projects")
        table.add_column("Name", style="cyan")
        table.add_column("Last Used", style="dim")
        for pname in projects:
            p = load_project(pname)
            table.add_row(pname, p.get("last_used", "unknown")[:19])
        console.print(table)

    elif subcmd == "status":
        p = get_active()
        if not p:
            console.print("[yellow]No active project.[/yellow]")
            return
        _show_project_summary(p)

    elif subcmd == "clear":
        set_active(None)
        console.print("[yellow]Project unloaded.[/yellow]")

    else:
        console.print("""[cyan]Project commands:
  /project new <name>   → Create and load project
  /project use <name>   → Load existing project
  /project list         → Show all projects
  /project status       → Show active project
  /project clear        → Unload project[/cyan]""")

def _show_project_summary(p):
    files = list(p["files"].keys()) or ["none"]
    history_count = len(p["history"])
    console.print(Panel(
        f"[bold]Project:[/bold] {p['name']}\n"
        f"[bold]Files:[/bold] {', '.join(files)}\n"
        f"[bold]History:[/bold] {history_count} messages",
        title="📁 Active Project",
        border_style="cyan"
    ))

def auto_detect_project():
    folder = os.path.basename(os.getcwd())
    p = load_project(folder)
    if p:
        ans = input(f"\n📁 Project '{folder}' found. Load it? (yes/no): ").strip().lower()
        if ans == "yes":
            set_active(p)
            console.print(f"[green]✅ Project '{folder}' loaded.[/green]")
