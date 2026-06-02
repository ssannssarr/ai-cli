import os


SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "node_modules",
}

MAX_FILE_CHARS = 12000
MAX_TOTAL_CHARS = 180000


def is_probably_text(path):
    try:
        with open(path, "rb") as f:
            chunk = f.read(2048)
    except OSError:
        return False

    if b"\x00" in chunk:
        return False
    return True


def iter_repo_files(root="."):
    root = os.path.abspath(root)
    for current_root, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            path = os.path.join(current_root, name)
            rel_path = os.path.relpath(path, root)
            if not is_probably_text(path):
                continue
            yield rel_path, path


def collect_repo_context(root=".", max_file_chars=MAX_FILE_CHARS, max_total_chars=MAX_TOTAL_CHARS):
    root = os.path.abspath(root)
    sections = []
    files_read = 0
    files_truncated = 0
    total_chars = 0

    for rel_path, path in iter_repo_files(root):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError:
            continue

        if total_chars >= max_total_chars:
            break

        if len(content) > max_file_chars:
            content = content[:max_file_chars]
            files_truncated += 1

        remaining = max_total_chars - total_chars
        if len(content) > remaining:
            content = content[:remaining]
            files_truncated += 1

        sections.append(f"--- FILE: {rel_path} ---\n{content}")
        total_chars += len(content)
        files_read += 1

    return {
        "root": root,
        "files_read": files_read,
        "files_truncated": files_truncated,
        "total_chars": total_chars,
        "context": "\n\n".join(sections),
    }


def build_repo_analysis_prompt(request, root="."):
    repo = collect_repo_context(root=root)
    if request:
        task = request.strip()
    else:
        task = "Analyze this repository. Summarize the architecture, major modules, key workflows, and important risks."

    prompt = (
        f"{task}\n\n"
        "You are analyzing the local repository contents below.\n"
        "Read the repository structure and code, then provide a concise but useful analysis.\n"
        "Call out architecture, entry points, important modules, hidden risks, and notable gaps.\n\n"
        f"Files read: {repo['files_read']}\n"
        f"Files truncated: {repo['files_truncated']}\n"
        f"Characters included: {repo['total_chars']}\n\n"
        f"{repo['context']}"
    )
    return prompt, repo
