import pytest

from arrowcap.commitment import (
    MerkleProof,
    MerkleTree,
    hash_file,
    merkle_root_of_chunks,
    sha256_bytes,
    sha256_hex,
)


def test_sha256_hex_matches_bytes():
    data = b"hello arrowcap"
    assert sha256_hex(data) == sha256_bytes(data).hex()
    assert len(sha256_hex(data)) == 64


def test_hash_file_streams_correctly(tmp_path):
    path = tmp_path / "blob.bin"
    payload = b"x" * 5000 + b"y" * 5000
    path.write_bytes(payload)
    assert hash_file(str(path)) == sha256_hex(payload)


@pytest.mark.parametrize("leaf_count", [1, 2, 3, 7, 8])
def test_merkle_tree_all_proofs_verify(leaf_count):
    leaves = [f"leaf-{i}".encode() for i in range(leaf_count)]
    tree = MerkleTree(leaves)
    for i in range(leaf_count):
        proof = tree.proof(i)
        assert proof.verify(tree.root)


def test_merkle_proof_rejects_tampered_root():
    leaves = [f"leaf-{i}".encode() for i in range(5)]
    tree = MerkleTree(leaves)
    proof = tree.proof(2)
    bogus_root = bytes(b ^ 0xFF for b in tree.root)
    assert not proof.verify(bogus_root)


def test_merkle_proof_round_trips_through_dict():
    leaves = [f"leaf-{i}".encode() for i in range(4)]
    tree = MerkleTree(leaves)
    proof = tree.proof(3)
    restored = MerkleProof.from_dict(proof.to_dict())
    assert restored.verify(tree.root)


def test_merkle_tree_rejects_empty_leaves():
    with pytest.raises(ValueError):
        MerkleTree([])


def test_merkle_tree_proof_out_of_range():
    tree = MerkleTree([b"only-leaf"])
    with pytest.raises(IndexError):
        tree.proof(1)


def test_merkle_root_of_chunks_empty_data():
    root_hex, count = merkle_root_of_chunks(b"")
    assert count == 1
    assert len(root_hex) == 64


def test_merkle_root_of_chunks_multi_chunk():
    data = bytes(range(256)) * 50  # 12800 bytes -> 3 chunks at 4096
    root_hex, count = merkle_root_of_chunks(data, chunk_size=4096)
    assert count == 4
    assert len(root_hex) == 64
