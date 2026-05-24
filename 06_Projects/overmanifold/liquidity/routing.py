"""
Overmanifold Liquidity Manifold Routing Engine
Trust-constrained routing through dynamic liquidity surfaces.
"""

from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import heapq
import math

from ..core.types import (
    EndpointID,
    LiquiditySurface,
    RoutingPath,
    Hash,
    CapabilitySurface,
    CapabilityType
)
from ..core.config import LiquidityConfig


@dataclass
class RouteNode:
    """Node in the routing graph."""
    endpoint_id: EndpointID
    liquidity_surfaces: Dict[str, LiquiditySurface]
    trust_score: float
    capabilities: List[CapabilitySurface]
    
    def get_liquidity_for_token(self, token_address: str) -> Optional[LiquiditySurface]:
        """Get liquidity surface for specific token."""
        return self.liquidity_surfaces.get(token_address)
    
    def has_capability(self, capability_type: CapabilityType) -> bool:
        """Check if node has specific capability."""
        return any(cap.capability_type == capability_type and cap.is_available() 
                   for cap in self.capabilities)


@dataclass
class RouteEdge:
    """Edge in the routing graph."""
    from_node: EndpointID
    to_node: EndpointID
    weight: float  # Combined cost metric
    trust_score: float
    latency_estimate: float
    liquidity_requirement: Optional[str] = None
    
    def efficiency_score(self) -> float:
        """Calculate routing efficiency for this edge."""
        return self.trust_score / (self.weight * self.latency_estimate + 1e-6)


