# ai-cli

**ai-cli** is a terminal‑based AI assistant that leverages OpenRouter models to help you code, reason, manage projects, and interact with GitHub—all from the command line.
It provides an interactive chat, project context management, file safety utilities, README generation, and more.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Running the CLI](#running-the-cli)
- [Core Commands](#core-commands)
- [Project Management](#project-management)
- [File Utilities](#file-utilities)
- [GitHub Integration](#github-integration)
- [Chat Mode](#chat-mode)
- [README Generation](#readme-generation)
- [License](#license)

---

## Features

- **Multi‑model routing** – automatically selects the best OpenRouter model for coding, reasoning, or fallback tasks.
- **Project awareness** – store project metadata, file history, and conversation context.
- **Safe file editing** – preview diffs, explain changes, and edit files with AI assistance.
- **GitHub commands** – quick repo interactions (clone, push, pull, create PR, etc.).
- **Interactive chat** – a Rich‑styled chat UI with `/exit`, `/clear`, and context‑aware suggestions.
- **Automatic README generation** – scan source files and produce a starter README.
- **Extensible command parser** – built on `shlex` for robust argument handling.

---

## Installation

```bash
# clone the repository
git clone https://github.com/yourusername/ai-cli.git
cd ai-cli

# create a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate

# install dependencies
pip install -r requirements.txt
```

### Requirements

- Python 3.9+
- An OpenRouter API key (see [Configuration](#configuration))
- Optional: GitHub token for GitHub commands

---

## Configuration

Create a `.env` file in the project root:

```dotenv
# OpenRouter
OPENROUTER_API_KEY=your_openrouter_api_key_here

# GitHub (optional)
GITHUB_TOKEN=your_github_token_here
GITHUB_USERNAME=your_github_username_here
```

The `config.py` module loads these variables automatically.

---

## Usage

### Running the CLI

```bash
python main.py
```

You will be presented with a Rich‑styled prompt where you can type commands.

### Core Commands

| Command | Description |
|---------|-------------|
| `project new <name>` | Create a new project and set it as active. |
| `project list` | List all saved projects. |
| `project switch <name>` | Switch active context to an existing project. |
| `project info` | Show details of the current project. |
| `file read <path>` | Safely read a file and display its contents. |
| `file edit <path>` | Open an AI‑assisted edit session for a file. |
| `file explain <path>` | Ask the AI to explain a file’s purpose. |
| `github <subcommand>` | Run GitHub‑related actions (`clone`, `push`, `pull`, `pr`, etc.). |
| `chat` | Enter interactive chat mode (`/exit` to quit, `/clear` to reset history). |
| `readme generate` | Auto‑generate a README based on project files. |
| `history show` | Display the command/history log for the active project. |
| `exit` | Quit the CLI. |

(For a full list, type `help` inside the CLI.)

---

## Project Management

Projects are stored under `~/.ai-cli/projects` as JSON files. Each project tracks:

- Project name, creation date, and last used timestamp
- Files added/modified with timestamps
- Chat/history entries for context‑aware AI calls

Key functions are located in `project.py` and `memory.py`.

Commands:

```bash
project new my-awesome-app
project switch my-awesome-app
project info
project list
```

---

## File Utilities

Located in `filesafe.py`:

- `read_file(path)` – safely reads and returns file contents.
- `safe_edit(path, prompt)` – AI‑assisted edit with diff preview.
- `explain_file(path, prompt)` – asks the model to explain code.
- `create_file_ai(path, description)` – generate a new file from a description.
- `add_to_file(path, snippet)` – append AI‑generated code to an existing file.

All operations output Rich panels with clear success/error messages.

---

## GitHub Integration

Implemented in `github.py`. Example usage inside the CLI:

```bash
github clone https://github.com/user/repo.git
github status
github push origin main
github pr create "Fix bug in authentication"
```

The module reads `GITHUB_TOKEN` and `GITHUB_USERNAME` from the environment for authentication.

---

## Chat Mode

Launch with the `chat` command. The chat UI:

- Shows a header panel `[project:chat]` if a project is active.
- Supports `/exit` to quit and `/clear` to reset the conversation.
- Sends prompts to the appropriate model via `router.send_request`.
- Displays AI responses in a formatted Rich panel.

---

## README Generation

Run:

```bash
readme generate
```

The `readme.py` module scans the current directory for Python files, extracts the first 500 characters of each, and builds a starter README using the AI model. The generated content is displayed in the terminal for you to copy or save.

---

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.
