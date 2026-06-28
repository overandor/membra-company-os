"""The BlurHash64 fidelity ladder: ten disclosure levels from null glyph to
full Base64 transport, plus the lambda friction heuristic.

Level 0  Null            -- no useful information
Level 1  Presence        -- file exists
Level 2  Type             -- broad class (source/pdf/image/archive/binary/...)
Level 3  Metadata         -- size, extension, timestamps, mime guess
Level 4  Feature          -- extracted structure (imports, line count, entropy)
Level 5  Sketch           -- fuzzy hash + perceptual hash + redacted preview
Level 6  Receipt          -- SHA-256 + Merkle commitments, time anchor
Level 7  Partial-Body     -- selected chunks with Merkle inclusion proofs
Level 8  Encrypted-Body   -- full body, AES-256-GCM sealed, key out-of-band
Level 9  Full-Transport   -- full body, Base64, directly reconstructable
"""

from __future__ import annotations

import base64
import math
import mimetypes
import os
import time
from collections import Counter
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .commitment import MerkleTree, sha256_hex

CHUNK_SIZE = 4096

_MAGIC_SIGNATURES: list[tuple[bytes, str]] = [
    (b"%PDF", "pdf"),
    (b"\x89PNG\r\n\x1a\n", "image"),
    (b"\xff\xd8\xff", "image"),
    (b"GIF87a", "image"),
    (b"GIF89a", "image"),
    (b"PK\x03\x04", "archive"),
    (b"\x7fELF", "binary"),
    (b"MZ", "binary"),
    (b"\xca\xfe\xba\xbe", "binary"),
    (b"SQLite format 3\x00", "dataset"),
]

_SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".c", ".cpp", ".h",
    ".hpp", ".java", ".rb", ".php", ".sh", ".sql", ".html", ".css", ".json",
    ".yaml", ".yml", ".toml",
}
_DATASET_EXTENSIONS = {".csv", ".parquet", ".jsonl", ".db", ".sqlite"}
_MODEL_EXTENSIONS = {".pt", ".onnx", ".safetensors", ".h5", ".pkl"}


class FidelityLevel(IntEnum):
    NULL = 0
    PRESENCE = 1
    TYPE = 2
    METADATA = 3
    FEATURE = 4
    SKETCH = 5
    RECEIPT = 6
    PARTIAL_BODY = 7
    ENCRYPTED_BODY = 8
    FULL_TRANSPORT = 9


@dataclass
class Glyph:
    level: int
    identity: bool
    resemblance: bool
    recoverability: bool
    executability: bool
    payload: dict[str, Any] = field(default_factory=dict)
    lambda_score: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "level_name": FidelityLevel(self.level).name,
            "identity": self.identity,
            "resemblance": self.resemblance,
            "recoverability": self.recoverability,
            "executability": self.executability,
            "lambda_score": self.lambda_score,
            "payload": self.payload,
        }


def detect_broad_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    try:
        with open(path, "rb") as fh:
            header = fh.read(16)
    except OSError:
        header = b""
    for sig, kind in _MAGIC_SIGNATURES:
        if header.startswith(sig):
            return kind
    if ext in _SOURCE_EXTENSIONS:
        return "source"
    if ext in _DATASET_EXTENSIONS:
        return "dataset"
    if ext in _MODEL_EXTENSIONS:
        return "model"
    if header[:1] and all(32 <= b < 127 or b in (9, 10, 13) for b in header):
        return "text"
    return "binary"


def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    length = len(data)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def extract_features(path: str, broad_type: str, data: bytes) -> dict[str, Any]:
    features: dict[str, Any] = {"byte_entropy": round(shannon_entropy(data), 4)}
    if broad_type == "source" and path.endswith(".py"):
        import ast

        try:
            tree = ast.parse(data.decode("utf-8", errors="replace"))
            imports = sorted(
                {
                    alias.name
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Import)
                    for alias in node.names
                }
                | {
                    node.module
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom) and node.module
                }
            )
            functions = [
                n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
            ]
            classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            features.update(
                {
                    "imports": imports,
                    "function_count": len(functions),
                    "class_count": len(classes),
                    "line_count": data.count(b"\n") + 1,
                }
            )
        except SyntaxError:
            features["line_count"] = data.count(b"\n") + 1
    elif broad_type in ("source", "text"):
        text = data.decode("utf-8", errors="replace")
        features.update(
            {
                "line_count": data.count(b"\n") + 1,
                "word_count": len(text.split()),
            }
        )
    elif broad_type == "image":
        dims = _try_image_dimensions(path)
        if dims:
            features["dimensions"] = dims
    return features


