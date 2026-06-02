<h1 align="center">Contributing to ai-cli</h1>

---

<b>
Thanks for wanting to contribute to `ai-cli`.

This project is a terminal-based AI assistant built around slash commands, OpenRouter models, project memory, file helpers, GitHub helpers, README generation, and small developer tools like TCP scanning.

The goal is simple: keep the CLI useful, safe, and easy to understand.
</b>

---
## Before You Start:

Please check the existing issues first.

If you want to work on something:
<i>
1. Comment on the issue and say you want to work on it.
2. Wait for a short confirmation if the issue is already active or unclear.
3. Fork the repo.
4. Create a new branch.
5. Make your changes.
6. Test your changes.
7. Open a pull request.
</i>

Small fixes are welcome. Even tiny cleanups count if they make the project better.

---

## Setup:

***Clone your fork:***

```bash
git clone https://github.com/<your-username>/ai-cli.git
cd ai-cli
```

***Create a virtual environment:***

```bash
python -m venv .venv
```

***Activate it:***

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

***Install dependencies:***

```bash
pip install -r requirements.txt
```

***Create a `.env` file:***

```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here

GITHUB_TOKEN=your_github_token_here
GITHUB_USERNAME=your_github_username_here
```

`OPENROUTER_API_KEY` is required for AI requests. GitHub values are only needed for `/github` commands.

---

## Run the CLI:

```bash
python main.py
```

***Use:***

```bash
/help
```

inside the CLI to see available commands.

---

## Run Tests:

Before opening a PR, run:

```bash
python -m unittest discover tests
```

If you add logic, try to add tests too.

Good places for tests:
<i>
- model selection
- TCP port parsing
- command parsing
- config/cache behavior
- file safety helpers
</i>

---

## Branch Naming:

Use simple branch names:

```bash
fix/tcp-error
feature/model-command
chore/readme-cleanup
test/tcp-parser
```

No need to overthink it.

---

## Pull Request Style:

Keep PRs focused.

Good PR:
<i>
- fixes one bug
- adds one small feature
- improves one part of docs
- adds tests for one module
</i>

Avoid PRs that change many unrelated things at once.

In your PR, include:

```md
## What changed
- ...

## Why
- ...

## Testing
- [ ] Ran `python -m unittest discover tests`
- [ ] Tested manually with `python main.py`
```
---

## Code Style:

Keep the code readable and boring in the good way.
<i>
- Use clear names.
- Keep functions small when possible.
- Avoid unnecessary clever code.
- Handle errors with useful messages.
- Do not hide failures silently.
- Keep terminal output clean and helpful.
</i>

This project is for humans using a terminal, so messages should be understandable.

---

## Safety Rules:

Some commands can touch files, GitHub, or network targets.

Please keep safety in mind:
<i>
- File-changing commands should ask before writing.
- Keep backups or previews where possible.
- Do not add destructive behavior without confirmation.
- TCP scanning should be used only on systems the user owns or has permission to test.
- Never commit API keys, tokens, or `.env` files.
</i>

---

## Good First Issues:

Good beginner-friendly contributions:
<i>
- add tests for `module/tcp.py`
- improve error messages
- clean README examples
- add command examples
- improve `/help` text
- add safer input validation
- fix typos
</i>

---

## Commit Messages:

Use simple commit messages:

```bash
fix tcp banner import
add model command tests
update readme usage
improve config error message
```

Readable is better than fancy.

---
<div align="center">
<i>
 <h2>Final Note</h2>

This project does not need perfect code from the first try.

Keep it minimal, working, and useful. Do not remove the soul of the app while cleaning it.
</i>
</div>

---