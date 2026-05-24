"""
Overmanifold Merkle Proof System
Cryptographic proof system for state transitions and provenance tracking.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from core.types import Hash, StateTransition, StateTransitionType, EndpointID


@dataclass
class MerkleNode:
    """Node in a Merkle tree."""
    hash: Hash
    left: Optional['MerkleNode'] = None
    right: Optional['MerkleNode'] = None
    is_leaf: bool = False
    data: Optional[Dict] = None


@dataclass
class MerkleProof:
    """Merkle proof for inclusion verification."""
    leaf_hash: Hash
    root_hash: Hash
    proof_path: List[Tuple[Hash, bool]]  # (sibling_hash, is_left)
    leaf_index: int
    
    def verify(self, expected_root: Hash) -> bool:
        """Verify Merkle proof against expected root."""
        current_hash = self.leaf_hash
        
        for sibling_hash, is_left in self.proof_path:
            if is_left:
                # Current hash is right child
                combined = sibling_hash.value + current_hash.value
            else:
                # Current hash is left child
                combined = current_hash.value + sibling_hash.value
            
            current_hash = Hash.from_data(combined)
        
        return current_hash.value == expected_root.value
    
    def to_dict(self) -> Dict:
        """Convert Merkle proof to dictionary."""
        return {
            "leaf_hash": str(self.leaf_hash),
            "root_hash": str(self.root_hash),
            "proof_path": [(str(hash), is_left) for hash, is_left in self.proof_path],
            "leaf_index": self.leaf_index
        }


class MerkleTree:
    """
    Merkle tree for constructing and managing cryptographic proofs.
    Supports incremental updates and efficient proof generation.
    """
    
    def __init__(self, hash_algorithm: str = "sha256"):
        self.hash_algorithm = hash_algorithm
        self.leaves: List[Dict] = []
        self.root: Optional[MerkleNode] = None
        self.leaf_hashes: List[Hash] = []
    
    def add_leaf(self, data: Dict) -> Hash:
        """Add leaf data to the tree."""
        leaf_hash = Hash.from_data(data, self.hash_algorithm)
        self.leaves.append(data)
        self.leaf_hashes.append(leaf_hash)
        return leaf_hash
    
    def build_tree(self) -> None:
        """Build the Merkle tree from current leaves."""
        if not self.leaves:
            self.root = None
            return
        
        # Create leaf nodes
        nodes = [
            MerkleNode(
                hash=leaf_hash,
                is_leaf=True,
                data=data
            )
            for leaf_hash, data in zip(self.leaf_hashes, self.leaves)
        ]
        
        # Build tree bottom-up
        while len(nodes) > 1:
            next_level = []
            
            for i in range(0, len(nodes), 2):
                if i + 1 < len(nodes):
                    # Pair of nodes
                    combined_hash = self._combine_hashes(nodes[i].hash, nodes[i + 1].hash)
                    parent = MerkleNode(
                        hash=combined_hash,
                        left=nodes[i],
                        right=nodes[i + 1]
                    )
                else:
                    # Odd node - promote to next level
                    parent = nodes[i]
                
                next_level.append(parent)
            
            nodes = next_level
        
        self.root = nodes[0] if nodes else None
    
    def get_root_hash(self) -> Optional[Hash]:
        """Get the root hash of the tree."""
        if self.root is None:
            self.build_tree()
        return self.root.hash if self.root else None
    
    def generate_proof(self, leaf_index: int) -> Optional[MerkleProof]:
        """Generate Merkle proof for leaf at index."""
        if self.root is None:
            self.build_tree()
        
        if leaf_index >= len(self.leaves):
            return None
        
        proof_path = []
        current_index = leaf_index
        nodes_at_level = self.leaf_hashes.copy()
        
        while len(nodes_at_level) > 1:
            level_size = len(nodes_at_level)
            is_left = current_index % 2 == 0
            
            if is_left:
                if current_index + 1 < level_size:
                    sibling_hash = nodes_at_level[current_index + 1]
                    proof_path.append((sibling_hash, True))  # sibling is left
            else:
                sibling_hash = nodes_at_level[current_index - 1]
                proof_path.append((sibling_hash, False))  # sibling is right
            
            # Move to parent level
            current_index = current_index // 2
            nodes_at_level = self._get_parent_level_hashes(nodes_at_level)
        
        return MerkleProof(
            leaf_hash=self.leaf_hashes[leaf_index],
            root_hash=self.get_root_hash(),
            proof_path=proof_path,
            leaf_index=leaf_index
        )
    
    def verify_leaf(self, leaf_data: Dict, proof: MerkleProof) -> bool:
        """Verify leaf data against Merkle proof."""
        leaf_hash = Hash.from_data(leaf_data, self.hash_algorithm)
        if leaf_hash.value != proof.leaf_hash.value:
            return False
        
        return proof.verify(self.get_root_hash())
    
    def _combine_hashes(self, left: Hash, right: Hash) -> Hash:
        """Combine two hashes to create parent hash."""
        combined = left.value + right.value
        return Hash.from_data(combined, self.hash_algorithm)
    
    def _get_parent_level_hashes(self, child_hashes: List[Hash]) -> List[Hash]:
        """Get hashes for parent level of tree."""
        parent_hashes = []
        
        for i in range(0, len(child_hashes), 2):
            if i + 1 < len(child_hashes):
                parent_hash = self._combine_hashes(child_hashes[i], child_hashes[i + 1])
            else:
                parent_hash = child_hashes[i]
            parent_hashes.append(parent_hash)
        
        return parent_hashes


class StateTransitionMerkleTree(MerkleTree):
    """
    Specialized Merkle tree for state transitions.
    Includes metadata and provenance tracking.
    """
    
    def __init__(self):
        super().__init__()
        self.transitions: List[StateTransition] = []
    
    def add_transition(self, transition: StateTransition) -> Hash:
        """Add state transition to the tree."""
        transition_data = {
            "transition_id": str(transition.transition_id),
            "transition_type": transition.transition_type.value,
            "from_state": str(transition.from_state),
            "to_state": str(transition.to_state),
            "timestamp": transition.timestamp.isoformat(),
            "actor": str(transition.actor),
            "transport": transition.transport.value,
            "proof_count": len(transition.proofs)
        }
        
        hash_value = self.add_leaf(transition_data)
        self.transitions.append(transition)
        return hash_value
    
    def get_transition_proof(self, transition_index: int) -> Optional[MerkleProof]:
        """Get Merkle proof for specific transition."""
        return self.generate_proof(transition_index)
    
    def verify_transition(self, transition: StateTransition, proof: MerkleProof) -> bool:
        """Verify state transition against Merkle proof."""
        transition_data = {
            "transition_id": str(transition.transition_id),
            "transition_type": transition.transition_type.value,
            "from_state": str(transition.from_state),
            "to_state": str(transition.to_state),
            "timestamp": transition.timestamp.isoformat(),
            "actor": str(transition.actor),
            "transport": transition.transport.value,
            "proof_count": len(transition.proofs)
        }
        
        return self.verify_leaf(transition_data, proof)


class ProvenanceTracker:
    """
    Tracker for recursive provenance trees with hash-linked contributions.
    Maintains complete history of state transitions and their relationships.
    """
    
    def __init__(self):
        self.trees: Dict[str, StateTransitionMerkleTree] = {}
        self.transition_index: Dict[Hash, Tuple[str, int]] = {}  # transition_id -> (tree_id, index)
        self.parent_child_links: Dict[Hash, List[Hash]] = {}  # parent -> children
        self.child_parent_links: Dict[Hash, Hash] = {}  # child -> parent
    
    def create_tree(self, tree_id: str) -> StateTransitionMerkleTree:
        """Create a new provenance tree."""
        tree = StateTransitionMerkleTree()
        self.trees[tree_id] = tree
        return tree
    
    def add_transition(self, tree_id: str, transition: StateTransition, 
                       parent_transition_id: Optional[Hash] = None) -> Hash:
        """Add transition to provenance tree with optional parent link."""
        if tree_id not in self.trees:
            self.create_tree(tree_id)
        
        tree = self.trees[tree_id]
        index = len(tree.transitions)
        transition_hash = tree.add_transition(transition)
        
        # Index the transition
        self.transition_index[transition.transition_id] = (tree_id, index)
        
        # Create parent-child links
        if parent_transition_id:
            self.parent_child_links.setdefault(parent_transition_id, []).append(transition.transition_id)
            self.child_parent_links[transition.transition_id] = parent_transition_id
        
        return transition_hash
    
    def get_transition_proof(self, transition_id: Hash) -> Optional[MerkleProof]:
        """Get Merkle proof for transition."""
        if transition_id not in self.transition_index:
            return None
        
        tree_id, index = self.transition_index[transition_id]
        tree = self.trees.get(tree_id)
        if tree:
            return tree.get_transition_proof(index)
        return None
    
    def get_provenance_chain(self, transition_id: Hash) -> List[Hash]:
        """Get full provenance chain for a transition."""
        chain = []
        current = transition_id
        
        while current in self.child_parent_links:
            chain.append(current)
            current = self.child_parent_links[current]
        
        chain.append(current)  # Add root
        return chain
    
    def get_child_transitions(self, transition_id: Hash) -> List[Hash]:
        """Get all child transitions of a given transition."""
        return self.parent_child_links.get(transition_id, [])
    
    def verify_provenance(self, transition_id: Hash) -> bool:
        """Verify complete provenance chain for a transition."""
        proof = self.get_transition_proof(transition_id)
        if not proof:
            return False
        
        # Get the tree and verify the proof
        tree_id, index = self.transition_index[transition_id]
        tree = self.trees.get(tree_id)
        if not tree:
            return False
        
        transition = tree.transitions[index]
        return tree.verify_transition(transition, proof)
    
    def get_tree_root(self, tree_id: str) -> Optional[Hash]:
        """Get root hash of a specific tree."""
        tree = self.trees.get(tree_id)
        if tree:
            return tree.get_root_hash()
        return None
    
    def get_provenance_snapshot(self) -> Dict:
        """Get snapshot of entire provenance state."""
        return {
            "total_trees": len(self.trees),
            "total_transitions": sum(len(tree.transitions) for tree in self.trees.values()),
            "trees": {
                tree_id: {
                    "root_hash": str(tree.get_root_hash()),
                    "transition_count": len(tree.transitions)
                }
                for tree_id, tree in self.trees.items()
            },
            "transition_index_size": len(self.transition_index),
            "parent_child_links": len(self.parent_child_links)
        }