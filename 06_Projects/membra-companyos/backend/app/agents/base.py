"""MEMBRA Agent Network Protocol OS — Base Agent Class.
Every employee is an autonomous agent with:
  - Ollama LLM integration (local & remote)
  - Network protocol communication (gossip, RPC, broadcast)
  - Job description & responsibilities
  - State machine (idle, busy, error, offline)
  - Contribution tracking
"""
import asyncio
import hashlib
import json
import os
import socket
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

import httpx

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MEMBRA_NETWORK_PORT = int(os.getenv("MEMBRA_NETWORK_PORT", "0"))  # 0 = auto


@dataclass
class AgentMessage:
    """Inter-agent message envelope."""
    msg_id: str
    src: str  # sender agent_id
    dst: str  # recipient agent_id or "*" for broadcast
    msg_type: str  # "rpc", "gossip", "task", "heartbeat", "result"
    payload: Dict[str, Any]
    ts: float = field(default_factory=time.time)
    ttl: int = 5  # hops before drop

    def to_bytes(self) -> bytes:
        return json.dumps({
            "msg_id": self.msg_id,
            "src": self.src,
            "dst": self.dst,
            "msg_type": self.msg_type,
            "payload": self.payload,
            "ts": self.ts,
            "ttl": self.ttl,
        }).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> "AgentMessage":
        d = json.loads(data.decode("utf-8"))
        return cls(**d)

    def hash(self) -> str:
        return hashlib.sha256(self.to_bytes()).hexdigest()[:16]


