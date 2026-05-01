import json
import os
from datetime import datetime

MEMORY_DIR = os.path.expanduser("~/.ai-cli/projects")

def get_project_path(name):
    return os.path.join(MEMORY_DIR, f"{name}.json")

def create_project(name):
    path = get_project_path(name)
    if os.path.exists(path):
        return load_project(name)
    project = {
        "name": name,
        "created": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
        "files": {},
        "history": []
    }
    save_project(name, project)
    return project

def load_project(name):
    path = get_project_path(name)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)

def save_project(name, data):
    data["last_used"] = datetime.now().isoformat()
    with open(get_project_path(name), "w") as f:
        json.dump(data, f, indent=2)

def list_projects():
    return [f.replace(".json", "") for f in os.listdir(MEMORY_DIR) if f.endswith(".json")]

def add_to_history(project, role, content):
    project["history"].append({
        "role": role,
        "content": content,
        "time": datetime.now().isoformat()
    })
    # Keep last 20 exchanges only
    project["history"] = project["history"][-40:]
    return project

def add_file_summary(project, filepath, summary):
    project["files"][filepath] = {
        "summary": summary,
        "updated": datetime.now().isoformat()
    }
    return project

def build_context(project):
    if not project:
        return ""
    
    parts = [f"Project: {project['name']}"]
    
    if project["files"]:
        parts.append("\nFiles worked on:")
        for path, info in project["files"].items():
            parts.append(f"- {path}: {info['summary']}")
    
    if project["history"]:
        parts.append("\nRecent conversation:")
        for msg in project["history"][-10:]:
            parts.append(f"{msg['role'].upper()}: {msg['content'][:200]}")
    
    return "\n".join(parts)
