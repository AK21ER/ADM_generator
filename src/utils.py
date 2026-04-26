from pathlib import Path
import json

def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
