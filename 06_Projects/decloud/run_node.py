#!/usr/bin/env python3
"""Launch a DeCloud Edge Node."""
import os
import uvicorn
from decloud.node import EdgeNode, create_node_app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", os.environ.get("DECLOUD_PORT", "9000")))
    host = os.environ.get("HOST", "0.0.0.0")
    gateway = os.environ.get("DECLOUD_GATEWAY")
    region = os.environ.get("DECLOUD_REGION", "unknown")
    endpoint = os.environ.get("DECLOUD_ENDPOINT", f"http://127.0.0.1:{port}")
    print(f"[DeCloud Edge] {endpoint} region={region}")
    edge = EdgeNode(
        endpoint=endpoint,
        gateway_url=gateway,
        region=region,
    )
    app = create_node_app(edge)
    uvicorn.run(app, host=host, port=port, reload=False)
