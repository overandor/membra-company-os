#!/usr/bin/env python3
"""
AGENT P2P NETWORK — Peer-to-Peer Communication for M5 Pro Mac Clusters

Each M5 Pro Mac runs an autonomous agent node. Nodes discover each other
via mDNS/Bonjour on the local network or a bootstrap relay. They gossip:
- Consensus votes (inference hashes)
- Resource availability (CPU/RAM/GPU)
- Token balances and trade offers
- Task assignments and completions

Protocol:
- UDP multicast for discovery (port 42424)
- WebSocket for reliable message passing
- Gossip every 2 seconds, anti-entropy every 30 seconds
"""
import asyncio
import hashlib
import json
import os
import socket
import struct
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Set

import aiohttp
from aiohttp import web, WSMsgType


MCAST_GROUP = "224.1.1.1"
MCAST_PORT = 42424
WS_PORT = 42425


@dataclass
class AgentNode:
    agent_id: str
    hostname: str
    ip: str
    resources: Dict
    timestamp: float
    token_balance: float = 0.0
    tasks_completed: int = 0
    reputation: float = 5.0


@dataclass
class GossipMessage:
    msg_type: str  # "vote", "resource", "trade", "task", "heartbeat"
    sender_id: str
    payload: Dict
    timestamp: float


