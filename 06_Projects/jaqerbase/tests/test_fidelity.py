import pytest

from arrowcap.fidelity import (
    FidelityLevel,
    compute_lambda_score,
    detect_broad_type,
    fuzzy_hash,
    fuzzy_similarity,
    perceptual_hash,
    project,
    shannon_entropy,
)

SAMPLE_SOURCE = b'''
import os

class Example:
    def run(self):
        return 1
'''


@pytest.fixture
def sample_py(tmp_path):
    path = tmp_path / "sample.py"
    path.write_bytes(SAMPLE_SOURCE)
    return str(path)


def test_detect_broad_type_by_magic_bytes(tmp_path):
    path = tmp_path / "thing.bin"
    path.write_bytes(b"%PDF-1.4 rest of file")
    assert detect_broad_type(str(path)) == "pdf"


def test_detect_broad_type_by_extension(tmp_path):
    path = tmp_path / "data.csv"
    path.write_bytes(b"a,b,c\n1,2,3\n")
    assert detect_broad_type(str(path)) == "dataset"


def test_detect_broad_type_source_extension(sample_py):
    assert detect_broad_type(sample_py) == "source"


def test_shannon_entropy_zero_for_empty():
    assert shannon_entropy(b"") == 0.0


def test_shannon_entropy_zero_for_constant_bytes():
    assert shannon_entropy(b"aaaaaaaa") == 0.0


def test_shannon_entropy_positive_for_varied_bytes():
    assert shannon_entropy(bytes(range(256))) == pytest.approx(8.0, abs=1e-9)


def test_project_null_level_discloses_nothing(sample_py):
    glyph = project(sample_py, FidelityLevel.NULL)
    assert not any([glyph.identity, glyph.resemblance, glyph.recoverability, glyph.executability])
    assert glyph.payload == {}


def test_project_presence_level_true_and_false(sample_py, tmp_path):
    present = project(sample_py, FidelityLevel.PRESENCE)
    assert present.payload["exists"] is True
    missing = project(str(tmp_path / "does_not_exist.py"), FidelityLevel.PRESENCE)
    assert missing.payload["exists"] is False


def test_project_missing_file_raises_above_presence(tmp_path):
    missing = str(tmp_path / "nope.py")
    with pytest.raises(FileNotFoundError):
        project(missing, FidelityLevel.TYPE)


def test_project_type_level(sample_py):
    glyph = project(sample_py, FidelityLevel.TYPE)
    assert glyph.payload["type"] == "source"
    assert glyph.identity is False and glyph.resemblance is True


def test_project_metadata_level(sample_py):
    glyph = project(sample_py, FidelityLevel.METADATA)
    assert glyph.payload["extension"] == ".py"
    assert glyph.payload["size_bytes"] > 0


def test_project_feature_level_extracts_ast_info(sample_py):
    glyph = project(sample_py, FidelityLevel.FEATURE)
    assert "os" in glyph.payload["imports"]
    assert glyph.payload["class_count"] == 1
    assert glyph.payload["function_count"] == 1


def test_project_sketch_level_has_fuzzy_hash_and_redacted_preview(sample_py):
    glyph = project(sample_py, FidelityLevel.SKETCH)
    assert ":" in glyph.payload["fuzzy_hash"]
    assert glyph.payload["preview_redacted"]
    # No Pillow installed in this environment -> perceptual_hash gracefully None.
    assert glyph.payload["perceptual_hash"] is None


def test_project_receipt_level_has_sha256_and_merkle_root(sample_py):
    glyph = project(sample_py, FidelityLevel.RECEIPT)
    assert len(glyph.payload["sha256"]) == 64
    assert len(glyph.payload["merkle_root"]) == 64
    assert glyph.identity is True
    assert glyph.resemblance is False


def test_project_partial_body_level_proofs_verify_against_merkle_root(sample_py):
    from arrowcap.commitment import MerkleProof

    glyph = project(sample_py, FidelityLevel.PARTIAL_BODY)
    root = bytes.fromhex(glyph.payload["merkle_root"])
    for chunk in glyph.payload["revealed_chunks"]:
        proof = MerkleProof.from_dict(chunk["proof"])
        assert proof.verify(root)


def test_project_encrypted_body_level_round_trips(sample_py):
    import base64

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    glyph = project(sample_py, FidelityLevel.ENCRYPTED_BODY)
    assert "generated_key_b64" in glyph.payload
    key = base64.b64decode(glyph.payload["generated_key_b64"])
    nonce = base64.b64decode(glyph.payload["nonce_b64"])
    ciphertext = base64.b64decode(glyph.payload["ciphertext_b64"])
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    assert plaintext == SAMPLE_SOURCE


def test_project_encrypted_body_with_caller_supplied_key(sample_py):
    import os as _os

    key = _os.urandom(32)
    glyph = project(sample_py, FidelityLevel.ENCRYPTED_BODY, encryption_key=key)
    assert "generated_key_b64" not in glyph.payload


def test_project_full_transport_level_reconstructs_exact_bytes(sample_py):
    import base64

    glyph = project(sample_py, FidelityLevel.FULL_TRANSPORT)
    assert base64.b64decode(glyph.payload["body_b64"]) == SAMPLE_SOURCE
    assert all([glyph.identity, glyph.resemblance, glyph.recoverability, glyph.executability])


def test_project_rejects_unknown_level(sample_py):
    with pytest.raises(ValueError):
        project(sample_py, 99)


def test_perceptual_hash_returns_none_without_pillow(sample_py):
    assert perceptual_hash(sample_py) is None


def test_fuzzy_hash_identical_data_has_similarity_one():
    data = b"the quick brown fox jumps over the lazy dog" * 20
    sig_a = fuzzy_hash(data)
    sig_b = fuzzy_hash(data)
    assert fuzzy_similarity(sig_a, sig_b) == 1.0


def test_fuzzy_hash_unrelated_data_has_lower_similarity():
    sig_a = fuzzy_hash(b"the quick brown fox jumps over the lazy dog" * 20)
    sig_b = fuzzy_hash(bytes(range(256)) * 10)
    similar_self = fuzzy_similarity(sig_a, sig_a)
    cross = fuzzy_similarity(sig_a, sig_b)
    assert cross <= similar_self


def test_fuzzy_similarity_mismatched_block_size_is_zero():
    small_sig = fuzzy_hash(b"x" * 10)
    large_sig = fuzzy_hash(b"y" * 1_000_000)
    assert fuzzy_similarity(small_sig, large_sig) == 0.0


def test_compute_lambda_score_full_transport_is_lowest_friction(sample_py):
    full = project(sample_py, FidelityLevel.FULL_TRANSPORT)
    null = project(sample_py, FidelityLevel.NULL)
    assert compute_lambda_score(full) < compute_lambda_score(null)


def test_compute_lambda_score_receipt_lower_than_sketch(sample_py):
    receipt = project(sample_py, FidelityLevel.RECEIPT)
    sketch = project(sample_py, FidelityLevel.SKETCH)
    assert compute_lambda_score(receipt) < compute_lambda_score(sketch)
