import os
import shutil
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.markup import escape
from module.router import send_request

console = Console()

def read_file(filepath):
    filepath = os.path.expanduser(filepath)
    if not os.path.exists(filepath):
        console.print(f"[red]❌ File not found: {filepath}[/red]")
        return None
    with open(filepath, "r") as f:
        return f.read()

def show_diff(old, new):
    console.print(Panel("[bold yellow]OLD CODE[/bold yellow]"))
    console.print(Syntax(old, "python", theme="monokai", line_numbers=True))
    console.print(Panel("[bold green]NEW CODE[/bold green]"))
    console.print(Syntax(new, "python", theme="monokai", line_numbers=True))

def confirm(question):
    ans = input(f"\n👉 {question} (yes/no): ").strip().lower()
    return ans == "yes"

def clean(content):
    return (content.strip()
            .removeprefix("```python")
            .removeprefix("```javascript")
            .removeprefix("```html")
            .removeprefix("```")
            .removesuffix("```")
            .strip())

def safe_edit(filepath, instruction):
    filepath = os.path.expanduser(filepath)
    console.print(f"\n📂 Reading [cyan]{filepath}[/cyan]...")
    content = read_file(filepath)
    if not content:
        return
    if not confirm("Proceed to AI analysis?"):
        console.print("[yellow]⛔ Cancelled.[/yellow]")
        return
    console.print("\n🧠 Sending to AI...")
    prompt = (f"{instruction}\n\nFile: {filepath}\n\n```python\n{content}\n```\n\n"
              "Return ONLY the improved code, no explanation.")
    new_content = send_request(prompt, task_type="coding")
    if not new_content:
        console.print("[red]❌ AI returned nothing.[/red]")
        return
    new_content = clean(new_content)
    if not confirm("Proceed to preview changes?"):
        console.print("[yellow]⛔ Cancelled.[/yellow]")
        return
    show_diff(content, new_content)
    if not confirm("Apply these changes?"):
        console.print("[yellow]⛔ Cancelled.[/yellow]")
        return
    backup = filepath + ".bak"
    shutil.copy2(filepath, backup)
    console.print(f"💾 Backup saved: [cyan]{backup}[/cyan]")
    if not confirm("Proceed to write file?"):
        console.print("[yellow]⛔ Cancelled.[/yellow]")
        return
    with open(filepath, "w") as f:
        f.write(new_content)
    console.print(f"[green]✅ File updated: {filepath}[/green]")

def explain_file(filepath):
    content = read_file(filepath)
    if not content:
        return
    console.print(f"\n🧠 Analyzing [cyan]{filepath}[/cyan]...")
    prompt = f"Explain this code clearly and concisely:\n\n```python\n{content}\n```"
    result = send_request(prompt, task_type="reasoning")
    if result:
        console.print(Panel(escape(result), title="📖 Explanation", border_style="cyan"))

def create_file_ai(filepath, description):
    filepath = os.path.expanduser(filepath)
    ext = os.path.splitext(filepath)[1]
    prompt = (
        f"Generate the full contents of a new {ext} file.\n\n"
        f"Description: {description}\n\n"
        "Output only the raw file content, no commentary, no markdown fences."
    )
    console.print("\n🧠 Generating file content...")
    result = send_request(prompt, task_type="coding")
    if not result:
        console.print("[red]❌ Failed to generate content.[/red]")
        return
    result = clean(result)
    console.print(Panel(escape(result), title=f"📄 Preview: {filepath}", border_style="cyan"))
    if not confirm(f"Save as {filepath}?"):
        console.print("[yellow]⛔ Cancelled.[/yellow]")
        return
    if os.path.exists(filepath):
        shutil.copy2(filepath, filepath + ".bak")
        console.print(f"💾 Backup saved: [cyan]{filepath}.bak[/cyan]")
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(result)
    console.print(f"[green]✅ Created: {filepath}[/green]")

def add_to_file(filepath, instruction):
    filepath = os.path.expanduser(filepath)
    content = read_file(filepath)
    if not content:
        return
    if not confirm("Proceed to AI processing?"):
        console.print("[yellow]⛔ Cancelled.[/yellow]")
        return
    console.print("\n🧠 Processing...")
    prompt = (
        f"Here is an existing file:\n\n```\n{content}\n```\n\n"
        f"Task: {instruction}\n\n"
        "Rules:\n"
        "- Keep all existing code intact\n"
        "- Add the new feature cleanly\n"
        "- Return the COMPLETE updated file\n"
        "- No explanation, no markdown fences"
    )
    new_content = send_request(prompt, task_type="coding")
    if not new_content:
        console.print("[red]❌ AI returned nothing.[/red]")
        return
    new_content = clean(new_content)
    if not confirm("Proceed to preview?"):
        console.print("[yellow]⛔ Cancelled.[/yellow]")
        return
    show_diff(content, new_content)
    if not confirm("Apply changes?"):
        console.print("[yellow]⛔ Cancelled.[/yellow]")
        return
    shutil.copy2(filepath, filepath + ".bak")
    console.print(f"💾 Backup: [cyan]{filepath}.bak[/cyan]")
    if not confirm("Proceed to write?"):
        console.print("[yellow]⛔ Cancelled.[/yellow]")
        return
    with open(filepath, "w") as f:
        f.write(new_content)
    console.print(f"[green]✅ Updated: {filepath}[/green]")
