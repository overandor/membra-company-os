#!/usr/bin/env python3
"""
File Miner for Mac Compute Node
Scans user files and converts them into monetizable compute tasks.
"""
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileMiner:
    """Scans filesystem for compute-worthy files and generates tasks."""

    def __init__(self, config: Dict):
        self.config = config
        self.scan_paths = [os.path.expanduser(p) for p in config.get("scan_paths", ["~/Documents"])]
        self.extensions = config.get("task_extensions", [".txt", ".py"])
        self.rewards = config.get("task_rewards", {})
        self.task_queue: List[Dict] = []
        self.processed_files: set = set()
        self.state_file = os.path.expanduser("~/.mac_compute_node/miner_state.json")
        self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file) as f:
                state = json.load(f)
                self.processed_files = set(state.get("processed", []))

    def _save_state(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump({"processed": list(self.processed_files)}, f)

    def scan_for_tasks(self, max_tasks: int = 10) -> List[Dict]:
        """Scan configured paths and return new compute tasks."""
        tasks = []
        for base_path in self.scan_paths:
            if not os.path.exists(base_path):
                continue
            for root, _, files in os.walk(base_path):
                for fname in files:
                    if len(tasks) >= max_tasks:
                        break
                    ext = Path(fname).suffix.lower()
                    if ext not in self.extensions:
                        continue

                    fpath = os.path.join(root, fname)
                    fid = hashlib.sha256(fpath.encode()).hexdigest()[:16]

                    if fid in self.processed_files:
                        continue

                    task = self._file_to_task(fpath, ext, fid)
                    if task:
                        tasks.append(task)
                        self.processed_files.add(fid)

                if len(tasks) >= max_tasks:
                    break

        self._save_state()
        return tasks

    def _file_to_task(self, fpath: str, ext: str, fid: str) -> Optional[Dict]:
        """Convert a file path into a compute task."""
        task_type = self._ext_to_task_type(ext)
        try:
            size = os.path.getsize(fpath)
            if size > 50 * 1024 * 1024:  # Skip >50MB
                return None
            content = self._read_file(fpath, ext)
        except Exception:
            return None

        return {
            "id": fid,
            "type": task_type,
            "file_path": fpath,
            "file_name": os.path.basename(fpath),
            "extension": ext,
            "size_bytes": size,
            "content": content,
            "reward": self.rewards.get(task_type, 0.001),
            "created_at": time.time(),
            "containerize": ext in (".py", ".js"),  # Sandbox code
        }

    def _ext_to_task_type(self, ext: str) -> str:
        mapping = {
            ".pdf": "ocr",
            ".txt": "embed",
            ".py": "code_review",
            ".js": "code_review",
            ".ts": "code_review",
            ".md": "embed",
            ".jpg": "vision",
            ".jpeg": "vision",
            ".png": "vision",
            ".csv": "data_process",
            ".json": "data_process",
        }
        return mapping.get(ext, "generic")

    def _read_file(self, fpath: str, ext: str) -> str:
        """Read file content as string (best effort)."""
        if ext in (".jpg", ".jpeg", ".png"):
            return f"[image: {fpath}]"
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""

    def get_stats(self) -> Dict:
        return {
            "scan_paths": self.scan_paths,
            "processed_files": len(self.processed_files),
            "supported_extensions": self.extensions,
            "task_rewards": self.rewards,
        }


class FileWatcher(FileSystemEventHandler):
    """Watchdog handler for real-time file discovery."""

    def __init__(self, miner: FileMiner):
        self.miner = miner
        self.pending: List[str] = []

    def on_created(self, event):
        if not event.is_directory:
            self.pending.append(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.pending.append(event.src_path)

    def flush(self) -> List[Dict]:
        tasks = []
        for path in set(self.pending):
            ext = Path(path).suffix.lower()
            if ext in self.miner.extensions:
                fid = hashlib.sha256(path.encode()).hexdigest()[:16]
                if fid not in self.miner.processed_files:
                    task = self.miner._file_to_task(path, ext, fid)
                    if task:
                        tasks.append(task)
                        self.miner.processed_files.add(fid)
        self.pending.clear()
        return tasks
