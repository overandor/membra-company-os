"""Cryptographic commitments: SHA-256 digests and Merkle trees with inclusion proofs.

This is the substrate every higher layer commits to. A commitment is a binding,
collision-resistant promise about content that does not by itself reveal the
content (Section 4 of the BlurHash64 paper: "Identity ... whether the
representation can verify sameness").
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

LEAF_PREFIX = b"\x00"
NODE_PREFIX = b"\x01"


def sha256_bytes(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_file(path: str, chunk_size: int = 1024 * 1024) -> str:
    """Stream a file through SHA-256 without loading it fully into memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _leaf_hash(data: bytes) -> bytes:
    return hashlib.sha256(LEAF_PREFIX + data).digest()


def _node_hash(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(NODE_PREFIX + left + right).digest()


@dataclass
class MerkleProof:
    leaf_index: int
    leaf_hash: bytes
    siblings: list[bytes] = field(default_factory=list)
    directions: list[str] = field(default_factory=list)  # "L" or "R" per level

    def verify(self, root: bytes) -> bool:
        current = self.leaf_hash
        for sibling, direction in zip(self.siblings, self.directions):
            if direction == "R":
                current = _node_hash(current, sibling)
            else:
                current = _node_hash(sibling, current)
        return current == root

    def to_dict(self) -> dict:
        return {
            "leaf_index": self.leaf_index,
            "leaf_hash": self.leaf_hash.hex(),
            "siblings": [s.hex() for s in self.siblings],
            "directions": self.directions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MerkleProof":
        return cls(
            leaf_index=data["leaf_index"],
            leaf_hash=bytes.fromhex(data["leaf_hash"]),
            siblings=[bytes.fromhex(s) for s in data["siblings"]],
            directions=list(data["directions"]),
        )


class MerkleTree:
    """A binary Merkle tree over arbitrary byte leaves (RFC 6962-style domain
    separation between leaf and internal node hashes to defeat second-preimage
    attacks against the tree structure)."""

    def __init__(self, leaves: list[bytes]):
        if not leaves:
            raise ValueError("MerkleTree requires at least one leaf")
        self.leaves = list(leaves)
        self._levels = self._build()

    def _build(self) -> list[list[bytes]]:
        level = [_leaf_hash(leaf) for leaf in self.leaves]
        levels = [level]
        while len(level) > 1:
            next_level = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else level[i]
                next_level.append(_node_hash(left, right))
            levels.append(next_level)
            level = next_level
        return levels

    @property
    def root(self) -> bytes:
        return self._levels[-1][0]

    @property
    def root_hex(self) -> str:
        return self.root.hex()

    def proof(self, index: int) -> MerkleProof:
        if index < 0 or index >= len(self.leaves):
            raise IndexError("leaf index out of range")
        siblings: list[bytes] = []
        directions: list[str] = []
        idx = index
        for level in self._levels[:-1]:
            is_right = idx % 2 == 1
            sibling_idx = idx - 1 if is_right else idx + 1
            if sibling_idx >= len(level):
                sibling_idx = idx  # odd tail duplicates itself
            siblings.append(level[sibling_idx])
            directions.append("L" if is_right else "R")
            idx //= 2
        return MerkleProof(
            leaf_index=index,
            leaf_hash=_leaf_hash(self.leaves[index]),
            siblings=siblings,
            directions=directions,
        )


def merkle_root_of_chunks(data: bytes, chunk_size: int = 4096) -> tuple[str, int]:
    """Chunk arbitrary bytes and return (root_hex, chunk_count). Used to commit
    to a file body in fixed-size shards so a Level 7 partial-body glyph can
    later prove individual chunks belong to the whole without revealing the rest.
    """
    if not data:
        chunks = [b""]
    else:
        chunks = [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]
    tree = MerkleTree(chunks)
    return tree.root_hex, len(chunks)
