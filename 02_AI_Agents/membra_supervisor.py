#!/usr/bin/env python3
"""
MEMBRA SUPERVISOR — 24/7 Daemon for Corpus, Agent, Dashboard

Keeps all MEMBRA components running, restarts on crash, logs with rotation.

Usage:
    python3 membra_supervisor.py start    # Start all components
    python3 membra_supervisor.py status   # Check component health
    python3 membra_supervisor.py stop     # Stop all components
    python3 membra_supervisor.py logs     # Show recent logs
"""

import os, sys, time, json, subprocess, signal, logging, threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, List
from dataclasses import dataclass, field

# ============================================================
# CONFIG
# ============================================================

BASE = Path("/Users/alep/Downloads")
LOGS = BASE / "membra_corpus" / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

COMPONENTS = {
    "dashboard": {
        "cmd": ["python3", str(BASE / "membra_dashboard.py"), "--port", "4242"],
        "port": 4242,
        "health_url": "http://localhost:4242/health",
        "restart_on_exit": True,
        "max_restarts": 10,
    },
    "agent_api": {
        "cmd": ["python3", str(BASE / "membra_agent.py"), "--mode", "daemon"],
        "port": None,
        "health_url": None,  # Agent writes heartbeat to file
        "restart_on_exit": True,
        "max_restarts": 10,
    },
    "corpus_reindex": {
        "cmd": ["python3", str(BASE / "membra_corpus_engine.py"), "pipeline", "--limit", "5000"],
        "cron": "0 */6 * * *",  # Every 6 hours
        "restart_on_exit": False,
        "max_restarts": 0,
    },
}

PID_FILE = BASE / "membra_supervisor.pid"
STATE_FILE = BASE / "membra_supervisor_state.json"

# ============================================================
# LOGGING
# ============================================================

class RotatingFileHandler(logging.Handler):
    """Simple rotating file handler."""
    def __init__(self, path: Path, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5):
        super().__init__()
        self.path = path
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self._rotate_if_needed()
    
    def _rotate_if_needed(self):
        if self.path.exists() and self.path.stat().st_size >= self.max_bytes:
            for i in range(self.backup_count - 1, 0, -1):
                src = self.path.with_suffix(f".log.{i}")
                dst = self.path.with_suffix(f".log.{i+1}")
                if src.exists():
                    src.rename(dst)
            if self.path.exists():
                self.path.rename(self.path.with_suffix(".log.1"))
    
    def emit(self, record):
        msg = self.format(record)
        with open(self.path, "a") as f:
            f.write(msg + "\n")
        if self.path.stat().st_size >= self.max_bytes:
            self._rotate_if_needed()

# Setup logging
logger = logging.getLogger("membra_supervisor")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(LOGS / "supervisor.log")
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))
logger.addHandler(handler)

console = logging.StreamHandler(sys.stdout)
console.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S"))
logger.addHandler(console)

# ============================================================
# PROCESS MANAGER
# ============================================================

@dataclass
class ComponentProcess:
    name: str
    config: Dict
    proc: Optional[subprocess.Popen] = None
    restarts: int = 0
    started_at: Optional[str] = None
    last_seen: Optional[str] = None
    pid: Optional[int] = None

