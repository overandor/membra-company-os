#!/usr/bin/env python3
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

def hash_file(path: str) -> dict:
    p = Path(path)
    data = p.read_bytes()
    return {
        "path": str(p),
        "length": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(json.dumps(hash_file(arg), indent=2))
