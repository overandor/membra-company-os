"""MEMBRA Agent OS — FastAPI entry point."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.agent_network import router as agent_router

app = FastAPI(
    title="MEMBRA Agent OS",
    description="60 Autonomous LLM Employees as Network Nodes",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router, prefix="/v1/agent-network")


@app.get("/")
def root():
    return {
        "name": "MEMBRA Agent OS",
        "version": "1.0.0",
        "agents": 60,
        "endpoints": {
            "agents": "/v1/agent-network/agents",
            "departments": "/v1/agent-network/departments",
            "stats": "/v1/agent-network/stats",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