class MembraSupervisor:
    """24/7 supervisor keeping all MEMBRA components alive."""
    
    def __init__(self):
        self.processes: Dict[str, ComponentProcess] = {}
        self.running = False
        self._load_state()
    
    def _load_state(self):
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                self.state = json.load(f)
        else:
            self.state = {"components": {}, "started_at": None}
    
    def _save_state(self):
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2)
    
    def _check_health(self, name: str) -> bool:
        """Check if a component is healthy."""
        comp = self.processes.get(name)
        if not comp or not comp.proc:
            return False
        
        # Check process is alive
        if comp.proc.poll() is not None:
            return False
        
        # Check HTTP health if available
        if comp.config.get("health_url"):
            try:
                import urllib.request
                with urllib.request.urlopen(comp.config["health_url"], timeout=5) as resp:
                    return resp.status == 200
            except Exception:
                return False
        
        return True
    
    def _start_component(self, name: str, config: Dict) -> Optional[subprocess.Popen]:
        """Start a component process."""
        logger.info(f"Starting {name}...")
        
        log_path = LOGS / f"{name}.log"
        env = os.environ.copy()
        env["MEMBRA_SUPERVISED"] = "1"
        
        try:
            proc = subprocess.Popen(
                config["cmd"],
                stdout=open(log_path, "a"),
                stderr=subprocess.STDOUT,
                env=env,
                preexec_fn=os.setsid if hasattr(os, "setsid") else None,
            )
            logger.info(f"  {name} started (PID {proc.pid})")
            return proc
        except Exception as e:
            logger.error(f"  Failed to start {name}: {e}")
            return None
    
    def _restart_component(self, name: str):
        """Restart a crashed component."""
        comp = self.processes[name]
        
        if comp.restarts >= comp.config.get("max_restarts", 10):
            logger.error(f"  {name}: Max restarts ({comp.restarts}) reached. Giving up.")
            return False
        
        comp.restarts += 1
        logger.warning(f"  Restarting {name} (attempt {comp.restarts})...")
        
        # Kill old process if still around
        if comp.proc and comp.proc.poll() is None:
            try:
                if hasattr(os, "killpg"):
                    os.killpg(os.getpgid(comp.proc.pid), signal.SIGTERM)
                else:
                    comp.proc.terminate()
                comp.proc.wait(timeout=5)
            except Exception:
                try:
                    comp.proc.kill()
                except Exception:
                    pass
        
        # Start fresh
        comp.proc = self._start_component(name, comp.config)
        if comp.proc:
            comp.started_at = datetime.now(timezone.utc).isoformat()
            comp.pid = comp.proc.pid
            self.state["components"][name] = {
                "pid": comp.pid,
                "started_at": comp.started_at,
                "restarts": comp.restarts,
            }
            self._save_state()
            return True
        return False
    
    def start(self):
        """Start all components."""
        if PID_FILE.exists():
            try:
                old_pid = int(PID_FILE.read_text())
                if self._is_running(old_pid):
                    logger.error("Supervisor already running (PID %s). Use 'status' or 'stop'." % old_pid)
                    return False
            except ValueError:
                pass
        
        PID_FILE.write_text(str(os.getpid()))
        self.running = True
        self.state["started_at"] = datetime.now(timezone.utc).isoformat()
        self._save_state()
        
        logger.info("=" * 60)
        logger.info("MEMBRA SUPERVISOR STARTING — 24/7 DAEMON")
        logger.info("=" * 60)
        
        # Start all components
        for name, config in COMPONENTS.items():
            if name == "corpus_reindex":
                # Schedule cron-like reindex
                continue
            
            comp = ComponentProcess(name=name, config=config)
            comp.proc = self._start_component(name, config)
            if comp.proc:
                comp.started_at = datetime.now(timezone.utc).isoformat()
                comp.pid = comp.proc.pid
            self.processes[name] = comp
            self.state["components"][name] = {
                "pid": comp.pid,
                "started_at": comp.started_at,
                "restarts": 0,
            }
        
        self._save_state()
        self._run_loop()
        return True
    
    def _is_running(self, pid: int) -> bool:
        """Check if a PID is alive."""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    
    def _run_loop(self):
        """Main supervision loop."""
        health_check_interval = 30  # seconds
        last_health_check = 0
        
        while self.running:
            now = time.time()
            
            # Periodic health checks
            if now - last_health_check >= health_check_interval:
                last_health_check = now
                self._do_health_check()
            
            # Check for process exits
            for name, comp in list(self.processes.items()):
                if comp.proc and comp.proc.poll() is not None:
                    exit_code = comp.proc.poll()
                    logger.warning(f"{name} exited (code {exit_code})")
                    
                    if comp.config.get("restart_on_exit", False):
                        self._restart_component(name)
                    else:
                        logger.info(f"  {name} will not be restarted (config)")
            
            # Run cron jobs
            self._run_cron_jobs()
            
            time.sleep(1)
    
    def _do_health_check(self):
        """Run health checks on all components."""
        healthy = 0
        for name, comp in self.processes.items():
            is_healthy = self._check_health(name)
            status = "✅ healthy" if is_healthy else "❌ dead"
            if is_healthy:
                healthy += 1
            else:
                logger.warning(f"Health check: {name} {status}")
                if comp.config.get("restart_on_exit"):
                    self._restart_component(name)
        
        self.state["last_health_check"] = datetime.now(timezone.utc).isoformat()
        self.state["healthy_count"] = healthy
        self.state["total_count"] = len(self.processes)
        self._save_state()
    
    def _run_cron_jobs(self):
        """Run scheduled background jobs."""
        # Every 6 hours: reindex corpus
        last_reindex = self.state.get("last_corpus_reindex", "")
        if last_reindex:
            last = datetime.fromisoformat(last_reindex)
            hours_since = (datetime.now(timezone.utc) - last).total_seconds() / 3600
        else:
            hours_since = 999
        
        if hours_since >= 6:
            logger.info("Running scheduled corpus reindex...")
            self._run_background("corpus_reindex", COMPONENTS["corpus_reindex"]["cmd"])
            self.state["last_corpus_reindex"] = datetime.now(timezone.utc).isoformat()
            self._save_state()
    
    def _run_background(self, name: str, cmd: List[str]):
        """Run a one-off background command."""
        log_path = LOGS / f"{name}.log"
        try:
            subprocess.Popen(
                cmd,
                stdout=open(log_path, "a"),
                stderr=subprocess.STDOUT,
                env={**os.environ, "MEMBRA_SUPERVISED": "1"},
            )
            logger.info(f"  Background job '{name}' started")
        except Exception as e:
            logger.error(f"  Failed to start background job '{name}': {e}")
    
    def stop(self):
        """Stop all components and supervisor."""
        self.running = False
        logger.info("Shutting down MEMBRA components...")
        
        for name, comp in self.processes.items():
            if comp.proc and comp.proc.poll() is None:
                logger.info(f"  Stopping {name} (PID {comp.proc.pid})...")
                try:
                    if hasattr(os, "killpg"):
                        os.killpg(os.getpgid(comp.proc.pid), signal.SIGTERM)
                    else:
                        comp.proc.terminate()
                    comp.proc.wait(timeout=5)
                except Exception:
                    try:
                        comp.proc.kill()
                    except Exception:
                        pass
        
        PID_FILE.unlink(missing_ok=True)
        logger.info("Supervisor stopped.")
    
    def status(self) -> str:
        """Get current status of all components."""
        lines = ["MEMBRA SUPERVISOR STATUS", "=" * 50]
        
        for name, comp in self.processes.items():
            healthy = self._check_health(name)
            status_icon = "🟢" if healthy else "🔴"
            pid = comp.pid if comp.pid else "N/A"
            restarts = comp.restarts
            started = comp.started_at.split("T")[0] if comp.started_at else "N/A"
            lines.append(f"{status_icon} {name:15} PID:{pid:<8} restarts:{restarts} started:{started}")
        
        lines.append("")
        lines.append(f"Logs: {LOGS}")
        lines.append(f"State: {STATE_FILE}")
        return "\n".join(lines)

# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Membra 24/7 Supervisor")
    parser.add_argument("action", choices=["start", "stop", "status", "logs", "restart"])
    args = parser.parse_args()
    
    supervisor = MembraSupervisor()
    
    if args.action == "start":
        # Daemonize: fork to background
        try:
            pid = os.fork()
            if pid > 0:
                print(f"Supervisor started (PID {pid}). Logs: {LOGS}")
                sys.exit(0)
        except OSError:
            pass  # Can't fork, run in foreground
        
        supervisor.start()
    
    elif args.action == "stop":
        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text())
                os.kill(pid, signal.SIGTERM)
                print(f"Sent stop signal to supervisor (PID {pid})")
            except (ValueError, OSError) as e:
                print(f"Error stopping: {e}")
        else:
            print("Supervisor not running.")
    
    elif args.action == "status":
        print(supervisor.status())
    
    elif args.action == "logs":
        log_file = LOGS / "supervisor.log"
        if log_file.exists():
            lines = log_file.read_text().splitlines()[-50:]
            print("\n".join(lines))
        else:
            print("No logs yet.")
    
    elif args.action == "restart":
        supervisor.stop()
        time.sleep(2)
        supervisor.start()

if __name__ == "__main__":
    main()
