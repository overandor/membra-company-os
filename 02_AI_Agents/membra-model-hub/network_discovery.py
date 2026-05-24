"""P2P network discovery — UDP multicast for LAN + HTTP gossip for mesh state."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import platform as plat
import socket
import struct
import time
from contextlib import suppress
from datetime import datetime, timezone
from typing import Any

import httpx

from shared_models import ModelCard, NodeState, RegistryGossip

DISCOVERY_MULTICAST_ADDR = os.getenv("MEMBRA_DISCOVERY_ADDR", "239.255.42.99")
DISCOVERY_PORT = int(os.getenv("MEMBRA_DISCOVERY_PORT", "42424"))
GOSSIP_INTERVAL = int(os.getenv("MEMBRA_GOSSIP_INTERVAL", "5"))
PEER_TIMEOUT = int(os.getenv("MEMBRA_PEER_TIMEOUT", "30"))


def _get_local_ip() -> str:
    """Best-effort local IP for binding."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


class DiscoveryProtocol:
    """Handles UDP multicast discovery and HTTP gossip."""

    def __init__(
        self,
        node_id: str,
        api_port: int,
        bootstrap_peers: list[str] | None = None,
    ):
        self.node_id = node_id
        self.api_port = api_port
        self.local_ip = _get_local_ip()
        self.api_endpoint = f"http://{self.local_ip}:{api_port}"
        self.ws_endpoint = f"ws://{self.local_ip}:{api_port}/ws"
        self.bootstrap_peers = list(bootstrap_peers or [])
        self.peers: dict[str, NodeState] = {}
        self.models: dict[str, ModelCard] = {}
        self._lock = asyncio.Lock()
        self._stop = asyncio.Event()
        self._udp_transport: asyncio.DatagramTransport | None = None

    async def start(self) -> None:
        await self._start_udp_listener()
        asyncio.create_task(self._gossip_loop())
        asyncio.create_task(self._prune_loop())
        # Seed with bootstrap peers
        for peer_url in self.bootstrap_peers:
            await self._probe_peer(peer_url)

    async def stop(self) -> None:
        self._stop.set()
        if self._udp_transport:
            self._udp_transport.close()

    async def announce_model(self, card: ModelCard) -> None:
        async with self._lock:
            self.models[card.model_id] = card

    def build_gossip_payload(self, node_state: NodeState) -> bytes:
        gossip = RegistryGossip(
            node=node_state,
            models=list(self.models.values()),
            known_peers=list(self.peers.keys()),
        )
        return json.dumps(gossip.model_dump(mode="json"), separators=(",", ":")).encode()

    async def _start_udp_listener(self) -> None:
        loop = asyncio.get_running_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", DISCOVERY_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(DISCOVERY_MULTICAST_ADDR), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.setblocking(False)
        self._udp_transport, _ = await loop.create_datagram_endpoint(
            lambda: _UDPHandler(self), sock=sock
        )

    async def _gossip_loop(self) -> None:
        while not self._stop.is_set():
            # Multicast beacon
            msg = f"MEMBRA_HUB|{self.node_id}|{self.local_ip}|{self.api_port}".encode()
            await self._send_multicast(msg)
            # HTTP gossip to known peers
            async with self._lock:
                peer_urls = [p.api_endpoint for p in self.peers.values()]
            for url in peer_urls:
                await self._gossip_to(url)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=GOSSIP_INTERVAL)
            except asyncio.TimeoutError:
                continue

    async def _send_multicast(self, data: bytes) -> None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as s:
                s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
                s.sendto(data, (DISCOVERY_MULTICAST_ADDR, DISCOVERY_PORT))
        except Exception:
            pass

    async def _gossip_to(self, url: str) -> None:
        from shared_models import NodeCapabilities  # lazy to avoid circular issues

        try:
            # Build a minimal self-state for gossip
            node_state = NodeState(
                node_id=self.node_id,
                hostname=plat.node(),
                api_endpoint=self.api_endpoint,
                ws_endpoint=self.ws_endpoint,
                caps=NodeCapabilities(),
            )
            payload = self.build_gossip_payload(node_state)
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.post(f"{url}/gossip", content=payload)
                if r.status_code == 200:
                    data = r.json()
                    await self._merge_gossip(data)
        except Exception:
            pass

    async def _probe_peer(self, url: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # First try gossip endpoint for full mesh state
                r = await client.get(f"{url}/health")
                if r.status_code == 200:
                    # Health only tells us the node exists; fetch gossip for state
                    try:
                        g = await client.get(f"{url}/gossip")
                        if g.status_code == 200:
                            await self._merge_gossip(g.json())
                    except Exception:
                        pass
        except Exception:
            pass

    async def _merge_gossip(self, data: dict[str, Any]) -> None:
        """Incorporate a gossip payload into local state."""
        try:
            gossip = RegistryGossip.model_validate(data)
        except Exception:
            return
        async with self._lock:
            now = datetime.now(timezone.utc)
            self.peers[gossip.node.node_id] = gossip.node
            for m in gossip.models:
                existing = self.models.get(m.model_id)
                if existing is None:
                    self.models[m.model_id] = m
                else:
                    # Merge shard locations
                    for shard in m.shards:
                        for idx, es in enumerate(existing.shards):
                            if es.shard_id == shard.shard_id:
                                merged_nodes = list(set(es.node_ids + shard.node_ids))
                                existing.shards[idx] = es.model_copy(update={"node_ids": merged_nodes})
                                break
                        else:
                            existing.shards.append(shard)
            # Add peers' known peers as potential bootstrap candidates
            for peer_url in gossip.known_peers:
                if peer_url not in [p.api_endpoint for p in self.peers.values()]:
                    if peer_url != self.api_endpoint:
                        pass  # we could probe here, but avoid recursion explosion

    async def _prune_loop(self) -> None:
        while not self._stop.is_set():
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=PEER_TIMEOUT)
            except asyncio.TimeoutError:
                pass
            now = datetime.now(timezone.utc)
            async with self._lock:
                stale = [
                    nid
                    for nid, p in self.peers.items()
                    if (now - p.last_seen).total_seconds() > PEER_TIMEOUT
                ]
                for nid in stale:
                    del self.peers[nid]

    async def handle_beacon(self, data: bytes, addr: tuple[str, int]) -> None:
        try:
            text = data.decode()
            if not text.startswith("MEMBRA_HUB|"):
                return
            _, nid, ip, port = text.split("|")
            if nid == self.node_id:
                return
            url = f"http://{ip}:{port}"
            await self._probe_peer(url)
        except Exception:
            pass


class _UDPHandler(asyncio.DatagramProtocol):
    def __init__(self, protocol: DiscoveryProtocol):
        self.protocol = protocol

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        asyncio.create_task(self.protocol.handle_beacon(data, addr))