def _try_image_dimensions(path: str) -> Optional[tuple[int, int]]:
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(path) as img:
            return img.size
    except Exception:
        return None


def perceptual_hash(path: str) -> Optional[str]:
    """8x8 average-hash (aHash). Returns None if Pillow is unavailable or the
    file is not a decodable image -- this is a resemblance fingerprint, not a
    cryptographic commitment."""
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(path) as img:
            small = img.convert("L").resize((8, 8))
            pixels = list(small.getdata())
    except Exception:
        return None
    avg = sum(pixels) / len(pixels)
    bits = "".join("1" if p > avg else "0" for p in pixels)
    return f"{int(bits, 2):016x}"


def _rolling_trigger_hash(window: bytes) -> int:
    h = 0
    for b in window:
        h = ((h << 5) + h + b) & 0xFFFFFFFF
    return h


def fuzzy_hash(data: bytes, window: int = 7) -> str:
    """A context-triggered piecewise hash in the spirit of Kornblum's CTPH
    (ssdeep): a rolling hash over a sliding window emits a new piece boundary
    whenever it hits a block-size-derived trigger, and each piece contributes
    one base64 character to the signature. Two files that are mostly similar
    will trigger boundaries at mostly the same offsets and so produce mostly
    matching signatures, which is the basis of fuzzy_similarity below."""
    if not data:
        return "3:"
    block_size = 3
    while block_size * 64 < len(data) and block_size < 2**20:
        block_size *= 2

    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    signature_chars: list[str] = []
    piece_acc = 0
    for i in range(len(data)):
        piece_acc = (piece_acc + data[i]) & 0xFFFFFFFF
        if i >= window - 1:
            h = _rolling_trigger_hash(data[max(0, i - window + 1) : i + 1])
            if h % block_size == block_size - 1:
                signature_chars.append(alphabet[piece_acc % 64])
                piece_acc = 0
    signature_chars.append(alphabet[piece_acc % 64])
    return f"{block_size}:{''.join(signature_chars)}"


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[-1]


def fuzzy_similarity(sig_a: str, sig_b: str) -> float:
    """Normalized similarity in [0, 1] between two fuzzy_hash signatures.
    Signatures from different block sizes are not directly comparable and
    are scored as dissimilar (0.0), matching ssdeep's blocksize-matching rule."""
    try:
        bs_a, body_a = sig_a.split(":", 1)
        bs_b, body_b = sig_b.split(":", 1)
    except ValueError:
        return 0.0
    if bs_a != bs_b:
        return 0.0
    if not body_a and not body_b:
        return 1.0
    distance = _levenshtein(body_a, body_b)
    max_len = max(len(body_a), len(body_b), 1)
    return max(0.0, 1.0 - distance / max_len)


