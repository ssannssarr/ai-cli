from rich.console import Console
from rich.panel import Panel
from module.router import send_request
from module.project import get_active

console = Console()

def start_chat():
    history = []
    project = get_active()
    project_name = project["name"] if project else None
    label = f"[{project_name}:chat]" if project_name else "[chat]"

    console.print(Panel(
        "[bold cyan]💬 Chat Mode[/bold cyan]\n"
        "Type messages to chat with AI.\n"
        "[dim]/exit → quit chat | /clear → reset history[/dim]",
        border_style="cyan"
    ))

    while True:
        try:
            user_input = input(f"\n{label}> ").strip()
            if not user_input:
                continue

            if user_input.lower() == "/exit":
                console.print("[yellow]👋 Exiting chat mode.[/yellow]")
                break

            if user_input.lower() == "/clear":
                history = []
                console.print("[green]✅ History cleared.[/green]")
                continue

            # Build context from history
            history.append({"role": "user", "content": user_input})
            context = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history[-10:]])
            prompt = f"You are a helpful AI assistant. Here is the conversation so far:\n\n{context}\n\nRespond to the last user message."

            console.print("\n🧠 Thinking...")
            result = send_request(prompt, project=project)

            if result:
                console.print(Panel(result, title="💬 AI", border_style="green"))
                history.append({"role": "assistant", "content": result})

        except KeyboardInterrupt:
            console.print("\n[yellow]👋 Exiting chat mode.[/yellow]")
            break
