#!/usr/bin/env python3
"""Launch the DeCloud Gateway."""
import os
import uvicorn
from decloud.gateway import Gateway, create_gateway_app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", os.environ.get("DECLOUD_PORT", "8080")))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"[DeCloud Gateway] http://{host}:{port}")
    print(f"[DeCloud Gateway] Health: http://{host}:{port}/health")
    gw = Gateway()
    app = create_gateway_app(gw)
    uvicorn.run(app, host=host, port=port, reload=False)
