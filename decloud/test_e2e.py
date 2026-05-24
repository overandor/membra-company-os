#!/usr/bin/env python3
"""End-to-end integration test using FastAPI TestClient."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/Users/alep/Downloads")

from fastapi.testclient import TestClient
from decloud.gateway import Gateway, create_gateway_app
from decloud.node import EdgeNode, create_node_app


def test_gateway_node_deploy():
    with tempfile.TemporaryDirectory() as gw_dir, tempfile.TemporaryDirectory() as node_dir:
        gw = Gateway(data_dir=gw_dir)
        gw_app = create_gateway_app(gw)
        gw_client = TestClient(gw_app)

        edge = EdgeNode(
            node_id="node-1",
            endpoint="http://test-node",
            data_dir=node_dir,
        )
        node_app = create_node_app(edge)
        node_client = TestClient(node_app)

        # Register node manually (normally done via HTTP)
        gw.nodes["node-1"] = type("N", (), {
            "node_id": "node-1",
            "endpoint": "http://testserver",
            "region": "test",
            "health": "healthy",
            "active_apps": [],
            "capacity_remaining": 100,
            "last_seen": 9999999999,
        })()

        # Create a static site
        site = Path(tempfile.mkdtemp())
        (site / "index.html").write_text("<h1>Hello DeCloud</h1>")

        # Deploy via gateway
        r = gw_client.post("/deploy", json={
            "app_id": "demo",
            "owner": "alice",
            "bundle_dir": str(site),
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "deployed"
        cid = data["cid"]

        # Copy bundle from gateway store to node store, then activate
        bundle_bytes = gw.store.get(cid)
        edge.store.put(bundle_bytes, "demo")
        r2 = node_client.post("/deploy", json={"app_id": "demo", "cid": cid})
        assert r2.status_code == 200, r2.text

        # Serve via node
        r3 = node_client.get("/serve/demo")
        assert r3.status_code == 200
        assert "Hello DeCloud" in r3.text

        # Check app info
        r4 = gw_client.get("/apps/demo")
        assert r4.status_code == 200
        assert r4.json()["record"]["cid"] == cid

        print("e2e test passed")


if __name__ == "__main__":
    test_gateway_node_deploy()