class LiquidityManifold:
    """
    Liquidity manifold managing dynamic liquidity surfaces and routing.
    Treats liquidity as navigable trust-constrained state surfaces.
    """
    
    def __init__(self, config: LiquidityConfig):
        self.config = config
        self.nodes: Dict[EndpointID, RouteNode] = {}
        self.edges: Dict[EndpointID, List[RouteEdge]] = {}
        self.liquidity_surfaces: Dict[str, LiquiditySurface] = {}
        self.manifold_state: Dict = {
            "total_liquidity": 0.0,
            "avg_trust_density": 0.0,
            "avg_curvature": 0.0,
            "last_updated": datetime.utcnow()
        }
    
    def add_node(self, node: RouteNode) -> None:
        """Add node to the manifold."""
        self.nodes[node.endpoint_id] = node
        self.edges[node.endpoint_id] = []
        
        # Add liquidity surfaces to global registry
        for surface in node.liquidity_surfaces.values():
            self.liquidity_surfaces[surface.token_address] = surface
        
        self._update_manifold_state()
    
    def add_edge(self, edge: RouteEdge) -> None:
        """Add edge to the manifold."""
        if edge.from_node not in self.nodes or edge.to_node not in self.nodes:
            raise ValueError("Both nodes must exist in manifold")
        
        self.edges[edge.from_node].append(edge)
        self._update_manifold_state()
    
    def remove_node(self, endpoint_id: EndpointID) -> bool:
        """Remove node from manifold."""
        if endpoint_id in self.nodes:
            del self.nodes[endpoint_id]
            
            # Remove associated edges
            if endpoint_id in self.edges:
                del self.edges[endpoint_id]
            
            # Remove edges pointing to this node
            for from_node, edge_list in self.edges.items():
                self.edges[from_node] = [e for e in edge_list if e.to_node != endpoint_id]
            
            self._update_manifold_state()
            return True
        return False
    
    def find_optimal_route(self, from_endpoint: EndpointID, to_endpoint: EndpointID,
                          token_address: str, max_hops: int = 10) -> Optional[RoutingPath]:
        """
        Find optimal routing path using trust-constrained Dijkstra's algorithm.
        Optimizes for trust, latency, and liquidity efficiency.
        """
        if from_endpoint not in self.nodes or to_endpoint not in self.nodes:
            return None
        
        # Priority queue: (total_cost, current_node, path, cumulative_trust, total_latency)
        pq = [(0.0, from_endpoint, [], 1.0, 0.0)]
        visited = set()
        
        while pq:
            total_cost, current, path, cum_trust, cum_latency = heapq.heappop(pq)
            
            if current in visited:
                continue
            
            visited.add(current)
            new_path = path + [current]
            
            if current == to_endpoint:
                # Calculate final metrics
                total_trust = cum_trust
                return RoutingPath(
                    path_id=Hash.from_data(new_path),
                    endpoints=[self.nodes[eid].endpoint_id for eid in new_path],
                    total_cost=total_cost,
                    total_trust=total_trust,
                    estimated_latency=cum_latency,
                    liquidity_requirements=[token_address]
                )
            
            if len(new_path) >= max_hops:
                continue
            
            # Explore neighbors
            for edge in self.edges.get(current, []):
                if edge.to_node in visited:
                    continue
                
                # Check trust constraint
                if edge.trust_score < self.config.trust_threshold:
                    continue
                
                # Check liquidity requirement
                if edge.liquidity_requirement:
                    surface = self.liquidity_surfaces.get(edge.liquidity_requirement)
                    if surface and surface.effective_liquidity() < self.config.min_liquidity_depth:
                        continue
                
                # Calculate edge cost (inverse of efficiency)
                edge_cost = 1.0 / (edge.efficiency_score() + 1e-6)
                new_cost = total_cost + edge_cost
                new_trust = cum_trust * edge.trust_score
                new_latency = cum_latency + edge.latency_estimate
                
                heapq.heappush(pq, (new_cost, edge.to_node, new_path, new_trust, new_latency))
        
        return None
    
    def find_liquidity_path(self, token_address: str, required_amount: float,
                           from_endpoint: EndpointID) -> List[EndpointID]:
        """
        Find path through liquidity surfaces for a specific token.
        Returns endpoints that can provide the required liquidity.
        """
        liquidity_path = []
        remaining_amount = required_amount
        
        # Start from source endpoint
        current = from_endpoint
        visited = set()
        
        while remaining_amount > 0 and current not in visited:
            visited.add(current)
            node = self.nodes.get(current)
            
            if not node:
                break
            
            # Check if current node has sufficient liquidity
            surface = node.get_liquidity_for_token(token_address)
            if surface and surface.effective_liquidity() >= remaining_amount:
                liquidity_path.append(current)
                break
            
            # Add current node to path if it has some liquidity
            if surface and surface.effective_liquidity() > 0:
                liquidity_path.append(current)
                remaining_amount -= surface.effective_liquidity()
            
            # Find next hop with liquidity
            best_next = None
            best_liquidity = 0.0
            
            for edge in self.edges.get(current, []):
                if edge.to_node in visited:
                    continue
                
                next_node = self.nodes.get(edge.to_node)
                if next_node:
                    next_surface = next_node.get_liquidity_for_token(token_address)
                    if next_surface and next_surface.effective_liquidity() > best_liquidity:
                        best_liquidity = next_surface.effective_liquidity()
                        best_next = edge.to_node
            
            if best_next:
                current = best_next
            else:
                break
        
        return liquidity_path
    
    def calculate_manifold_curvature(self, token_address: str) -> float:
        """
        Calculate curvature of liquidity manifold for a token.
        Curvature represents liquidity efficiency - higher is better.
        """
        surfaces = [
            surface for surface in self.liquidity_surfaces.values()
            if surface.token_address == token_address
        ]
        
        if not surfaces:
            return 0.0
        
        # Curvature = weighted average of surface curvatures by depth
        total_depth = sum(surface.depth for surface in surfaces)
        if total_depth == 0:
            return 0.0
        
        weighted_curvature = sum(
            surface.curvature * (surface.depth / total_depth)
            for surface in surfaces
        )
        
        return weighted_curvature
    
    def get_trust_constrained_path(self, from_endpoint: EndpointID, 
                                   min_trust: float) -> List[EndpointID]:
        """Get all reachable endpoints with trust above threshold."""
        reachable = []
        visited = set()
        queue = [from_endpoint]
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            
            visited.add(current)
            node = self.nodes.get(current)
            
            if node and node.trust_score >= min_trust:
                reachable.append(current)
            
            # Add neighbors to queue
            for edge in self.edges.get(current, []):
                if edge.to_node not in visited and edge.trust_score >= min_trust:
                    queue.append(edge.to_node)
        
        return reachable
    
    def estimate_slippage(self, path: List[EndpointID], token_address: str, 
                         amount: float) -> float:
        """
        Estimate slippage for a given path and amount.
        Considers liquidity depth and curvature along the path.
        """
        total_slippage = 0.0
        
        for i, endpoint_id in enumerate(path):
            node = self.nodes.get(endpoint_id)
            if not node:
                continue
            
            surface = node.get_liquidity_for_token(token_address)
            if surface:
                # Slippage increases with amount relative to depth
                # Decreases with curvature (efficiency)
                depth_factor = amount / (surface.depth + 1e-6)
                curvature_benefit = surface.curvature * self.config.curvature_weight
                edge_slippage = depth_factor * (1.0 - curvature_benefit)
                total_slippage += edge_slippage
        
        return min(total_slippage, self.config.max_slippage)
    
    def update_liquidity_surface(self, surface: LiquiditySurface) -> None:
        """Update or add liquidity surface."""
        self.liquidity_surfaces[surface.token_address] = surface
        
        # Update nodes that reference this surface
        for node in self.nodes.values():
            if surface.token_address in node.liquidity_surfaces:
                node.liquidity_surfaces[surface.token_address] = surface
        
        self._update_manifold_state()
    
    def _update_manifold_state(self) -> None:
        """Update aggregate manifold state metrics."""
        if not self.liquidity_surfaces:
            self.manifold_state = {
                "total_liquidity": 0.0,
                "avg_trust_density": 0.0,
                "avg_curvature": 0.0,
                "last_updated": datetime.utcnow()
            }
            return
        
        total_liquidity = sum(surface.depth for surface in self.liquidity_surfaces.values())
        avg_trust = sum(surface.trust_density for surface in self.liquidity_surfaces.values()) / len(self.liquidity_surfaces)
        avg_curvature = sum(surface.curvature for surface in self.liquidity_surfaces.values()) / len(self.liquidity_surfaces)
        
        self.manifold_state = {
            "total_liquidity": total_liquidity,
            "avg_trust_density": avg_trust,
            "avg_curvature": avg_curvature,
            "last_updated": datetime.utcnow()
        }
    
    def get_manifold_snapshot(self) -> Dict:
        """Get snapshot of current manifold state."""
        return {
            "state": self.manifold_state,
            "node_count": len(self.nodes),
            "edge_count": sum(len(edges) for edges in self.edges.values()),
            "liquidity_surface_count": len(self.liquidity_surfaces),
            "tokens": list(set(surface.token_address for surface in self.liquidity_surfaces.values()))
        }