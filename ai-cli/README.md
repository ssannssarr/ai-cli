# ai-cli

**ai-cli** is a terminal‑based AI assistant that automates coding tasks, project management, file editing, and GitHub integration. Built on top of the OpenRouter API, it routes prompts to the most suitable model for coding, reasoning, or fallback scenarios.

---

## 📁 Project Overview

| Item | Details |
|------|---------|
| **Project Name** | ai-cli |
| **Description** | Command‑line interface for AI‑powered code generation, debugging, and project management. |
| **Features** | • Smart routing of prompts to specialized AI models<br>• Context‑aware project handling (create, load, switch)<br>• File safe editing with diff preview<br>• GitHub integration (issues, PRs, repos)<br>• Continuous chat mode<br>• Automatic README generation |

---

## ⚙️ Installation

```bash
# Clone the repository
git clone https://github.com/ssannssarr/ai-cli.git
cd ai-cli

# (Optional) Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

> **Environment Variables**  
> Ensure the following variables are set in your shell or a `.env` file:
> ```bash
> export OPENROUTER_API_KEY="your_openrouter_api_key"
> export GITHUB_TOKEN="your_github_token"          # optional
> export GITHUB_USERNAME="your_github_username"    # optional
> ```

---

## 🚀 Usage

```bash
# Start the AI CLI
python main.py

# Inside the CLI, use the following commands:

/proj create <name>      # Create a new project
/proj load <name>        # Load an existing project
/proj list               # List all projects
/proj save                # Save current project

/file edit <path>        # Open a file for AI-driven editing
/file show <path>        # Display file content with syntax highlighting
/file diff <old> <new>   # Show diff between two files

/github <subcommand>     # GitHub related actions (e.g., issue, pr, repo)
/github issue create ...  # Create a new issue
/github pr create ...    # Create a new pull request

/chat                    # Enter interactive chat mode
/readme                  # Generate a README file for the current project

/exit                    # Exit the CLI
```

> Commands are prefixed with `/`. Within chat mode, use `/exit` to leave chat and `/clear` to reset the conversation history.

---

## 📚 Commands List

| Command | Description |
|---------|-------------|
| `/proj create <name>` | Initializes a new project directory and metadata. |
| `/proj load <name>`   | Loads an existing project into memory. |
| `/proj list`          | Displays all stored projects. |
| `/proj save`          | Persists the active project's state. |
| `/file edit <file>`   | Sends the file to the AI for editing suggestions. |
| `/file show <file>`   | Renders the file content in the console. |
| `/file diff <before> <after>` | Shows differences using unified diff format. |
| `/github <action>`   | Delegates GitHub actions to `github.py`. |
| `/chat`              | Starts a continuous dialog with the AI. |
| `/readme`            | Generates a README based on the current Python files. |
| `/exit`              | Exits the application or chat mode. |

---

## 🛠️ Archiving & Memory

All project metadata and history are stored under `~/.ai-cli/projects/<project>.json`.  
The CLI automatically remembers the last used project and maintains a history of prompts and responses for context-aware suggestions.

---

## 📝 License

MIT © 2026 ai-cli

---