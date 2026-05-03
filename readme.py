import os
from rich.console import Console
from rich.panel import Panel
from rich.markup import escape
from router import send_request

console = Console()

def generate_readme():
    console.print("\n📂 Scanning project files...")
    files = [f for f in os.listdir(".") if f.endswith(".py") and not f.startswith("__")]
    
    file_contents = ""
    for f in files:
        try:
            with open(f, "r") as fh:
                content = fh.read()[:500]
            file_contents += f"\n--- {f} ---\n{content}\n"
        except:
            pass

    prompt = (
        f"Generate a professional README.md for this project based on these files:\n\n"
        f"{file_contents}\n\n"
        "Include: project name, description, features, installation, usage, commands list, license.\n"
        "Return only the raw markdown, no explanation."
    )

    console.print("\n🧠 Generating README...")
    result = send_request(prompt, task_type="reasoning")
    
    if not result:
        console.print("[red]❌ Failed to generate README.[/red]")
        return

    console.print(Panel(escape(result), title="📄 README Preview", border_style="cyan"))
    
    ans = input("\n👉 Save as README.md? (yes/no): ").strip().lower()
    if ans != "yes":
        console.print("[yellow]⛔ Cancelled.[/yellow]")
        return

    with open("README.md", "w") as f:
        f.write(result)
    console.print("[green]✅ README.md saved![/green]")
