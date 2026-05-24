"""Gateway — API server, reverse proxy, and network coordinator.

Responsibilities:
  • Accept developer deploy / update / delete requests
  • Write deployment records to the chain
  • Distribute bundles to edge nodes
  • Route incoming HTTP traffic to the best edge node per app
  • Track node health and capacity
"""
import asyncio
import hashlib
import json
import random
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from decloud.chain import DeploymentChain, DeploymentRecord
from decloud.store import ContentStore


@dataclass
class NodeEntry:
    node_id: str
    endpoint: str
    region: str = "unknown"
    health: str = "healthy"
    active_apps: List[str] = field(default_factory=list)
    capacity_remaining: int = 100
    last_seen: float = field(default_factory=time.time)


class Gateway:
    """Central coordinator (can be federated later)."""

    def __init__(self, data_dir: str = "./decloud_gateway"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.chain = DeploymentChain(str(self.data_dir / "chain"))
        self.store = ContentStore(str(self.data_dir / "store"))
        self.nodes: Dict[str, NodeEntry] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(30)
            now = time.time()
            stale = [nid for nid, n in self.nodes.items() if now - n.last_seen > 60]
            for nid in stale:
                self.nodes.pop(nid, None)

    async def deploy(self, app_id: str, owner: str, bundle_dir: str,
                     metadata: Optional[dict] = None) -> str:
        cid = self.store.put_bundle(bundle_dir, app_id)
        rec = DeploymentRecord(
            app_id=app_id,
            cid=cid,
            owner=owner,
            action="deploy",
            metadata=metadata or {},
        )
        await self.chain.add_records([rec])
        asyncio.create_task(self._distribute(app_id, cid))
        return cid

    async def update(self, app_id: str, owner: str, bundle_dir: str,
                     metadata: Optional[dict] = None) -> str:
        cid = self.store.put_bundle(bundle_dir, app_id)
        rec = DeploymentRecord(
            app_id=app_id,
            cid=cid,
            owner=owner,
            action="update",
            metadata=metadata or {},
        )
        await self.chain.add_records([rec])
        asyncio.create_task(self._distribute(app_id, cid))
        return cid

    async def delete(self, app_id: str, owner: str):
        rec = DeploymentRecord(
            app_id=app_id,
            cid="",
            owner=owner,
            action="delete",
        )
        await self.chain.add_records([rec])
        asyncio.create_task(self._teardown(app_id))

    async def _distribute(self, app_id: str, cid: str):
        healthy = [n for n in self.nodes.values() if n.health == "healthy"]
        if not healthy:
            return
        random.shuffle(healthy)
        targets = healthy[:3]
        for node in targets:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    await client.post(f"{node.endpoint}/deploy", json={
                        "app_id": app_id,
                        "cid": cid,
                    })
                    node.active_apps.append(app_id)
            except Exception:
                pass

    async def _teardown(self, app_id: str):
        for node in self.nodes.values():
            if app_id in node.active_apps:
                node.active_apps.remove(app_id)

    def pick_node(self, app_id: str) -> Optional[NodeEntry]:
        candidates = [n for n in self.nodes.values()
                      if app_id in n.active_apps and n.health == "healthy"]
        if not candidates:
            candidates = [n for n in self.nodes.values() if n.health == "healthy"]
        if not candidates:
            return None
        return min(candidates, key=lambda n: len(n.active_apps))

    def get_status(self) -> dict:
        return {
            "nodes": len(self.nodes),
            "apps": len(self.chain.list_apps()),
            "chain_tip": self.chain.get_tip().index,
        }


def create_gateway_app(gw: Gateway) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await gw.start()
        yield
        await gw.stop()

    app = FastAPI(title="DeCloud Gateway", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return gw.get_status()

    @app.post("/deploy")
    async def deploy(req: Request):
        data = await req.json()
        app_id = data["app_id"]
        owner = data.get("owner", "anonymous")
        bundle_dir = data.get("bundle_dir")
        if not bundle_dir or not Path(bundle_dir).is_dir():
            raise HTTPException(status_code=400, detail="bundle_dir must be an existing directory")
        cid = await gw.deploy(app_id, owner, bundle_dir, data.get("metadata"))
        return {"app_id": app_id, "cid": cid, "status": "deployed"}

    @app.post("/update")
    async def update(req: Request):
        data = await req.json()
        app_id = data["app_id"]
        owner = data.get("owner", "anonymous")
        bundle_dir = data.get("bundle_dir")
        if not bundle_dir or not Path(bundle_dir).is_dir():
            raise HTTPException(status_code=400, detail="bundle_dir must be an existing directory")
        cid = await gw.update(app_id, owner, bundle_dir, data.get("metadata"))
        return {"app_id": app_id, "cid": cid, "status": "updated"}

    @app.post("/delete")
    async def delete_app(req: Request):
        data = await req.json()
        app_id = data["app_id"]
        owner = data.get("owner", "anonymous")
        await gw.delete(app_id, owner)
        return {"app_id": app_id, "status": "deleted"}

    @app.get("/apps")
    def list_apps():
        return {"apps": [
            {"app_id": aid, "latest": asdict(gw.chain.get_latest(aid))}
            for aid in gw.chain.list_apps()
        ]}

    @app.get("/apps/{app_id}")
    def app_info(app_id: str):
        rec = gw.chain.get_latest(app_id)
        if not rec:
            raise HTTPException(status_code=404, detail="App not found")
        nodes = [n.endpoint for n in gw.nodes.values() if app_id in n.active_apps]
        return {"app_id": app_id, "record": rec, "nodes": nodes}

    @app.get("/apps/{app_id}/history")
    def app_history(app_id: str):
        return {"app_id": app_id, "history": gw.chain.get_history(app_id)}

    @app.get("/chain/tip")
    def chain_tip():
        tip = gw.chain.get_tip()
        return {"index": tip.index, "hash": tip.hash, "timestamp": tip.timestamp}

    @app.get("/chain/block/{index}")
    def chain_block(index: int):
        for b in gw.chain.blocks:
            if b.index == index:
                return {
                    "index": b.index,
                    "timestamp": b.timestamp,
                    "records": [json.loads(r.canonical()) for r in b.records],
                    "prev_hash": b.prev_hash,
                    "hash": b.hash,
                }
        raise HTTPException(status_code=404, detail="Block not found")

    @app.get("/store/{cid}")
    def get_store(cid: str):
        data = gw.store.get(cid)
        if data is None:
            raise HTTPException(status_code=404, detail="CID not found")
        return StreamingResponse(iter([data]), media_type="application/octet-stream")

    # ---- Node registry ----
    @app.post("/nodes/register")
    async def register_node(req: Request):
        data = await req.json()
        nid = data["node_id"]
        gw.nodes[nid] = NodeEntry(
            node_id=nid,
            endpoint=data["endpoint"],
            region=data.get("region", "unknown"),
        )
        return {"ok": True}

    @app.post("/nodes/heartbeat")
    async def node_heartbeat(req: Request):
        data = await req.json()
        nid = data["node_id"]
        if nid in gw.nodes:
            gw.nodes[nid].last_seen = time.time()
            gw.nodes[nid].active_apps = data.get("active_apps", [])
            gw.nodes[nid].capacity_remaining = data.get("capacity_remaining", 0)
        return {"ok": True}

    @app.get("/nodes")
    def list_nodes():
        return {"nodes": [
            {"node_id": n.node_id, "endpoint": n.endpoint, "region": n.region,
             "health": n.health, "active_apps": n.active_apps,
             "capacity_remaining": n.capacity_remaining}
            for n in gw.nodes.values()
        ]}

    # ---- Reverse proxy ----
    @app.api_route("/proxy/{app_id}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
    async def proxy(app_id: str, path: str, req: Request):
        node = gw.pick_node(app_id)
        if not node:
            raise HTTPException(status_code=503, detail="No healthy nodes available for this app")
        url = f"{node.endpoint}/serve/{app_id}/{path}"
        if req.method == "GET":
            try:
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    upstream = await client.get(url, headers={k: v for k, v in req.headers.items() if k.lower() != "host"})
                    return StreamingResponse(
                        upstream.aiter_raw(),
                        status_code=upstream.status_code,
                        headers=dict(upstream.headers),
                    )
            except Exception:
                raise HTTPException(status_code=502, detail="Upstream error")
        raise HTTPException(status_code=405, detail="Method not supported yet")

    @app.api_route("/proxy/{app_id}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
    async def proxy_root(app_id: str, req: Request):
        return await proxy(app_id, "", req)

    return app
