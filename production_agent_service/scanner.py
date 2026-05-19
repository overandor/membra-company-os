#!/usr/bin/env python3
"""
Workspace Scanner — recursively inventories all projects and files.
Identifies git repos, language ecosystems, and project boundaries.
"""

import fnmatch
import json
import os
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Iterator


PROJECT_INDICATORS = [
    ".git",
    "package.json",
    "Cargo.toml",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "Pipfile",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "CMakeLists.txt",
    "Makefile",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "poetry.lock",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "Anchor.toml",
    "next.config.js",
    "nuxt.config.ts",
    "vite.config.ts",
    "vite.config.js",
    "tsconfig.json",
    ".github",
]

SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    "coverage",
    ".idea",
    ".vscode",
    ".gradle",
    ".npm",
    ".yarn",
    ".pnpm-store",
    "out",
    "public",
}

SKIP_PATTERNS = [
    "*.pyc",
    "*.pyo",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.class",
    "*.o",
    "*.a",
    ".DS_Store",
    "Thumbs.db",
    "*.swp",
    "*.swo",
    "*~",
    "*.log",
    "*.tmp",
    "*.temp",
    "*.pid",
    "*.sock",
    "*.zip",
    "*.tar",
    "*.gz",
    "*.rar",
    "*.7z",
    "*.dmg",
    "*.pkg",
    "*.deb",
    "*.rpm",
    "*.exe",
    "*.bin",
    "*.iso",
]


@dataclass
class FileEntry:
    path: str
    rel_path: str
    size: int
    hash: str
    ext: str
    is_binary: bool = False


@dataclass
class Project:
    root: str
    name: str
    project_type: str = "unknown"
    indicators: List[str] = field(default_factory=list)
    files: List[FileEntry] = field(default_factory=list)
    languages: Dict[str, int] = field(default_factory=dict)
    total_size: int = 0
    total_files: int = 0
    secrets_found: List[Dict] = field(default_factory=list)


@dataclass
class ScanResult:
    scanned_at: str
    root_path: str
    projects: List[Project] = field(default_factory=list)
    loose_files: List[FileEntry] = field(default_factory=list)
    total_size: int = 0
    total_files: int = 0


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def is_binary(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
            return b"\x00" in chunk
    except Exception:
        return True


def should_skip_dir(dir_name: str) -> bool:
    return dir_name in SKIP_DIRS or dir_name.startswith(".")


def should_skip_file(file_name: str) -> bool:
    for pat in SKIP_PATTERNS:
        if fnmatch.fnmatch(file_name, pat):
            return True
    if file_name.startswith("."):
        return True
    return False


def detect_project_type(indicators: List[str], files: List[str]) -> str:
    types = []
    if "package.json" in indicators:
        types.append("nodejs")
    if "Cargo.toml" in indicators:
        types.append("rust")
    if any(i in indicators for i in ("pyproject.toml", "setup.py", "requirements.txt", "Pipfile", "poetry.lock")):
        types.append("python")
    if "go.mod" in indicators:
        types.append("go")
    if any(i in indicators for i in ("pom.xml", "build.gradle")):
        types.append("jvm")
    if "CMakeLists.txt" in indicators or "Makefile" in indicators:
        types.append("cpp")
    if "Anchor.toml" in indicators:
        types.append("solana")
    if "Dockerfile" in indicators or "docker-compose.yml" in indicators or "docker-compose.yaml" in indicators:
        types.append("docker")
    if ".git" in indicators:
        types.append("git")
    return " + ".join(types) if types else "unknown"


def scan_workspace(root: Path, max_depth: int = 6) -> ScanResult:
    result = ScanResult(
        scanned_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        root_path=str(root.expanduser().resolve()),
    )

    # First pass: identify project roots
    project_roots: Dict[str, List[str]] = {}
    for dirpath, dirnames, filenames in os.walk(result.root_path):
        depth = len(Path(dirpath).relative_to(result.root_path).parts)
        if depth > max_depth:
            dirnames.clear()
            continue

        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]

        indicators = [f for f in filenames if f in PROJECT_INDICATORS]
        if ".git" in dirnames:
            indicators.append(".git")
        if indicators:
            project_roots[dirpath] = indicators

    # Second pass: build file lists per project / loose files
    assigned_dirs: Set[str] = set()
    project_objs: Dict[str, Project] = {}

    for proj_root, indicators in sorted(project_roots.items(), key=lambda x: len(x[0]), reverse=True):
        # Skip if already assigned to a deeper project
        if any(proj_root.startswith(a + os.sep) for a in assigned_dirs):
            continue
        assigned_dirs.add(proj_root)
        proj = Project(
            root=proj_root,
            name=Path(proj_root).name,
            indicators=indicators,
            project_type=detect_project_type(indicators, []),
        )
        project_objs[proj_root] = proj

    # Collect files
    for dirpath, dirnames, filenames in os.walk(result.root_path):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        rel_base = Path(result.root_path)

        # Find which project this belongs to
        current_proj: Optional[Project] = None
        for proj_root in assigned_dirs:
            if dirpath == proj_root or dirpath.startswith(proj_root + os.sep):
                current_proj = project_objs.get(proj_root)
                break

        for f in filenames:
            if should_skip_file(f):
                continue
            fp = Path(dirpath) / f
            try:
                size = fp.stat().st_size
                rel = str(fp.relative_to(rel_base))
                entry = FileEntry(
                    path=str(fp),
                    rel_path=rel,
                    size=size,
                    hash=sha256_file(fp),
                    ext=Path(f).suffix.lower(),
                    is_binary=is_binary(fp),
                )
                if current_proj is not None:
                    current_proj.files.append(entry)
                    current_proj.total_size += size
                    current_proj.total_files += 1
                    if entry.ext:
                        current_proj.languages[entry.ext] = current_proj.languages.get(entry.ext, 0) + 1
                else:
                    result.loose_files.append(entry)
                    result.total_size += size
                    result.total_files += 1
            except Exception:
                continue

    result.projects = list(project_objs.values())
    result.total_size = sum(p.total_size for p in result.projects) + sum(f.size for f in result.loose_files)
    result.total_files = sum(p.total_files for p in result.projects) + len(result.loose_files)
    return result


def scan_to_json(root: Path, out_path: Optional[Path] = None) -> Path:
    result = scan_workspace(root)
    data = {
        "scanned_at": result.scanned_at,
        "root_path": result.root_path,
        "total_projects": len(result.projects),
        "total_files": result.total_files,
        "total_size_mb": round(result.total_size / (1024 * 1024), 2),
        "projects": [
            {
                "root": p.root,
                "name": p.name,
                "project_type": p.project_type,
                "indicators": p.indicators,
                "total_files": p.total_files,
                "total_size_mb": round(p.total_size / (1024 * 1024), 2),
                "languages": p.languages,
                "files": [asdict(f) for f in p.files[:200]],  # cap per project
            }
            for p in result.projects
        ],
        "loose_files_count": len(result.loose_files),
    }
    path = out_path or (root / "SCAN_RESULT.json")
    path.write_text(json.dumps(data, indent=2, default=str))
    return path


if __name__ == "__main__":
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/Users/alep/Downloads")
    out = scan_to_json(root)
    print(f"Scan complete: {out}")
    print(f"  Projects: {len(json.loads(out.read_text())['projects'])}")
    print(f"  Total files: {json.loads(out.read_text())['total_files']}")
