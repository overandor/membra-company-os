from pathlib import Path
import os, stat
BASE = Path(__file__).resolve().parents[1]
def write(rel_path: str, content: str, executable: bool = False):
    path = BASE / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IEXEC)
    print(f"wrote {rel_path}")
