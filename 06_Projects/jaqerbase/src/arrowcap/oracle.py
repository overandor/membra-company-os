"""The oracle: subprocess-isolated execution of a buyer's hidden test suite
against a seller's revealed answer.

This is the only component allowed to look at a revealed answer and the only
component allowed to produce a pass/fail verdict. It runs pytest in a fresh
temporary directory, under a timeout, with a minimal environment -- the
revealed answer is never executed in-process and never touches the caller's
working directory.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass

_SUMMARY_RE = re.compile(r"(\d+)\s+(passed|failed|errors?|skipped)")


def _parse_summary(output: str) -> dict[str, int]:
    counts = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    for line in output.strip().splitlines()[-15:]:
        for match in _SUMMARY_RE.finditer(line):
            n, kind = int(match.group(1)), match.group(2)
            key = "errors" if kind.startswith("error") else kind
            counts[key] += n
    return counts


@dataclass
class OracleReport:
    passed: bool
    exit_code: int
    tests_passed: int
    tests_failed: int
    duration_seconds: float
    stdout_tail: str
    stderr_tail: str
    timed_out: bool

    def to_dict(self) -> dict:
        return asdict(self)


def run_hidden_tests(
    answer_content: bytes,
    hidden_test_path: str,
    *,
    answer_module_name: str = "submitted_answer",
    timeout_seconds: int = 30,
) -> OracleReport:
    """Run the hidden test suite at `hidden_test_path` (a file or directory)
    against `answer_content`, written into the sandbox as
    `<answer_module_name>.py` so the hidden tests can `import` it."""
    start = time.time()
    workdir = tempfile.mkdtemp(prefix="arrowcap_oracle_")
    timed_out = False
    stdout = ""
    stderr = ""
    exit_code = -1
    try:
        answer_file = os.path.join(workdir, f"{answer_module_name}.py")
        with open(answer_file, "wb") as fh:
            fh.write(answer_content)

        if os.path.isdir(hidden_test_path):
            dest = os.path.join(workdir, "hidden_tests")
            shutil.copytree(hidden_test_path, dest)
        else:
            dest = os.path.join(workdir, "test_hidden.py")
            shutil.copy(hidden_test_path, dest)

        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "PYTHONPATH": workdir,
            "PYTHONDONTWRITEBYTECODE": "1",
            "HOME": workdir,
        }
        cmd = [sys.executable, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider", dest]
        try:
            proc = subprocess.run(
                cmd, cwd=workdir, env=env, capture_output=True, text=True,
                timeout=timeout_seconds,
            )
            exit_code = proc.returncode
            stdout, stderr = proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            exit_code = -1
            stdout = exc.stdout or ""
            stderr = (exc.stderr or "") + "\n[oracle] hidden test run timed out"
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    counts = _parse_summary(stdout)
    passed = (not timed_out) and exit_code == 0 and counts["failed"] == 0 and counts["errors"] == 0
    return OracleReport(
        passed=passed,
        exit_code=exit_code,
        tests_passed=counts["passed"],
        tests_failed=counts["failed"] + counts["errors"],
        duration_seconds=round(time.time() - start, 4),
        stdout_tail="\n".join(stdout.strip().splitlines()[-40:]),
        stderr_tail="\n".join(stderr.strip().splitlines()[-40:]),
        timed_out=timed_out,
    )
