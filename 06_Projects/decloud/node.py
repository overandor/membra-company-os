"""Node — Edge server that hosts and serves decentralized app bundles.

Each edge node:
  1. Registers with a gateway (or bootstraps P2P)
  2. Accepts deployment downloads by CID
  3. Extracts bundles and serves them over HTTP
  4. Gossips health + peer state to other nodes
"""
import asyncio
import hashlib
import json
import random
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from decloud.store import ContentStore
from decloud.chain import DeploymentChain, DeploymentRecord


@dataclass
class NodeInfo:
    node_id: str
    endpoint: str
    region: str = "unknown"
    health: str = "healthy"
    active_apps: List[str] = field(default_factory=list)
    capacity_remaining: int = 100
    last_seen: float = field(default_factory=time.time)


class EdgeNode:
    """An edge node in the DeCloud network."""

    def __init__(
        self,
        node_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        gateway_url: Optional[str] = None,
        data_dir: str = "./decloud_node",
        region: str = "unknown",
    ):
        self.node_id = node_id or hashlib.sha256(
            f"{time.time()}{random.random()}".encode()
        ).hexdigest()[:16]
        self.endpoint = endpoint or f"http://127.0.0.1:9000"
        self.gateway_url = gateway_url
        self.region = region
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.apps_dir = self.data_dir / "apps"
        self.apps_dir.mkdir(exist_ok=True)
        self.store = ContentStore(str(self.data_dir / "store"))
        self.chain = DeploymentChain(str(self.data_dir / "chain"))

        self.active_apps: Dict[str, Path] = {}
        self.peers: Dict[str, NodeInfo] = {}
        self._shutdown = False
        self._gossip_task: Optional[asyncio.Task] = None
        self._health_task: Optional[asyncio.Task] = None

    async def start(self):
        self._shutdown = False
        self._gossip_task = asyncio.create_task(self._gossip_loop())
        self._health_task = asyncio.create_task(self._health_loop())
        if self.gateway_url:
            await self._register_with_gateway()
            await self._sync_chain()

    async def stop(self):
        self._shutdown = True
        for task in (self._gossip_task, self._health_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def _register_with_gateway(self):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(f"{self.gateway_url}/nodes/register", json={
                    "node_id": self.node_id,
                    "endpoint": self.endpoint,
                    "region": self.region,
                })
        except Exception:
            pass

    async def _sync_chain(self):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(f"{self.gateway_url}/chain/tip")
                data = r.json()
                remote_tip = data.get("index", 0)
                local_tip = self.chain.get_tip().index
                if remote_tip > local_tip:
                    for i in range(local_tip + 1, remote_tip + 1):
                        block_r = await client.get(f"{self.gateway_url}/chain/block/{i}")
                        block_data = block_r.json()
                        for rec_raw in block_data.get("records", []):
                            rec = DeploymentRecord(**rec_raw)
                            if rec.action == "delete":
                                self._teardown_app(rec.app_id)
                            elif rec.cid and self.store.has(rec.cid):
                                self._activate_app(rec.app_id, rec.cid)
                            else:
                                await self._fetch_and_activate(rec.app_id, rec.cid)
        except Exception:
            pass

    def _activate_app(self, app_id: str, cid: str) -> Path:
        dest = self.apps_dir / app_id
        if dest.exists():
            import shutil
            shutil.rmtree(dest)
        self.store.extract_bundle(cid, str(dest))
        self.active_apps[app_id] = dest
        return dest

    async def _fetch_and_activate(self, app_id: str, cid: str):
        if not self.gateway_url:
            return
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(f"{self.gateway_url}/store/{cid}")
                if r.status_code == 200:
                    self.store.put(r.content, app_id)
                    self._activate_app(app_id, cid)
        except Exception:
            pass

    def _teardown_app(self, app_id: str):
        self.active_apps.pop(app_id, None)
        app_path = self.apps_dir / app_id
        if app_path.exists():
            import shutil
            shutil.rmtree(app_path)

    def get_app_path(self, app_id: str) -> Optional[Path]:
        return self.active_apps.get(app_id)

    async def _health_loop(self):
        while not self._shutdown:
            try:
                if self.gateway_url:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        await client.post(f"{self.gateway_url}/nodes/heartbeat", json={
                            "node_id": self.node_id,
                            "active_apps": list(self.active_apps.keys()),
                            "capacity_remaining": 100 - len(self.active_apps),
                        })
            except Exception:
                pass
            await asyncio.sleep(10)

    async def _gossip_loop(self):
        while not self._shutdown:
            try:
                await self._gossip_once()
            except Exception:
                pass
            await asyncio.sleep(15)

    async def _gossip_once(self):
        targets = list(self.peers.values())
        if not targets and self.gateway_url:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    r = await client.get(f"{self.gateway_url}/nodes")
                    for p in r.json().get("nodes", []):
                        if p["node_id"] != self.node_id:
                            self.peers[p["node_id"]] = NodeInfo(**p)
            except Exception:
                pass
            return
        random.shuffle(targets)
        for peer in targets[:3]:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(f"{peer.endpoint}/peers/gossip", json={
                        "from": self.node_id,
                        "peers": [asdict(p) for p in self.peers.values()],
                        "active_apps": list(self.active_apps.keys()),
                    })
            except Exception:
                peer.health = "unreachable"

    def handle_gossip(self, payload: dict):
        for p in payload.get("peers", []):
            nid = p["node_id"]
            if nid != self.node_id:
                self.peers[nid] = NodeInfo(**p)
        sender = payload.get("from")
        if sender in self.peers:
            self.peers[sender].last_seen = time.time()
            self.peers[sender].active_apps = payload.get("active_apps", [])

    def get_status(self) -> dict:
        return {
            "node_id": self.node_id,
            "endpoint": self.endpoint,
            "region": self.region,
            "health": "healthy",
            "active_apps": list(self.active_apps.keys()),
            "peers": len(self.peers),
            "chain_tip": self.chain.get_tip().index,
        }


def create_node_app(edge: EdgeNode) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await edge.start()
        yield
        await edge.stop()

    app = FastAPI(title=f"DeCloud Edge {edge.node_id}", lifespan=lifespan)

    @app.get("/health")
    def health():
        return edge.get_status()

    @app.post("/deploy")
    async def deploy(req: Request):
        data = await req.json()
        app_id = data["app_id"]
        cid = data["cid"]
        if not edge.store.has(cid):
            await edge._fetch_and_activate(app_id, cid)
        else:
            edge._activate_app(app_id, cid)
        return {"ok": True, "app_id": app_id, "cid": cid}

    @app.post("/peers/gossip")
    async def gossip(req: Request):
        data = await req.json()
        edge.handle_gossip(data)
        return {"ok": True}

    @app.get("/serve/{app_id}/{path:path}")
    async def serve(app_id: str, path: str):
        app_path = edge.get_app_path(app_id)
        if not app_path:
            raise HTTPException(status_code=404, detail="App not deployed on this node")
        target = app_path / path if path else app_path / "index.html"
        if not target.exists():
            target = app_path / "index.html"
        if target.exists() and target.is_file():
            return FileResponse(str(target))
        raise HTTPException(status_code=404, detail="File not found")

    @app.get("/serve/{app_id}")
    async def serve_root(app_id: str):
        return await serve(app_id, "")

    return app
