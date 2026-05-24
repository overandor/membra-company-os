"""Integration test for compute_mesh."""
import json
import subprocess
import sys
import time
import urllib.request

API_KEY = "test-secret"
BASE = "http://localhost:8000"

def api(method, path, data=None):
    req = urllib.request.Request(
        f"{BASE}{path}",
        method=method,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        data=json.dumps(data).encode() if data else None,
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def main():
    print("[test] starting coordinator...")
    coord = subprocess.Popen(
        [sys.executable, "coordinator.py"],
        env={**dict(subprocess.os.environ), "MESH_API_KEY": API_KEY},
    )
    time.sleep(2)

    print("[test] starting worker...")
    worker = subprocess.Popen(
        [sys.executable, "worker.py", "--url", "ws://localhost:8000", "--api-key", API_KEY, "--max-cpu", "50", "--max-ram", "512", "--max-jobs", "1"],
        env={**dict(subprocess.os.environ), "MESH_API_KEY": API_KEY},
    )
    time.sleep(3)

    try:
        print("[test] submitting job...")
        job = api("POST", "/jobs", {
            "job_type": "shell",
            "payload": "echo hello_from_mesh && sleep 1",
            "timeout_seconds": 10,
            "max_cpu_percent": 20,
            "max_ram_mb": 256,
        })
        print(f"[test] job submitted: {job['job_id']}")

        time.sleep(3)

        result = api("GET", f"/jobs/{job['job_id']}")
        print(f"[test] job status: {result['status']}")
        if result.get("result"):
            print(f"[test] stdout: {result['result']['stdout'].strip()}")

        workers = api("GET", "/workers")
        print(f"[test] workers online: {len(workers)}")

        assert result["status"] == "success", f"expected success, got {result['status']}"
        assert result["result"]["stdout"].strip() == "hello_from_mesh", "unexpected stdout"
        print("[test] ALL PASSED")
    finally:
        worker.terminate()
        coord.terminate()
        worker.wait()
        coord.wait()
        print("[test] cleaned up")


if __name__ == "__main__":
    main()
