import os
import subprocess
import requests
from rich.console import Console
from rich.panel import Panel

console = Console()

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "")

def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip()

def handle_github_command(args):
    parts = args.strip().split(" ", 1)
    subcmd = parts[0].lower() if parts else ""
    arg = parts[1].strip() if len(parts) > 1 else ""

    if subcmd == "init":
        github_init(arg)
    elif subcmd == "push":
        github_push(arg)
    elif subcmd == "status":
        github_status()
    else:
        console.print("""[cyan]GitHub commands:
  /github init <name>      → setup git, create repo, first push
  /github push <message>   → commit and push changes
  /github status           → show git status[/cyan]""")

def github_init(repo_name):
    if not repo_name:
        console.print("[red]Usage: /github init <reponame>[/red]")
        return
    if not GITHUB_TOKEN:
        console.print("[red]❌ GITHUB_TOKEN not set.[/red]")
        return
    if not GITHUB_USERNAME:
        console.print("[red]❌ GITHUB_USERNAME not set.[/red]")
        return

    with open(".gitignore", "w") as f:
        f.write("__pycache__/\n*.pyc\n*.bak\n.env\n")
    console.print("[green]✅ .gitignore created[/green]")

    run("git init")
    run("git config --global init.defaultBranch main")
    console.print("[green]✅ Git initialized[/green]")

    console.print(f"\n🌐 Creating GitHub repo '{repo_name}'...")
    response = requests.post(
        "https://api.github.com/user/repos",
        headers={"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"},
        json={"name": repo_name, "private": False, "auto_init": False}
    )

    if response.status_code == 201:
        console.print(f"[green]✅ Repo created[/green]")
    elif response.status_code == 422:
        console.print("[yellow]⚠️  Repo already exists, continuing...[/yellow]")
    else:
        console.print(f"[red]❌ Failed: {response.json().get('message')}[/red]")
        return

    run("git add .")
    run('git commit -m "Initial release"')
    run("git branch -M main")
    run("git remote remove origin")
    run(f"git remote add origin https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{repo_name}.git")
    run("git push -u origin main")

    console.print(Panel(
        f"[bold green]🎉 Done!\nhttps://github.com/{GITHUB_USERNAME}/{repo_name}[/bold green]",
        border_style="green"
    ))

def github_push(message="Update"):
    if not GITHUB_TOKEN or not GITHUB_USERNAME:
        console.print("[red]❌ GITHUB_TOKEN or GITHUB_USERNAME not set.[/red]")
        return

    out, err = run("git status")
    if "not a git repository" in err:
        console.print("\n⚠️  No git repo found. Initializing...")
        run("git init")
        run("git config --global init.defaultBranch main")
        console.print("[green]✅ Git initialized[/green]")

    remote, _ = run("git remote get-url origin")
    if not remote:
        folder = os.path.basename(os.getcwd())
        repo_name = input(f"\n⚠️  No remote found. Repo name? (Enter for '{folder}'): ").strip()
        if not repo_name:
            repo_name = folder

        if not os.path.exists(".gitignore"):
            with open(".gitignore", "w") as f:
                f.write("__pycache__/\n*.pyc\n*.bak\n.env\n")

        response = requests.post(
            "https://api.github.com/user/repos",
            headers={"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"},
            json={"name": repo_name, "private": False, "auto_init": False}
        )

        if response.status_code == 201:
            console.print(f"[green]✅ Repo created: https://github.com/{GITHUB_USERNAME}/{repo_name}[/green]")
        elif response.status_code == 422:
            console.print("[yellow]⚠️  Repo already exists, continuing...[/yellow]")
        else:
            console.print(f"[red]❌ Failed: {response.json().get('message')}[/red]")
            return

        run(f"git remote add origin https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{repo_name}.git")
        console.print("[green]✅ Remote set[/green]")

    console.print("\n🚀 Pushing changes...")
    run("git add .")
    out, err = run(f'git commit -m "{message}"')
    if "nothing to commit" in out:
        console.print("[yellow]⚠️  Nothing to commit.[/yellow]")
        return

    run("git branch -M main")
    out, err = run("git push -u origin main")

    if err and "error" in err.lower():
        console.print(f"[red]❌ Push failed: {err}[/red]")
    else:
        console.print(Panel("[bold green]✅ Pushed successfully![/bold green]", border_style="green"))

def github_status():
    out, _ = run("git status")
    out2, _ = run("git log --oneline -5")
    console.print(Panel(
        f"[bold]Status:[/bold]\n{out}\n\n[bold]Last 5 commits:[/bold]\n{out2}",
        title="📊 Git Status",
        border_style="cyan"
    ))
