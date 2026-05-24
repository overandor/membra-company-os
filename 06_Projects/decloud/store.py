"""Store — Content-addressed flat file storage (IPFS-lite).

Bundles are stored by their SHA-256 hash so identical content deduplicates
automatically.  The store is safe to share across nodes via rsync / IPFS.
"""
import hashlib
import json
import shutil
import tarfile
from pathlib import Path
from typing import List, Optional
import tempfile


class ContentStore:
    """Local content-addressed object store."""

    def __init__(self, base_dir: str = "./decloud_store"):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)
        self.bundles = self.base / "bundles"
        self.bundles.mkdir(exist_ok=True)
        self.meta = self.base / "meta.json"
        self._cache: dict = {}
        if self.meta.exists():
            try:
                self._cache = json.loads(self.meta.read_text())
            except Exception:
                self._cache = {}

    def _save_meta(self):
        self.meta.write_text(json.dumps(self._cache, sort_keys=True, indent=2))

    @staticmethod
    def compute_cid(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def put(self, data: bytes, app_id: Optional[str] = None) -> str:
        """Store raw bytes, return CID."""
        cid = self.compute_cid(data)
        path = self.bundles / cid
        if not path.exists():
            path.write_bytes(data)
        if app_id:
            self._cache.setdefault(app_id, []).append(cid)
            self._save_meta()
        return cid

    def get(self, cid: str) -> Optional[bytes]:
        path = self.bundles / cid
        return path.read_bytes() if path.exists() else None

    def has(self, cid: str) -> bool:
        return (self.bundles / cid).exists()

    def put_bundle(self, source_dir: str, app_id: Optional[str] = None) -> str:
        """Tar + gzip a directory, store it, and return CID."""
        source = Path(source_dir)
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            with tarfile.open(tmp.name, "w:gz") as tf:
                for item in source.rglob("*"):
                    if item.is_file():
                        arcname = item.relative_to(source)
                        tf.add(item, arcname=arcname)
            data = Path(tmp.name).read_bytes()
            Path(tmp.name).unlink()
        return self.put(data, app_id)

    def extract_bundle(self, cid: str, dest_dir: str) -> Path:
        """Extract a bundle CID to a destination directory."""
        data = self.get(cid)
        if data is None:
            raise FileNotFoundError(f"CID {cid} not found in store")
        dest = Path(dest_dir)
        dest.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            tmp.write(data)
            tmp.flush()
            with tarfile.open(tmp.name, "r:gz") as tf:
                tf.extractall(path=dest)
            Path(tmp.name).unlink()
        return dest

    def app_cids(self, app_id: str) -> List[str]:
        return list(self._cache.get(app_id, []))
