<h1 align="center">ai-cli</h1>

---
---

`ai-cli` is a terminal-based AI assistant that uses OpenRouter models to help with coding, reasoning, project memory, GitHub actions, README generation, and TCP scanning from the command line.

## Features:

- Multi-model routing through OpenRouter with retry and fallback behavior.
- Live free/paid OpenRouter model selection with cached model metadata.
- Project-aware context saved under `~/.ai-cli/projects`.
- Gemini-style status line, boxed prompt, and slash-command autocomplete.
- AI-assisted file utilities with confirmations, previews, and backups.
- Interactive chat mode with short local conversation history.
- GitHub helpers for repo initialization, status, commits, and pushes.
- README generation from local Python files.
- TCP port scanning with configurable ports, timeout, and worker count.

## Installation:

```bash
git clone https://github.com/ssannssarr/ai-cli.git
cd ai-cli

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

On macOS or Linux, activate the virtual environment with:

```bash
source .venv/bin/activate
```

## Configuration:

Create a `.env` file in the project root:

```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here

GITHUB_TOKEN=your_github_token_here
GITHUB_USERNAME=your_github_username_here
```

`OPENROUTER_API_KEY` is required for AI requests. The GitHub values are only needed for `/github` commands.

## Usage:

Start the CLI:

```bash
python main.py
```

Then type slash commands or ask a normal question directly. Start a line with `/` to browse matching commands, and press Tab to complete the selected command.

## Commands:

| Command | Description |
|---------|-------------|
| `/ask <question>` | Ask a one-off AI question. |
| `/chat` | Enter interactive chat mode. |
| `/fix <path>` | Ask AI to fix and improve a file after confirmation. |
| `/optimize <path>` | Ask AI to optimize a file after confirmation. |
| `/explain <path>` | Ask AI to explain a file. |
| `/create <path> "description"` | Generate a new file from a description. |
| `/add <path> "request"` | Add a feature to an existing file after confirmation. |
| `/project new <name>` | Create and load a project. |
| `/project use <name>` | Load an existing project. |
| `/project list` | Show saved projects. |
| `/project status` | Show the active project. |
| `/project clear` | Unload the active project. |
| `/github init <name>` | Initialize git, create a GitHub repo, and push. |
| `/github push <message>` | Commit and push changes. |
| `/github status` | Show git status and recent commits. |
| `/model current` | Show the active OpenRouter model. |
| `/model list free` | Show currently available free text models. |
| `/model list paid` | Show currently available paid text models. |
| `/model use <model-id>` | Save the active model. Paid models require confirmation. |
| `/model refresh` | Refresh the OpenRouter model cache. |
| `/readme` | Generate a README preview and optionally save it. |
| `/deepsearch <query>` | Run the bundled deep-search script. |
| `/tcp <host> -p <ports>` | Scan TCP ports, for example `/tcp example.com -p 80,443`. |
| `/help` | Show the command menu. |
| `/exit` | Quit the CLI. |

## Project Memory

Projects are stored as JSON files under `~/.ai-cli/projects`. An active project can add recent conversation and file summaries to future AI prompts.

```bash
/project new my-awesome-app
/project use my-awesome-app
/project status
/project list
```

## Model Selection

Models are fetched from OpenRouter's live Models API and cached under `~/.ai-cli/models_cache.json`. The selected model is saved in `~/.ai-cli/config.json`.

```bash
/model refresh
/model list free
/model list paid
/model use openai/gpt-oss-120b:free
/model current
```

If no model is selected, the router uses the first cached or fetched free model. Paid models can be selected, but the CLI asks for confirmation before saving them.

## Development

Install dependencies, then run the tests:

```bash
python -m unittest
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
