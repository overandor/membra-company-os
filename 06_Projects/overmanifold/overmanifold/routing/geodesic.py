"""
Overmanifold Geodesic Routing System
Optimal traversal across liquidity manifolds according to trust, slippage, proof risk, settlement cost, and latency constraints.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import heapq
import math
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RoutingConstraint(Enum):
    """Types of routing constraints"""
    TRUST_DENSITY = "trust_density"
    MAX_SLIPPAGE = "max_slippage"
    PROOF_RISK = "proof_risk"
    SETTLEMENT_COST = "settlement_cost"
    MAX_LATENCY = "max_latency"
    MIN_LIQUIDITY = "min_liquidity"
    CAPABILITY_REQUIREMENT = "capability_requirement"


@dataclass
class RoutingConstraintValue:
    """Value for a routing constraint"""
    constraint_type: RoutingConstraint
    value: float
    weight: float  # Importance weight (0.0 to 1.0)
    strict: bool  # If True, constraint must be satisfied exactly
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['constraint_type'] = self.constraint_type.value
        return data


@dataclass
class ManifoldEdge:
    """Edge in the liquidity manifold"""
    from_endpoint: str
    to_endpoint: str
    trust_density: float
    slippage: float
    proof_risk: float
    settlement_cost: float
    latency_ms: int
    liquidity_depth: float
    capability_requirements: List[str]
    active: bool
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class GeodesicPath:
    """Optimal path through the manifold"""
    path_id: str
    endpoints: List[str]
    total_cost: float
    total_trust_density: float
    total_latency_ms: int
    total_settlement_cost: float
    total_slippage: float
    constraint_satisfaction: Dict[str, bool]
    confidence_score: float
    estimated_duration_seconds: int
    created_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RoutingMetrics:
    """Metrics for routing performance"""
    total_routes_calculated: int
    average_path_length: float
    average_trust_density: float
    average_latency_ms: int
    successful_routes: int
    failed_routes: int
    constraint_violations: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


class LiquidityManifold:
    """
    Represents the dynamic liquidity manifold as a graph
    where endpoints are nodes and relationships are edges
    """
    
    def __init__(self):
        self.endpoints: Set[str] = set()
        self.edges: Dict[Tuple[str, str], ManifoldEdge] = {}
        self.endpoint_capabilities: Dict[str, Set[str]] = {}
        self.endpoint_liquidity: Dict[str, float] = {}
        self.endpoint_trust: Dict[str, float] = {}
        
    def add_endpoint(self, endpoint_id: str, capabilities: List[str] = None, liquidity: float = 0.0, trust: float = 0.5):
        """Add an endpoint to the manifold"""
        self.endpoints.add(endpoint_id)
        self.endpoint_capabilities[endpoint_id] = set(capabilities or [])
        self.endpoint_liquidity[endpoint_id] = liquidity
        self.endpoint_trust[endpoint_id] = trust
    
    def add_edge(self, edge: ManifoldEdge):
        """Add an edge (relationship) between endpoints"""
        key = (edge.from_endpoint, edge.to_endpoint)
        self.edges[key] = edge
        
        # Ensure endpoints exist
        self.add_endpoint(edge.from_endpoint)
        self.add_endpoint(edge.to_endpoint)
    
    def get_neighbors(self, endpoint_id: str) -> List[str]:
        """Get neighboring endpoints"""
        neighbors = []
        for (from_ep, to_ep), edge in self.edges.items():
            if from_ep == endpoint_id and edge.active:
                neighbors.append(to_ep)
        return neighbors
    
    def get_edge(self, from_endpoint: str, to_endpoint: str) -> Optional[ManifoldEdge]:
        """Get edge between two endpoints"""
        return self.edges.get((from_endpoint, to_endpoint))


class GeodesicRouter:
    """
    Geodesic Router for optimal manifold traversal
    Uses modified Dijkstra's algorithm with multi-constraint optimization
    """
    
    def __init__(self, manifold: LiquidityManifold):
        self.manifold = manifold
        self.routing_cache: Dict[Tuple[str, str, str], GeodesicPath] = {}
        self.routing_metrics = RoutingMetrics(
            total_routes_calculated=0,
            average_path_length=0.0,
            average_trust_density=0.0,
            average_latency_ms=0,
            successful_routes=0,
            failed_routes=0,
            constraint_violations=0
        )
    
    def calculate_geodesic_path(
        self,
        from_endpoint: str,
        to_endpoint: str,
        constraints: List[RoutingConstraintValue] = None
    ) -> Optional[GeodesicPath]:
        """
        Calculate optimal path through the manifold using geodesic routing
        """
        constraints = constraints or []
        
        # Check cache first
        cache_key = self._generate_cache_key(from_endpoint, to_endpoint, constraints)
        if cache_key in self.routing_cache:
            cached_path = self.routing_cache[cache_key]
            # Check if cache is still valid (edges haven't changed)
            if self._is_cache_valid(cached_path):
                return cached_path
        
        # Verify endpoints exist
        if from_endpoint not in self.manifold.endpoints or to_endpoint not in self.manifold.endpoints:
            self.routing_metrics.failed_routes += 1
            return None
        
        # Use A* algorithm with heuristic function
        path = self._astar_search(from_endpoint, to_endpoint, constraints)
        
        if path:
            self.routing_metrics.successful_routes += 1
            self.routing_cache[cache_key] = path
            self._update_metrics(path)
        else:
            self.routing_metrics.failed_routes += 1
        
        self.routing_metrics.total_routes_calculated += 1
        
        return path
    
    def _generate_cache_key(
        self,
        from_endpoint: str,
        to_endpoint: str,
        constraints: List[RoutingConstraintValue]
    ) -> str:
        """Generate cache key for routing result"""
        constraint_str = "|".join([
            f"{c.constraint_type.value}:{c.value}:{c.strict}"
            for c in constraints
        ])
        key_str = f"{from_endpoint}:{to_endpoint}:{constraint_str}"
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]
    
    def _is_cache_valid(self, path: GeodesicPath) -> bool:
        """Check if cached path is still valid"""
        # Check if all edges in path still exist and are active
        for i in range(len(path.endpoints) - 1):
            edge = self.manifold.get_edge(path.endpoints[i], path.endpoints[i + 1])
            if not edge or not edge.active:
                return False
        return True
    
    def _astar_search(
        self,
        start: str,
        goal: str,
        constraints: List[RoutingConstraintValue]
    ) -> Optional[GeodesicPath]:
        """
        A* search algorithm for finding optimal path
        """
        # Priority queue: (f_score, current_endpoint, path, cumulative_metrics)
        open_set = []
        heapq.heappush(open_set, (0.0, start, [start], self._initial_metrics()))
        
        # Track best scores
        g_scores = {start: 0.0}
        f_scores = {start: self._heuristic(start, goal)}
        
        # Track visited
        closed_set = set()
        
        while open_set:
            current_f, current, path, metrics = heapq.heappop(open_set)
            
            if current in closed_set:
                continue
            
            if current == goal:
                return self._construct_path(path, metrics, constraints)
            
            closed_set.add(current)
            
            # Explore neighbors
            for neighbor in self.manifold.get_neighbors(current):
                if neighbor in closed_set:
                    continue
                
                edge = self.manifold.get_edge(current, neighbor)
                if not edge or not edge.active:
                    continue
                
                # Check constraint satisfaction
                constraint_violations = self._check_constraints(edge, metrics, constraints)
                if constraint_violations:
                    # Skip this edge if strict constraints are violated
                    strict_violations = [c for c in constraints if c.strict and c in constraint_violations]
                    if strict_violations:
                        self.routing_metrics.constraint_violations += 1
                        continue
                
                # Calculate new metrics
                new_metrics = self._update_metrics(metrics, edge)
                
                # Calculate costs
                edge_cost = self._calculate_edge_cost(edge, constraints)
                tentative_g_score = g_scores[current] + edge_cost
                
                if neighbor not in g_scores or tentative_g_score < g_scores[neighbor]:
                    g_scores[neighbor] = tentative_g_score
                    h_score = self._heuristic(neighbor, goal)
                    f_score = tentative_g_score + h_score
                    f_scores[neighbor] = f_score
                    
                    new_path = path + [neighbor]
                    heapq.heappush(open_set, (f_score, neighbor, new_path, new_metrics))
        
        return None  # No path found
    
    def _initial_metrics(self) -> Dict:
        """Initialize cumulative metrics"""
        return {
            'cost': 0.0,
            'trust_density': 0.0,
            'latency_ms': 0,
            'settlement_cost': 0.0,
            'slippage': 0.0,
            'hop_count': 0
        }
    
    def _update_metrics(self, metrics: Dict, edge: ManifoldEdge) -> Dict:
        """Update cumulative metrics with edge data"""
        return {
            'cost': metrics['cost'] + self._calculate_edge_cost(edge, []),
            'trust_density': metrics['trust_density'] + edge.trust_density,
            'latency_ms': metrics['latency_ms'] + edge.latency_ms,
            'settlement_cost': metrics['settlement_cost'] + edge.settlement_cost,
            'slippage': metrics['slippage'] + edge.slippage,
            'hop_count': metrics['hop_count'] + 1
        }
    
    def _calculate_edge_cost(self, edge: ManifoldEdge, constraints: List[RoutingConstraintValue]) -> float:
        """Calculate cost of traversing an edge"""
        base_cost = 1.0
        
        # Adjust for trust density (lower trust = higher cost)
        trust_cost = (1.0 - edge.trust_density) * 2.0
        
        # Adjust for slippage
        slippage_cost = edge.slippage * 10.0
        
        # Adjust for proof risk
        risk_cost = edge.proof_risk * 5.0
        
        # Adjust for settlement cost
        settlement_cost = edge.settlement_cost * 0.01
        
        # Adjust for latency
        latency_cost = edge.latency_ms / 1000.0
        
        # Adjust for liquidity depth (lower liquidity = higher cost)
        liquidity_cost = 1.0 / (edge.liquidity_depth + 1.0)
        
        total_cost = base_cost + trust_cost + slippage_cost + risk_cost + settlement_cost + latency_cost + liquidity_cost
        
        # Apply constraint weights
        for constraint in constraints:
            if constraint.constraint_type == RoutingConstraint.TRUST_DENSITY:
                if edge.trust_density < constraint.value:
                    total_cost *= (1.0 + constraint.weight)
            elif constraint.constraint_type == RoutingConstraint.MAX_SLIPPAGE:
                if edge.slippage > constraint.value:
                    total_cost *= (1.0 + constraint.weight)
            elif constraint.constraint_type == RoutingConstraint.MAX_LATENCY:
                if edge.latency_ms > constraint.value * 1000:
                    total_cost *= (1.0 + constraint.weight)
        
        return total_cost
    
    def _check_constraints(
        self,
        edge: ManifoldEdge,
        metrics: Dict,
        constraints: List[RoutingConstraintValue]
    ) -> List[RoutingConstraintValue]:
        """Check which constraints are violated"""
        violations = []
        
        for constraint in constraints:
            if constraint.constraint_type == RoutingConstraint.TRUST_DENSITY:
                if edge.trust_density < constraint.value:
                    violations.append(constraint)
            elif constraint.constraint_type == RoutingConstraint.MAX_SLIPPAGE:
                if edge.slippage > constraint.value:
                    violations.append(constraint)
            elif constraint.constraint_type == RoutingConstraint.PROOF_RISK:
                if edge.proof_risk > constraint.value:
                    violations.append(constraint)
            elif constraint.constraint_type == RoutingConstraint.SETTLEMENT_COST:
                if edge.settlement_cost > constraint.value:
                    violations.append(constraint)
            elif constraint.constraint_type == RoutingConstraint.MAX_LATENCY:
                if edge.latency_ms > constraint.value * 1000:
                    violations.append(constraint)
            elif constraint.constraint_type == RoutingConstraint.MIN_LIQUIDITY:
                if edge.liquidity_depth < constraint.value:
                    violations.append(constraint)
            elif constraint.constraint_type == RoutingConstraint.CAPABILITY_REQUIREMENT:
                required_cap = str(constraint.value)
                if required_cap not in edge.capability_requirements:
                    violations.append(constraint)
        
        return violations
    
    def _heuristic(self, current: str, goal: str) -> float:
        """
        Heuristic function for A* search
        Estimates trust density between current and goal
        """
        # Simple heuristic based on endpoint trust scores
        current_trust = self.manifold.endpoint_trust.get(current, 0.5)
        goal_trust = self.manifold.endpoint_trust.get(goal, 0.5)
        
        # Lower heuristic (better) if both have high trust
        trust_heuristic = 2.0 - (current_trust + goal_trust)
        
        return trust_heuristic
    
    def _construct_path(
        self,
        endpoints: List[str],
        metrics: Dict,
        constraints: List[RoutingConstraintValue]
    ) -> GeodesicPath:
        """Construct GeodesicPath from search results"""
        path_id = hashlib.sha256(
            f"{''.join(endpoints)}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        # Calculate constraint satisfaction
        constraint_satisfaction = {}
        for constraint in constraints:
            constraint_satisfaction[constraint.constraint_type.value] = True  # Simplified
        
        # Calculate average trust density
        avg_trust = metrics['trust_density'] / max(metrics['hop_count'], 1)
        
        # Calculate confidence score based on trust and constraint satisfaction
        confidence_score = min(1.0, avg_trust * 0.8 + 0.2)
        
        # Estimate duration based on latency
        estimated_duration = metrics['latency_ms'] / 1000.0
        
        path = GeodesicPath(
            path_id=path_id,
            endpoints=endpoints,
            total_cost=metrics['cost'],
            total_trust_density=metrics['trust_density'],
            total_latency_ms=metrics['latency_ms'],
            total_settlement_cost=metrics['settlement_cost'],
            total_slippage=metrics['slippage'],
            constraint_satisfaction=constraint_satisfaction,
            confidence_score=confidence_score,
            estimated_duration_seconds=int(estimated_duration),
            created_at=datetime.now().isoformat()
        )
        
        return path
    
    def _update_metrics(self, path: GeodesicPath):
        """Update routing metrics with path data"""
        n = self.routing_metrics.total_routes_calculated
        
        # Update averages
        path_length = len(path.endpoints)
        self.routing_metrics.average_path_length = (
            (self.routing_metrics.average_path_length * n + path_length) / (n + 1)
        )
        
        avg_trust = path.total_trust_density / max(path_length - 1, 1)
        self.routing_metrics.average_trust_density = (
            (self.routing_metrics.average_trust_density * n + avg_trust) / (n + 1)
        )
        
        self.routing_metrics.average_latency_ms = (
            (self.routing_metrics.average_latency_ms * n + path.total_latency_ms) / (n + 1)
        )
    
    def find_alternative_paths(
        self,
        from_endpoint: str,
        to_endpoint: str,
        constraints: List[RoutingConstraintValue] = None,
        max_alternatives: int = 3
    ) -> List[GeodesicPath]:
        """
        Find alternative paths with different characteristics
        """
        constraints = constraints or []
        paths = []
        
        # Find primary path
        primary_path = self.calculate_geodesic_path(from_endpoint, to_endpoint, constraints)
        if primary_path:
            paths.append(primary_path)
        
        # Generate alternative constraint sets
        alternative_constraints = [
            # Higher trust tolerance
            [RoutingConstraintValue(
                RoutingConstraint.TRUST_DENSITY,
                c.value * 0.8 if c.constraint_type == RoutingConstraint.TRUST_DENSITY else c.value,
                c.weight,
                c.strict
            ) if c.constraint_type == RoutingConstraint.TRUST_DENSITY else c
            for c in constraints],
            
            # Higher latency tolerance
            [RoutingConstraintValue(
                RoutingConstraint.MAX_LATENCY,
                c.value * 1.5 if c.constraint_type == RoutingConstraint.MAX_LATENCY else c.value,
                c.weight,
                c.strict
            ) if c.constraint_type == RoutingConstraint.MAX_LATENCY else c
            for c in constraints],
            
            # Lower cost priority
            [RoutingConstraintValue(
                c.constraint_type,
                c.value,
                c.weight * 0.5,
                c.strict
            ) for c in constraints]
        ]
        
        # Find paths with alternative constraints
        for alt_constraints in alternative_constraints:
            if len(paths) >= max_alternatives:
                break
            
            alt_path = self.calculate_geodesic_path(from_endpoint, to_endpoint, alt_constraints)
            if alt_path:
                # Check if this is meaningfully different from existing paths
                is_different = True
                for existing_path in paths:
                    if set(alt_path.endpoints) == set(existing_path.endpoints):
                        is_different = False
                        break
                
                if is_different:
                    paths.append(alt_path)
        
        return paths
    
    def get_routing_metrics(self) -> RoutingMetrics:
        """Get current routing metrics"""
        return self.routing_metrics
    
    def clear_cache(self):
        """Clear routing cache"""
        self.routing_cache.clear()


def main():
    """Example usage of Geodesic Router"""
    # Create liquidity manifold
    manifold = LiquidityManifold()
    
    # Add endpoints
    endpoints = [
        ("endpoint_1", ["messaging", "computation"], 1000.0, 0.8),
        ("endpoint_2", ["storage", "settlement"], 800.0, 0.7),
        ("endpoint_3", ["validation", "oracle"], 1200.0, 0.9),
        ("endpoint_4", ["relay", "liquidity"], 1500.0, 0.85),
        ("endpoint_5", ["governance", "compute"], 900.0, 0.75)
    ]
    
    for ep_id, caps, liquidity, trust in endpoints:
        manifold.add_endpoint(ep_id, caps, liquidity, trust)
    
    # Add edges (relationships)
    edges = [
        ManifoldEdge("endpoint_1", "endpoint_2", 0.7, 0.02, 0.1, 50.0, 100, 500.0, ["messaging"], True),
        ManifoldEdge("endpoint_2", "endpoint_3", 0.8, 0.01, 0.05, 30.0, 150, 800.0, ["storage"], True),
        ManifoldEdge("endpoint_1", "endpoint_3", 0.6, 0.03, 0.15, 80.0, 200, 400.0, ["computation"], True),
        ManifoldEdge("endpoint_3", "endpoint_4", 0.9, 0.01, 0.03, 25.0, 120, 1000.0, ["validation"], True),
        ManifoldEdge("endpoint_4", "endpoint_5", 0.75, 0.02, 0.08, 40.0, 180, 700.0, ["liquidity"], True),
        ManifoldEdge("endpoint_2", "endpoint_5", 0.65, 0.04, 0.12, 60.0, 250, 600.0, ["settlement"], True),
    ]
    
    for edge in edges:
        manifold.add_edge(edge)
    
    # Create geodesic router
    router = GeodesicRouter(manifold)
    
    # Define routing constraints
    constraints = [
        RoutingConstraintValue(RoutingConstraint.TRUST_DENSITY, 0.7, 0.8, True),
        RoutingConstraintValue(RoutingConstraint.MAX_SLIPPAGE, 0.03, 0.6, False),
        RoutingConstraintValue(RoutingConstraint.MAX_LATENCY, 200.0, 0.5, False)
    ]
    
    # Calculate optimal path
    print("=== Calculating Geodesic Path ===\n")
    path = router.calculate_geodesic_path("endpoint_1", "endpoint_5", constraints)
    
    if path:
        print(f"Path found: {' -> '.join(path.endpoints)}")
        print(f"Total cost: {path.total_cost:.2f}")
        print(f"Total trust density: {path.total_trust_density:.2f}")
        print(f"Total latency: {path.total_latency_ms}ms")
        print(f"Confidence score: {path.confidence_score:.2f}")
        print(f"Estimated duration: {path.estimated_duration_seconds}s")
    else:
        print("No path found")
    
    # Find alternative paths
    print("\n=== Alternative Paths ===\n")
    alternatives = router.find_alternative_paths("endpoint_1", "endpoint_5", constraints)
    
    for i, alt_path in enumerate(alternatives, 1):
        print(f"Alternative {i}: {' -> '.join(alt_path.endpoints)}")
        print(f"  Cost: {alt_path.total_cost:.2f}, Confidence: {alt_path.confidence_score:.2f}")
    
    # Get routing metrics
    metrics = router.get_routing_metrics()
    print(f"\n=== Routing Metrics ===")
    print(json.dumps(metrics.to_dict(), indent=2))


if __name__ == '__main__':
    main()