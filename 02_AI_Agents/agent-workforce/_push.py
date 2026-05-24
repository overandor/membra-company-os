#!/usr/bin/env python3
"""Push all files to GitHub via Contents API."""
import os, base64, json, time
from pathlib import Path

TOKEN = "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"
OWNER = "overandor"
REPO = "agent-workforce"
BRANCH = "main"
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

import urllib.request

def api(method, path, data=None):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"
    req = urllib.request.Request(url, method=method, headers=HEADERS)
    if data:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode()
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"status": e.code, "body": e.read().decode()[:500]}

base = Path("/Users/alep/Downloads/agent-workforce")
ignore = {".git", "_push.py", "__pycache__", ".DS_Store"}
files = sorted(p for p in base.rglob("*") if p.is_file() and not any(part in ignore for part in p.parts))

for p in files:
    rel = str(p.relative_to(base))
    content = base64.b64encode(p.read_bytes()).decode()
    # Check if file exists to get sha
    existing = api("GET", rel)
    sha = existing.get("sha")
    payload = {
        "message": f"Add {rel}",
        "content": content,
        "branch": BRANCH,
    }
    if sha:
        payload["sha"] = sha
    result = api("PUT", rel, payload)
    print(f"{'UPDATED' if sha else 'CREATED'} {rel} -> {result.get('status', 'OK')}")
    time.sleep(0.5)

print("Done!")
