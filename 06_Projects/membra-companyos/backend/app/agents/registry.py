"""MEMBRA Agent Registry — Discovery, lookup, and orchestration for 60 agents."""
import asyncio
import importlib
import os
import pkgutil
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent


class AgentRegistry:
    """Central registry for all 60 MEMBRA agents.

    Naming: {name}.{department}.membra
    Example: alex.strategy.membra, linda.marketing.membra
    """

    def __init__(self, ollama_host: Optional[str] = None, mode: str = "local"):
        self.ollama_host = ollama_host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.mode = mode
        self._agents: Dict[str, BaseAgent] = {}
        self._classes: Dict[str, Any] = {}
        self._meta: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    async def load_all(self) -> int:
        """Auto-discover and instantiate all 60 agent classes."""
        if self._loaded:
            return len(self._agents)

        # Import all agent modules
        import app.agents as agents_pkg
        for _, modname, _ in pkgutil.iter_modules(agents_pkg.__path__):
            if modname.endswith("_membra"):
                try:
                    mod = importlib.import_module(f"app.agents.{modname}")
                    for attr_name in dir(mod):
                        attr = getattr(mod, attr_name)
                        if (isinstance(attr, type) and
                            issubclass(attr, BaseAgent) and
                            attr is not BaseAgent and
                            getattr(attr, "AGENT_ID", None)):

                            agent_id = attr.AGENT_ID
                            self._classes[agent_id] = attr
                            # Instantiate
                            instance = attr(
                                ollama_host=self.ollama_host,
                                mode=self.mode,
                            )
                            self._agents[agent_id] = instance
                            self._meta[agent_id] = instance.to_dict()
                except Exception as e:
                    print(f"[Registry] Failed to load {modname}: {e}")

        self._loaded = True
        return len(self._agents)

    def get(self, agent_id: str) -> Optional[BaseAgent]:
        return self._agents.get(agent_id)

    def list_all(self) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self._agents.values()]

    def by_department(self, dept: str) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self._agents.values() if a.department == dept]

    def departments(self) -> List[Dict[str, Any]]:
        depts = {}
        for a in self._agents.values():
            d = a.department
            if d not in depts:
                depts[d] = {"id": d, "name": d.title(), "count": 0, "agents": []}
            depts[d]["count"] += 1
            depts[d]["agents"].append(a.agent_id)
        return list(depts.values())

    def stats(self) -> Dict[str, Any]:
        all_agents = list(self._agents.values())
        return {
            "total": len(all_agents),
            "idle": sum(1 for a in all_agents if a.status == "idle"),
            "busy": sum(1 for a in all_agents if a.status == "busy"),
            "error": sum(1 for a in all_agents if a.status == "error"),
            "offline": sum(1 for a in all_agents if a.status == "offline"),
            "total_runs": sum(a.total_runs for a in all_agents),
            "total_contributions": sum(a.total_contributions for a in all_agents),
            "departments": len(set(a.department for a in all_agents)),
        }

    async def start_network(self, base_port: int = 9000):
        """Start TCP servers for all agents on sequential ports."""
        port = base_port
        for agent_id, agent in self._agents.items():
            assigned = await agent.start_server(host="0.0.0.0", port=port)
            print(f"[Network] {agent_id} listening on port {assigned}")
            port = assigned + 1
        # Cross-link peers
        for agent_id, agent in self._agents.items():
            for peer_id, peer in self._agents.items():
                if peer_id != agent_id:
                    agent.peers[peer_id] = {
                        "port": peer.network_port,
                        "department": peer.department,
                        "status": peer.status,
                    }

    async def stop_all(self):
        for agent in self._agents.values():
            await agent.stop()

    def job_descriptions(self) -> Dict[str, str]:
        return {aid: agent.job_description for aid, agent in self._agents.items()}
