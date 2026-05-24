"""VM LLM OS Online — FastAPI server with WebSocket terminal.

Provides a web-based VM interface to the LLM OS kernel.
"""

import asyncio
import json
import os
import sys
import threading
import time
from io import StringIO
from typing import Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from llm_os.governance import ActionClass, Policy
from llm_os.kernel import Kernel

app = FastAPI(title="VM LLM OS", version="0.2.0")

# Serve static files if the directory exists
_static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_path):
    app.mount("/static", StaticFiles(directory=_static_path), name="static")


class _CaptureBuffer:
    """Thread-local stdout capture for kernel instances."""

    def __init__(self):
        self.buffer = StringIO()
        self.lock = threading.Lock()
        self._callbacks = []

    def write(self, text: str):
        with self.lock:
            self.buffer.write(text)
        for cb in self._callbacks:
            try:
                cb(text)
            except Exception:
                pass

    def flush(self):
        pass

    def getvalue(self) -> str:
        with self.lock:
            return self.buffer.getvalue()

    def on_write(self, callback):
        self._callbacks.append(callback)

    def clear(self):
        with self.lock:
            self.buffer = StringIO()


class VMInstance:
    """A per-connection VM instance wrapping the LLM OS kernel."""

    def __init__(self):
        policy = Policy(
            name="vm_online_default",
            action_classes={ActionClass.SAFE, ActionClass.STANDARD, ActionClass.RISKY},
            daily_cost_limit_usd=50.0,
            single_action_cost_limit_usd=25.0,
            simulation_mode=True,
            allow_model_training=True,
            allow_real_payments=False,
            allow_production_deploy=False,
        )
        self.kernel = Kernel(policy=policy)
        self.capture = _CaptureBuffer()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._loop_task: Optional[asyncio.Task] = None
        self._websocket: Optional[WebSocket] = None
        self._lock = threading.Lock()

    def set_websocket(self, ws: WebSocket):
        self._websocket = ws

    def _send(self, text: str):
        if self._websocket is not None:
            try:
                # Use asyncio.run_coroutine_threadsafe because we may be called from a background thread
                asyncio.run_coroutine_threadsafe(
                    self._websocket.send_json({"type": "output", "text": text}),
                    asyncio.get_event_loop(),
                )
            except Exception:
                pass

    async def send_status(self):
        if self._websocket is not None:
            try:
                await self._websocket.send_json({
                    "type": "status",
                    "data": self.kernel.get_status(),
                })
            except Exception:
                pass

    def _run_loop(self):
        """Run the kernel loop in a background thread with captured stdout."""
        old_stdout = sys.stdout
        sys.stdout = self.capture
        self.capture.on_write(self._send)
        try:
            self.kernel.start(autonomous=True)
        except Exception as e:
            self.capture.write(f"\n[VM ERROR] {e}\n")
        finally:
            sys.stdout = old_stdout

    def boot(self):
        """Boot the VM (start kernel loop)."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return {"status": "already_running"}
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            return {"status": "booted"}

    def shutdown(self):
        """Shutdown the VM."""
        self.kernel.stop()
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
        return {"status": "shutdown"}

    def run_once(self):
        """Run a single autonomous cycle synchronously."""
        old_stdout = sys.stdout
        sys.stdout = self.capture
        self.capture.on_write(self._send)
        try:
            self.kernel.start(autonomous=False)
        finally:
            sys.stdout = old_stdout
        return {"status": "cycle_complete"}

    def handle_command(self, command: str, args: list) -> dict:
        """Handle CLI-like commands from the web terminal."""
        old_stdout = sys.stdout
        sys.stdout = self.capture
        self.capture.on_write(self._send)
        try:
            if command == "status":
                return {"type": "status", "data": self.kernel.get_status()}
            elif command == "scan":
                opps = self.kernel.economic_engine.scan_opportunities()
                return {"type": "scan", "count": len(opps), "opportunities": [
                    {"id": o.opportunity_id, "desc": o.description, "profit": o.expected_profit}
                    for o in opps
                ]}
            elif command == "treasury":
                return {"type": "treasury", "data": self.kernel.treasury.get_status()}
            elif command == "halt":
                reason = " ".join(args) if args else "Web halt"
                self.kernel.emergency_halt(reason)
                return {"type": "halt", "reason": reason}
            elif command == "resume":
                self.kernel.emergency_resume()
                return {"type": "resume"}
            elif command == "build":
                build_type = args[0] if args else "generic"
                plan = self.kernel.system_builder.analyze_requirements({
                    "type": build_type,
                    "description": f"VM-requested {build_type}",
                    "requirements": ["functional", "tested"],
                })
                result = self.kernel.system_builder.generate_code(plan)
                if result.get("success"):
                    self.kernel.system_builder.run_tests(plan.plan_id)
                    self.kernel.system_builder.finalize_build(plan.plan_id)
                return {"type": "build", "result": result}
            elif command == "train":
                name = args[0] if args else "vm_model"
                spec = self.kernel.llm_factory.create_model_spec(name, "VM trained model")
                result = self.kernel.llm_factory.train_model(spec.model_id)
                return {"type": "train", "result": result}
            elif command == "zkpopc":
                subcmd = args[0] if args else "status"
                if subcmd == "status":
                    return {"type": "zkpopc_status", "data": self.kernel.zk_popc.get_stats()}
                elif subcmd == "mint":
                    results = self.kernel.zk_popc.batch_mint_verified_proofs()
                    return {"type": "zkpopc_mint", "minted": results}
                elif subcmd == "proofs":
                    proof_id = args[1] if len(args) > 1 else None
                    if proof_id:
                        return {"type": "zkpopc_proof", "data": self.kernel.zk_popc.get_proof_status(proof_id)}
                    return {"type": "zkpopc_proofs", "data": list(self.kernel.zk_popc.proofs.keys())}
                else:
                    return {"type": "error", "text": f"Unknown zkpopc subcommand: {subcmd}"}
            elif command == "help":
                return {"type": "help", "text": (
                    "commands: status, scan, treasury, build <type>, train <name>, "
                    "zkpopc <status|mint|proofs [id]>, "
                    "halt [reason], resume, once, boot, shutdown, help, clear"
                )}
            else:
                return {"type": "error", "text": f"Unknown command: {command}"}
        finally:
            sys.stdout = old_stdout


# In-memory store of active VM sessions
_sessions: Dict[str, VMInstance] = {}


@app.get("/")
async def index():
    index_path = os.path.join(_static_path, "index.html")
    if os.path.isfile(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>VM LLM OS Online</h1><p>Static files missing. Place static/index.html</p>")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    session_id = f"vm_{id(ws)}_{int(time.time())}"
    vm = VMInstance()
    vm.set_websocket(ws)
    _sessions[session_id] = vm

    # Send boot banner
    await ws.send_json({
        "type": "output",
        "text": (
            "\n[VM LLM OS v0.2.0 Online]\n"
            f"Session: {session_id}\n"
            "Mode: SIMULATION (no real money)\n"
            "ZK-PoPC: Proof-backed monetary issuance enabled\n"
            "Type 'help' for commands.\n\n"
        ),
    })

    try:
        while True:
            msg = await ws.receive_text()
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                data = {"cmd": msg.strip()}

            action = data.get("action", "")
            cmd = data.get("cmd", "").strip()

            if action == "boot":
                result = vm.boot()
                await ws.send_json({"type": "boot", "data": result})
            elif action == "shutdown":
                result = vm.shutdown()
                await ws.send_json({"type": "shutdown", "data": result})
            elif action == "once":
                # Run one cycle in background thread so it doesn't block the websocket
                def run_once_bg():
                    vm.run_once()
                t = threading.Thread(target=run_once_bg, daemon=True)
                t.start()
                await ws.send_json({"type": "once", "status": "started"})
            elif action == "status":
                await vm.send_status()
            elif cmd:
                parts = cmd.split()
                command = parts[0]
                args = parts[1:]
                result = vm.handle_command(command, args)
                await ws.send_json(result)
            else:
                await ws.send_json({"type": "error", "text": "Unknown action or empty cmd"})

    except WebSocketDisconnect:
        pass
    finally:
        vm.shutdown()
        _sessions.pop(session_id, None)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