class BaseAgent(ABC):
    """Base class for every MEMBRA employee.

    Naming convention: {name}.{department}.membra
    Example: linda.marketing.membra
    """

    # Override in subclass
    AGENT_ID: str = ""
    NAME: str = ""
    DEPARTMENT: str = ""
    TITLE: str = ""
    MODEL: str = "llama3.2"
    SYSTEM_PROMPT: str = "You are a MEMBRA agent."
    RESPONSIBILITIES: List[str] = []
    CAPABILITIES: List[str] = []

    def __init__(
        self,
        ollama_host: Optional[str] = None,
        mode: str = "local",  # "local" | "remote" | "hybrid"
        network_port: Optional[int] = None,
        registry_url: Optional[str] = None,
    ):
        self.agent_id = self.AGENT_ID
        self.name = self.NAME
        self.department = self.DEPARTMENT
        self.title = self.TITLE
        self.model = self.MODEL
        self.mode = mode
        self.ollama_host = ollama_host or OLLAMA_HOST
        self.registry_url = registry_url
        self.network_port = network_port or 0

        self.status = "idle"  # idle | busy | error | offline
        self.total_runs = 0
        self.total_contributions = 0
        self.last_output = ""
        self.last_error = ""
        self.peers: Dict[str, Dict[str, Any]] = {}  # known agents on the network
        self.message_log: List[AgentMessage] = []
        self.handlers: Dict[str, Callable] = {}
        self._server: Optional[asyncio.Server] = None
        self._client = httpx.AsyncClient(timeout=60.0)
        self._running = False

        self._register_handlers()

    # ─── Identity ───
    @property
    def full_name(self) -> str:
        return f"{self.name}.{self.department}.membra"

    @property
    def job_description(self) -> str:
        resp = "\n  - ".join([""] + self.RESPONSIBILITIES)
        caps = "\n  - ".join([""] + self.CAPABILITIES)
        return (
            f"【{self.agent_id}】{self.full_name}\n"
            f"Department: {self.DEPARTMENT.upper()}\n"
            f"Title: {self.TITLE}\n"
            f"Model: {self.MODEL}\n"
            f"Mode: {self.mode}\n"
            f"Status: {self.status}\n\n"
            f"Responsibilities:{resp}\n\n"
            f"Capabilities:{caps}\n\n"
            f"System Prompt:\n{self.SYSTEM_PROMPT}"
        )

    # ─── LLM / Ollama ───
    async def think(self, prompt: str, context: Optional[str] = None) -> str:
        """Run a thought through Ollama."""
        self.status = "busy"
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "user", "content": f"Context: {context}"})
        messages.append({"role": "user", "content": prompt})

        try:
            resp = await self._client.post(
                f"{self.ollama_host}/api/chat",
                json={"model": self.model, "messages": messages, "stream": False},
            )
            resp.raise_for_status()
            data = resp.json()
            output = data.get("message", {}).get("content", "")
            self.last_output = output
            self.total_runs += 1
            self.total_contributions += 1
            self.status = "idle"
            return output
        except Exception as e:
            self.status = "error"
            self.last_error = str(e)
            return f"[ERROR] {self.agent_id}: {e}"

    async def generate(self, prompt: str) -> str:
        """Raw generation via Ollama generate endpoint."""
        self.status = "busy"
        try:
            resp = await self._client.post(
                f"{self.ollama_host}/api/generate",
                json={"model": self.model, "prompt": prompt, "system": self.SYSTEM_PROMPT, "stream": False},
            )
            resp.raise_for_status()
            data = resp.json()
            output = data.get("response", "")
            self.last_output = output
            self.total_runs += 1
            self.status = "idle"
            return output
        except Exception as e:
            self.status = "error"
            self.last_error = str(e)
            return f"[ERROR] {self.agent_id}: {e}"

    # ─── Network Protocol OS ───
    def _register_handlers(self):
        """Register default message handlers."""
        self.handlers["heartbeat"] = self._on_heartbeat
        self.handlers["rpc"] = self._on_rpc
        self.handlers["task"] = self._on_task
        self.handlers["gossip"] = self._on_gossip

    def _on_heartbeat(self, msg: AgentMessage) -> Optional[AgentMessage]:
        """Respond to heartbeat with peer info."""
        self.peers[msg.src] = {
            "last_seen": time.time(),
            "department": msg.payload.get("department"),
            "status": msg.payload.get("status"),
            "port": msg.payload.get("port"),
        }
        return None

    def _on_rpc(self, msg: AgentMessage) -> Optional[AgentMessage]:
        """Handle RPC calls. Subclasses override for custom RPCs."""
        method = msg.payload.get("method")
        params = msg.payload.get("params", {})
        if method == "status":
            return self._reply(msg, {"status": self.status, "runs": self.total_runs})
        elif method == "describe":
            return self._reply(msg, {"job": self.job_description})
        elif method == "think":
            # Async think is handled separately via task
            return self._reply(msg, {"ack": True, "note": "Use 'task' for LLM work"})
        return self._reply(msg, {"error": f"Unknown method: {method}"})

    async def _on_task(self, msg: AgentMessage) -> Optional[AgentMessage]:
        """Execute an LLM task sent by another agent."""
        prompt = msg.payload.get("prompt", "")
        result = await self.think(prompt)
        return self._reply(msg, {"result": result, "agent": self.agent_id})

    def _on_gossip(self, msg: AgentMessage) -> Optional[AgentMessage]:
        """Accept gossip (peer discovery) messages."""
        for peer_id, peer_info in msg.payload.get("peers", {}).items():
            if peer_id != self.agent_id:
                self.peers.setdefault(peer_id, {}).update(peer_info)
        return None

    def _reply(self, incoming: AgentMessage, payload: Dict[str, Any]) -> AgentMessage:
        return AgentMessage(
            msg_id=str(uuid.uuid4())[:8],
            src=self.agent_id,
            dst=incoming.src,
            msg_type="result",
            payload=payload,
        )

    # ─── Server (listen for incoming messages) ───
    async def start_server(self, host: str = "0.0.0.0", port: int = 0) -> int:
        """Start TCP server to accept inter-agent messages."""
        self._server = await asyncio.start_server(
            self._handle_connection, host, port
        )
        addr = self._server.sockets[0].getsockname()
        self.network_port = addr[1]
        self._running = True
        # Announce to registry if configured
        if self.registry_url:
            await self._register_with_registry()
        # Start heartbeat loop
        asyncio.create_task(self._heartbeat_loop())
        return self.network_port

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming TCP connections."""
        try:
            raw_len = await reader.read(4)
            if not raw_len:
                return
            msg_len = int.from_bytes(raw_len, "big")
            raw_msg = await reader.read(msg_len)
            msg = AgentMessage.from_bytes(raw_msg)
            self.message_log.append(msg)

            # Process
            if msg.dst != self.agent_id and msg.dst != "*":
                # Not for us; route if we know the peer
                await self._route_message(msg)
                return

            handler = self.handlers.get(msg.msg_type)
            if handler:
                if asyncio.iscoroutinefunction(handler):
                    reply = await handler(msg)
                else:
                    reply = handler(msg)
                if reply:
                    await self._send_raw(reply, writer)
        except Exception as e:
            self.last_error = str(e)
        finally:
            writer.close()

    async def _send_raw(self, msg: AgentMessage, writer: asyncio.StreamWriter):
        data = msg.to_bytes()
        writer.write(len(data).to_bytes(4, "big"))
        writer.write(data)
        await writer.drain()

    async def _route_message(self, msg: AgentMessage):
        """Route a message to its destination if known."""
        msg.ttl -= 1
        if msg.ttl <= 0:
            return
        peer = self.peers.get(msg.dst)
        if peer and peer.get("port"):
            await self._send_tcp(msg, "localhost", peer["port"])

    async def _send_tcp(self, msg: AgentMessage, host: str, port: int):
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=3.0
            )
            await self._send_raw(msg, writer)
            writer.close()
        except Exception:
            pass

    # ─── Client (send messages to peers) ───
    async def send(self, dst: str, msg_type: str, payload: Dict[str, Any]) -> Optional[AgentMessage]:
        """Send a message to another agent by ID."""
        msg = AgentMessage(
            msg_id=str(uuid.uuid4())[:8],
            src=self.agent_id,
            dst=dst,
            msg_type=msg_type,
            payload=payload,
        )
        peer = self.peers.get(dst)
        if peer and peer.get("port"):
            await self._send_tcp(msg, "localhost", peer["port"])
        elif self.registry_url:
            # Ask registry to forward
            await self._client.post(
                f"{self.registry_url}/relay",
                json={"msg": msg.to_bytes().decode("utf-8")},
            )
        return msg

    async def broadcast(self, msg_type: str, payload: Dict[str, Any]):
        """Broadcast to all known peers."""
        msg = AgentMessage(
            msg_id=str(uuid.uuid4())[:8],
            src=self.agent_id,
            dst="*",
            msg_type=msg_type,
            payload=payload,
        )
        for peer_id, peer in self.peers.items():
            if peer.get("port"):
                await self._send_tcp(msg, "localhost", peer["port"])

    async def rpc(self, dst: str, method: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Call a remote procedure on another agent."""
        reply = await self.send(dst, "rpc", {"method": method, "params": params or {}})
        # In a real system we'd await the reply; simplified here
        return {"sent": True, "msg_id": reply.msg_id if reply else None}

    # ─── Heartbeat & Discovery ───
    async def _heartbeat_loop(self):
        while self._running:
            await self.broadcast("heartbeat", {
                "department": self.department,
                "status": self.status,
                "port": self.network_port,
                "agent_id": self.agent_id,
            })
            # Gossip peer table
            await self.broadcast("gossip", {"peers": {
                pid: {"dept": p.get("department"), "status": p.get("status"), "port": p.get("port")}
                for pid, p in self.peers.items()
            }})
            await asyncio.sleep(10)

    async def _register_with_registry(self):
        try:
            await self._client.post(
                f"{self.registry_url}/register",
                json={
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "department": self.department,
                    "title": self.title,
                    "port": self.network_port,
                    "host": "localhost",
                    "status": self.status,
                },
            )
        except Exception:
            pass

    # ─── Lifecycle ───
    async def stop(self):
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        await self._client.aclose()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "full_name": self.full_name,
            "name": self.name,
            "department": self.department,
            "title": self.title,
            "model": self.model,
            "status": self.status,
            "mode": self.mode,
            "total_runs": self.total_runs,
            "total_contributions": self.total_contributions,
            "network_port": self.network_port,
            "responsibilities": self.RESPONSIBILITIES,
            "capabilities": self.CAPABILITIES,
            "peers_known": len(self.peers),
            "last_error": self.last_error,
        }
