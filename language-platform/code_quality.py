"""
CollateralOps — Code quality scanner (T11).
Cyclomatic complexity estimation, test coverage heuristics, documentation ratio.
"""
import ast
import os
import re
from pathlib import Path
from typing import Dict, List


def _count_functions(source: str) -> int:
    """Count function definitions in Python source."""
    try:
        tree = ast.parse(source)
        return sum(1 for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
    except SyntaxError:
        return 0


def _count_classes(source: str) -> int:
    try:
        tree = ast.parse(source)
        return sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
    except SyntaxError:
        return 0


def _estimate_complexity(source: str) -> int:
    """Rough cyclomatic complexity: count branches."""
    branches = len(re.findall(r"\b(if|elif|while|for|except|with|assert|and|or)\b", source))
    functions = max(1, _count_functions(source))
    return max(1, branches // functions)


def scan_repo_quality(repo_path: str) -> Dict:
    """Scan a local repo for code quality metrics."""
    repo = Path(repo_path)
    if not repo.exists():
        return {"error": "Repo path does not exist"}

    total_files = 0
    total_lines = 0
    code_lines = 0
    comment_lines = 0
    test_files = 0
    test_lines = 0
    doc_files = 0
    complexity_sum = 0
    complexity_count = 0
    languages = {}

    for file_path in repo.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.stat().st_size > 2 * 1024 * 1024:
            continue
        rel = str(file_path.relative_to(repo))
        if ".git" in rel or "node_modules" in rel or "__pycache__" in rel or ".venv" in rel:
            continue

        ext = file_path.suffix.lower()
        if ext in (".py", ".js", ".ts", ".go", ".rs", ".java", ".cpp", ".c", ".h", ".cs", ".rb", ".php"):
            total_files += 1
            languages[ext] = languages.get(ext, 0) + 1
            try:
                text = file_path.read_text(errors="ignore")
                lines = text.splitlines()
                total_lines += len(lines)
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("/*"):
                        comment_lines += 1
                    elif stripped:
                        code_lines += 1
                if ext == ".py":
                    complexity_sum += _estimate_complexity(text)
                    complexity_count += max(1, _count_functions(text))
            except Exception:
                pass
        if "test" in rel.lower() or "spec" in rel.lower():
            test_files += 1
            try:
                test_lines += len(file_path.read_text(errors="ignore").splitlines())
            except Exception:
                pass
        if rel.lower().endswith((".md", ".rst", ".txt")) and not rel.lower().startswith(("changelog", "license", "copying")):
            doc_files += 1

    avg_complexity = round(complexity_sum / max(1, complexity_count), 1)
    coverage_estimate = min(100, round((test_lines / max(1, code_lines)) * 100, 1))
    doc_ratio = round((doc_files / max(1, total_files)) * 100, 1)

    return {
        "total_files": total_files,
        "total_lines": total_lines,
        "code_lines": code_lines,
        "comment_lines": comment_lines,
        "test_files": test_files,
        "test_lines": test_lines,
        "doc_files": doc_files,
        "avg_complexity": avg_complexity,
        "coverage_estimate": coverage_estimate,
        "doc_ratio": doc_ratio,
        "languages": languages,
        "grade": "A" if avg_complexity < 8 and coverage_estimate > 60 else "B" if avg_complexity < 15 and coverage_estimate > 30 else "C" if avg_complexity < 25 else "D",
    }