def project(
    path: str,
    level: int,
    *,
    encryption_key: Optional[bytes] = None,
    partial_chunk_indices: Optional[list[int]] = None,
) -> Glyph:
    """Project `path` to a Glyph at the requested fidelity `level`."""
    level = int(level)
    if level not in FidelityLevel.__members__.values() and level not in range(0, 10):
        raise ValueError(f"unknown fidelity level: {level}")

    if level == FidelityLevel.NULL:
        return Glyph(level, False, False, False, False, {})

    exists = os.path.isfile(path)
    if level == FidelityLevel.PRESENCE:
        return Glyph(level, False, False, False, False, {"exists": exists})

    if not exists:
        raise FileNotFoundError(path)

    broad_type = detect_broad_type(path)
    if level == FidelityLevel.TYPE:
        return Glyph(level, False, True, False, False, {"type": broad_type})

    stat = os.stat(path)
    if level == FidelityLevel.METADATA:
        mime, _ = mimetypes.guess_type(path)
        payload = {
            "type": broad_type,
            "size_bytes": stat.st_size,
            "extension": os.path.splitext(path)[1],
            "mime": mime,
            "mtime": stat.st_mtime,
        }
        return Glyph(level, False, True, False, False, payload)

    with open(path, "rb") as fh:
        data = fh.read()

    if level == FidelityLevel.FEATURE:
        features = extract_features(path, broad_type, data)
        return Glyph(level, False, True, False, False, {"type": broad_type, **features})

    if level == FidelityLevel.SKETCH:
        payload = {
            "type": broad_type,
            "fuzzy_hash": fuzzy_hash(data),
            "perceptual_hash": perceptual_hash(path),
            "preview_redacted": _redacted_preview(data),
        }
        return Glyph(level, False, True, False, False, payload)

    if level == FidelityLevel.RECEIPT:
        chunks = [data[i : i + CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)] or [b""]
        tree = MerkleTree(chunks)
        payload = {
            "type": broad_type,
            "size_bytes": stat.st_size,
            "sha256": sha256_hex(data),
            "merkle_root": tree.root_hex,
            "chunk_count": len(chunks),
            "chunk_size": CHUNK_SIZE,
            "time_anchor": time.time(),
        }
        return Glyph(level, True, False, False, False, payload)

    if level == FidelityLevel.PARTIAL_BODY:
        chunks = [data[i : i + CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)] or [b""]
        tree = MerkleTree(chunks)
        indices = partial_chunk_indices
        if indices is None:
            indices = [0] if len(chunks) == 1 else sorted({0, len(chunks) - 1})
        revealed = []
        for idx in indices:
            proof = tree.proof(idx)
            revealed.append(
                {
                    "index": idx,
                    "chunk_b64": base64.b64encode(chunks[idx]).decode("ascii"),
                    "proof": proof.to_dict(),
                }
            )
        payload = {
            "type": broad_type,
            "merkle_root": tree.root_hex,
            "chunk_count": len(chunks),
            "chunk_size": CHUNK_SIZE,
            "revealed_chunks": revealed,
        }
        return Glyph(level, True, True, True, False, payload)

    if level == FidelityLevel.ENCRYPTED_BODY:
        key_provided = encryption_key is not None
        key = encryption_key or os.urandom(32)
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        payload = {
            "type": broad_type,
            "sha256_plaintext": sha256_hex(data),
            "cipher": "AES-256-GCM",
            "nonce_b64": base64.b64encode(nonce).decode("ascii"),
            "ciphertext_b64": base64.b64encode(ciphertext).decode("ascii"),
        }
        if not key_provided:
            payload["generated_key_b64"] = base64.b64encode(key).decode("ascii")
            payload["key_distribution_note"] = (
                "key was generated because none was supplied; transmit it "
                "out-of-band, never alongside this glyph"
            )
        return Glyph(level, True, False, True, True, payload)

    if level == FidelityLevel.FULL_TRANSPORT:
        payload = {
            "type": broad_type,
            "sha256": sha256_hex(data),
            "body_b64": base64.b64encode(data).decode("ascii"),
        }
        return Glyph(level, True, True, True, True, payload)

    raise ValueError(f"unhandled fidelity level: {level}")


def _redacted_preview(data: bytes, head: int = 24) -> str:
    text = data[:head]
    printable = "".join(chr(b) if 32 <= b < 127 else "." for b in text)
    return printable + ("..." if len(data) > head else "")


def compute_lambda_score(glyph: Glyph) -> float:
    """Heuristic transferability score in [0, 1]; lower means easier for a
    third party to verify/use without extra context (Section 7, Lambda
    Friction). This is a deterministic heuristic over the glyph's own
    declared properties, not a learned model."""
    base_by_level = {
        FidelityLevel.NULL: 1.0,
        FidelityLevel.PRESENCE: 0.9,
        FidelityLevel.TYPE: 0.8,
        FidelityLevel.METADATA: 0.7,
        FidelityLevel.FEATURE: 0.55,
        FidelityLevel.SKETCH: 0.5,
        FidelityLevel.RECEIPT: 0.2,
        FidelityLevel.PARTIAL_BODY: 0.4,
        FidelityLevel.ENCRYPTED_BODY: 0.6,
        FidelityLevel.FULL_TRANSPORT: 0.1,
    }
    score = base_by_level[FidelityLevel(glyph.level)]
    payload_str = str(glyph.payload)
    if os.sep in payload_str and ("/home/" in payload_str or "/Users/" in payload_str):
        score = min(1.0, score + 0.2)
    if glyph.identity and "time_anchor" in glyph.payload:
        score = max(0.0, score - 0.05)
    glyph.lambda_score = round(score, 4)
    return glyph.lambda_score