class AgentP2PNetwork:
    """P2P gossip network for inter-agent communication."""

    def __init__(self, agent_id: str, port: int = WS_PORT):
        self.agent_id = agent_id
        self.hostname = socket.gethostname()
        self.ip = self._get_local_ip()
        self.port = port
        self.peers: Dict[str, AgentNode] = {}
        self.ws_peers: Dict[str, web.WebSocketResponse] = {}
        self.messages_received = 0
        self.messages_sent = 0
        self.trade_offers: List[Dict] = []
        self.pending_votes: List[Dict] = []
        self.running = False
        self._app: Optional[web.Application] = None

    def _get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    # ────────────────────────────────────────────
    # DISCOVERY
    # ────────────────────────────────────────────

    async def _discovery_listener(self):
        """Listen for multicast discovery beacons."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', MCAST_PORT))

        mreq = struct.pack("4sl", socket.inet_aton(MCAST_GROUP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.setblocking(False)

        loop = asyncio.get_event_loop()
        while self.running:
            try:
                data = await loop.sock_recv(sock, 1024)
                msg = json.loads(data.decode())
                if msg.get("agent_id") != self.agent_id:
                    self._handle_discovery(msg)
            except Exception:
                await asyncio.sleep(0.1)

    async def _discovery_beacon(self, interval: float = 3.0):
        """Broadcast multicast discovery beacons."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        while self.running:
            msg = json.dumps({
                "type": "discover",
                "agent_id": self.agent_id,
                "hostname": self.hostname,
                "ip": self.ip,
                "ws_port": self.port,
                "timestamp": time.time(),
            })
            try:
                sock.sendto(msg.encode(), (MCAST_GROUP, MCAST_PORT))
                self.messages_sent += 1
            except Exception:
                pass
            await asyncio.sleep(interval)

    def _handle_discovery(self, msg: Dict):
        peer_id = msg.get("agent_id")
        if peer_id and peer_id not in self.peers:
            self.peers[peer_id] = AgentNode(
                agent_id=peer_id,
                hostname=msg.get("hostname", "unknown"),
                ip=msg.get("ip", "unknown"),
                resources={},
                timestamp=msg.get("timestamp", time.time()),
            )
            # Connect via WebSocket
            asyncio.create_task(self._connect_peer(msg.get("ip"), msg.get("ws_port", WS_PORT)))

    # ────────────────────────────────────────────
    # WEBSOCKET SERVER + CLIENT
    # ────────────────────────────────────────────

    async def _ws_handler(self, request):
        """Handle incoming WebSocket connections."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        peer_id = None

        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)
                peer_id = data.get("sender_id")
                if peer_id:
                    self.ws_peers[peer_id] = ws
                self._handle_message(data)
                self.messages_received += 1
            elif msg.type == WSMsgType.ERROR:
                break

        if peer_id and peer_id in self.ws_peers:
            del self.ws_peers[peer_id]
        return ws

    async def _connect_peer(self, ip: str, port: int):
        """Connect to a peer via WebSocket."""
        try:
            session = aiohttp.ClientSession()
            async with session.ws_connect(f"ws://{ip}:{port}/p2p") as ws:
                self.ws_peers[f"{ip}:{port}"] = ws
                # Send our hello
                await ws.send_json({
                    "type": "hello",
                    "sender_id": self.agent_id,
                    "hostname": self.hostname,
                    "timestamp": time.time(),
                })
                async for msg in ws:
                    if msg.type == WSMsgType.TEXT:
                        self._handle_message(json.loads(msg.data))
                        self.messages_received += 1
                    elif msg.type == WSMsgType.CLOSED:
                        break
        except Exception:
            pass

    # ────────────────────────────────────────────
    # GOSSIP
    # ────────────────────────────────────────────

    async def _gossip_loop(self, interval: float = 2.0):
        """Periodically gossip state to all connected peers."""
        while self.running:
            gossip = self._build_gossip()
            for peer_id, ws in list(self.ws_peers.items()):
                try:
                    await ws.send_json(gossip)
                    self.messages_sent += 1
                except Exception:
                    # Peer disconnected
                    if peer_id in self.ws_peers:
                        del self.ws_peers[peer_id]
            await asyncio.sleep(interval)

    def _build_gossip(self) -> Dict:
        """Build current gossip message."""
        return {
            "type": "gossip",
            "sender_id": self.agent_id,
            "timestamp": time.time(),
            "payload": {
                "resources": {
                    "cpu_percent": 0,  # Filled by caller
                    "memory_percent": 0,
                    "gpu_available": False,
                },
                "token_balance": 0.0,
                "tasks_completed": 0,
                "pending_votes": self.pending_votes,
                "trade_offers": self.trade_offers,
            },
        }

    def _handle_message(self, msg: Dict):
        """Process incoming P2P message."""
        msg_type = msg.get("type")
        sender = msg.get("sender_id")

        if msg_type == "hello":
            self.peers[sender] = AgentNode(
                agent_id=sender,
                hostname=msg.get("hostname", ""),
                ip="unknown",
                resources={},
                timestamp=msg.get("timestamp", time.time()),
            )

        elif msg_type == "gossip":
            payload = msg.get("payload", {})
            if sender in self.peers:
                self.peers[sender].resources = payload.get("resources", {})
                self.peers[sender].token_balance = payload.get("token_balance", 0.0)
                self.peers[sender].tasks_completed = payload.get("tasks_completed", 0)
                self.peers[sender].timestamp = time.time()

        elif msg_type == "vote":
            # Consensus vote from peer
            self.pending_votes.append({
                "sender": sender,
                "vote": msg.get("payload", {}),
                "timestamp": time.time(),
            })

        elif msg_type == "trade":
            self.trade_offers.append({
                "from": sender,
                "offer": msg.get("payload", {}),
                "timestamp": time.time(),
            })

    # ────────────────────────────────────────────
    # PUBLIC API
    # ────────────────────────────────────────────

    def broadcast_vote(self, vote: Dict):
        """Broadcast a consensus vote to all peers."""
        self.pending_votes.append({"sender": self.agent_id, "vote": vote})
        msg = {
            "type": "vote",
            "sender_id": self.agent_id,
            "timestamp": time.time(),
            "payload": vote,
        }
        for ws in self.ws_peers.values():
            try:
                asyncio.create_task(ws.send_json(msg))
                self.messages_sent += 1
            except Exception:
                pass

    def broadcast_trade(self, offer: Dict):
        """Broadcast a trade offer to all peers."""
        self.trade_offers.append({"from": self.agent_id, "offer": offer})
        msg = {
            "type": "trade",
            "sender_id": self.agent_id,
            "timestamp": time.time(),
            "payload": offer,
        }
        for ws in self.ws_peers.values():
            try:
                asyncio.create_task(ws.send_json(msg))
                self.messages_sent += 1
            except Exception:
                pass

    async def start(self):
        """Start the P2P network."""
        self.running = True
        self._app = web.Application()
        self._app.router.add_get("/p2p", self._ws_handler)

        runner = web.AppRunner(self._app)
        await runner.setup()
        site = web.TCPSite(runner, self.ip, self.port)
        await site.start()

        print(f"[P2P] Agent {self.agent_id} listening on ws://{self.ip}:{self.port}/p2p")

        await asyncio.gather(
            self._discovery_beacon(),
            self._discovery_listener(),
            self._gossip_loop(),
        )

    async def stop(self):
        self.running = False
        for ws in self.ws_peers.values():
            await ws.close()

    def get_stats(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "ip": self.ip,
            "port": self.port,
            "peers": len(self.peers),
            "ws_connections": len(self.ws_peers),
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "peer_list": [
                {"id": p.agent_id, "host": p.hostname, "balance": p.token_balance}
                for p in self.peers.values()
            ],
        }
