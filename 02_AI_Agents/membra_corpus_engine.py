#!/usr/bin/env python3
"""
MEMBRA CORPUS ENGINE — Knowledge-Backed Liquidity Agent
Scans, hashes, indexes, and appraises the entire machine corpus.
Creates the knowledge seed that backs the Membra token thesis.

Architecture:
  FILES_DISCOVERED → FILES_HASHED → CORPUS_INDEXED
  → SYSTEMS_APPRAISED → KNOWLEDGE_AGENT_LIVE
  → PAID_CHAT_ENABLED → TREASURY_RECEIVES_SOL_OR_USDC
  → MEMBRA_TOKEN_MINTED → LIQUIDITY_POOL_FUNDED → SWAPS_ENABLED
"""

import json, os, sys, hashlib, sqlite3, time, re, textwrap, subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict

# ============================================================
# CONFIGURATION
# ============================================================

SCAN_ROOT = Path("/Users/alep/Downloads")
CORPUS_DIR = Path("/Users/alep/Downloads/membra_corpus")
CORPUS_DIR.mkdir(parents=True, exist_ok=True)

# Subdirectories for corpus artifacts
(CORPUS_DIR / "system_cards").mkdir(exist_ok=True)
(CORPUS_DIR / "proofs").mkdir(exist_ok=True)
(CORPUS_DIR / "public_export").mkdir(exist_ok=True)

# Files/directories to EXCLUDE from scanning
EXCLUDE_PATTERNS = [
    # Secrets & keys
    ".env", ".env.*", "*.pem", "*.key", "*.keystore", "id_rsa*",
    "*.keypair", "secret*", "credential*", "private*",
    # Wallets & state
    "*.json",  # We'll selectively include JSON
    "wallet*", "membra_state.json", "bot_state.json",
    "hedge_state.json", "beast_state.json", "beast_status.json",
    "agent_state.json",
    # Databases
    "*.db", "*.sqlite", "*.sqlite3", "*.duckdb",
    # Binaries & installers
    "*.dmg", "*.exe", "*.zip", "*.tar.gz", "*.gz", "*.bin",
    "*.so", "*.dylib", "*.wasm",
    # Media (large files)
    "*.m4a", "*.mp3", "*.mp4", "*.mov", "*.avi", "*.wav",
    "*.jpg", "*.jpeg", "*.png", "*.gif", "*.svg", "*.ico",
    "*.webp", "*.heic", "*.heif", "*.tiff", "*.bmp",
    # System & cache
    "__pycache__", ".git", ".DS_Store", ".localized",
    "*.pyc", "*.pyo", "*.class",
    # Node
    "node_modules",
    # PDFs (exclude from text indexing but note in manifest)
]

# Directories to exclude entirely
EXCLUDE_DIRS = {
    "__pycache__", ".git", "node_modules", "cache",
    "09_Backup/.git", "membra_human_chain/.git",
    "go",  # Go distribution, not user code
}

# File extensions we CAN index as text
TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".sol", ".rs", ".go",
    ".sh", ".bash", ".zsh", ".fish",
    ".md", ".txt", ".rst", ".log",
    ".html", ".css", ".scss", ".less",
    ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".conf",
    ".env.example", ".env.sample",
    ".sql", ".graphql",
    ".dockerfile", ".dockerignore", ".gitignore",
    ".c", ".cpp", ".h", ".hpp", ".java", ".kt", ".swift",
    ".rb", ".php", ".lua", ".r", ".m", ".mm",
}

# Max file size for text indexing (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024

# ============================================================
# CORPUS SCANNER
# ============================================================

class CorpusScanner:
    """Scans the machine, discovers files, hashes them, builds manifest."""
    
    def __init__(self, root: Path = SCAN_ROOT):
        self.root = root
        self.files: List[Dict] = []
        self.stats = defaultdict(int)
    
    def _should_exclude(self, path: Path) -> bool:
        """Check if a file/directory should be excluded."""
        name = path.name
        
        # Check directory exclusions
        if path.is_dir():
            if name in EXCLUDE_DIRS:
                return True
            # Check relative path against exclude dirs
            try:
                rel = str(path.relative_to(self.root))
                for ed in EXCLUDE_DIRS:
                    if rel.startswith(ed) or ed in rel.split('/'):
                        return True
            except ValueError:
                pass
            return False
        
        # Check file exclusions
        for pattern in EXCLUDE_PATTERNS:
            if pattern.startswith("*."):
                ext = pattern[1:]
                if name.endswith(ext):
                    return True
            elif pattern.endswith("*"):
                prefix = pattern[:-1]
                if name.startswith(prefix):
                    return True
            elif pattern == name:
                return True
        
        # Exclude hidden files (but not .env.example etc)
        if name.startswith(".") and name not in (".env.example", ".env.sample", ".gitignore", ".dockerignore"):
            return True
        
        # Exclude large files
        try:
            if path.stat().st_size > MAX_FILE_SIZE:
                return True
        except OSError:
            return True
        
        return False
    
    def _categorize(self, path: Path) -> str:
        """Categorize a file by its extension and location."""
        suffix = path.suffix.lower()
        try:
            rel = str(path.relative_to(self.root))
        except ValueError:
            rel = str(path)
        
        parts = rel.split('/')
        top_dir = parts[0] if parts else ""
        
        # Category by top-level directory
        if top_dir.startswith("01_Trading") or top_dir.startswith("trading"):
            return "trading_systems"
        if top_dir.startswith("02_AI") or top_dir.startswith("ai"):
            return "ai_agents"
        if top_dir.startswith("03_Doc") or top_dir.startswith("doc"):
            return "documentation"
        if top_dir.startswith("04_Soft") or top_dir.startswith("install"):
            return "installers"
        if top_dir.startswith("05_Config") or top_dir.startswith("config"):
            return "configuration"
        if top_dir.startswith("06_Proj") or top_dir.startswith("project"):
            return "projects"
        if top_dir.startswith("07_Scr") or top_dir.startswith("script"):
            return "scripts"
        if top_dir.startswith("08_Data") or top_dir.startswith("data"):
            return "data_files"
        if top_dir.startswith("09_Back") or top_dir.startswith("backup"):
            return "backup"
        if top_dir.startswith("membra"):
            return "membra_core"
        if top_dir.startswith("token"):
            return "tokenization"
        
        # Category by extension
        if suffix in (".py", ".pyw"):
            return "python"
        if suffix in (".js", ".jsx", ".ts", ".tsx"):
            return "javascript"
        if suffix in (".sol",):
            return "solidity"
        if suffix in (".rs",):
            return "rust"
        if suffix in (".sh", ".bash", ".zsh"):
            return "shell"
        if suffix in (".md", ".rst", ".txt"):
            return "text"
        if suffix in (".html", ".css", ".scss"):
            return "web"
        if suffix in (".json", ".yaml", ".yml", ".toml"):
            return "config"
        
        return "other"
    
    def _complexity_score(self, path: Path, content: str) -> str:
        """Estimate file complexity: advanced, complex, moderate, simple."""
        lines = content.count('\n')
        suffix = path.suffix.lower()
        
        # Heuristic based on lines and file type
        if suffix in (".py", ".js", ".ts", ".tsx", ".sol", ".rs", ".go"):
            if lines > 500: return "advanced"
            if lines > 150: return "complex"
            if lines > 50: return "moderate"
            return "simple"
        elif suffix in (".sh", ".bash"):
            if lines > 200: return "complex"
            if lines > 50: return "moderate"
            return "simple"
        elif suffix in (".md", ".txt", ".rst"):
            if lines > 300: return "complex"
            if lines > 100: return "moderate"
            return "simple"
        
        return "simple"
    
    def scan(self) -> List[Dict]:
        """Scan the root directory and discover all files."""
        print(f"🔍 Scanning: {self.root}")
        self.files = []
        self.stats = defaultdict(int)
        
        for entry in self.root.rglob("*"):
            if self._should_exclude(entry):
                continue
            
            if entry.is_file():
                try:
                    stat = entry.stat()
                    rel_path = str(entry.relative_to(self.root))
                    category = self._categorize(entry)
                    
                    file_info = {
                        "path": str(entry),
                        "relative_path": rel_path,
                        "name": entry.name,
                        "suffix": entry.suffix.lower(),
                        "size_bytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                        "category": category,
                        "is_text": entry.suffix.lower() in TEXT_EXTENSIONS,
                    }
                    self.files.append(file_info)
                    self.stats[category] += 1
                except OSError:
                    continue
        
        self.files.sort(key=lambda f: f["relative_path"])
        print(f"   Found {len(self.files):,} files across {len(self.stats)} categories")
        return self.files
    
    def hash_files(self) -> Dict[str, str]:
        """SHA-256 hash every discovered file."""
        print(f"🔐 Hashing {len(self.files):,} files...")
        hashes = {}
        count = 0
        
        for f in self.files:
            try:
                with open(f["path"], "rb") as fh:
                    content = fh.read()
                file_hash = hashlib.sha256(content).hexdigest()
                hashes[f["relative_path"]] = file_hash
                f["sha256"] = file_hash
                count += 1
                if count % 500 == 0:
                    print(f"   {count:,}/{len(self.files):,}...")
            except (OSError, PermissionError):
                f["sha256"] = "ERROR"
                hashes[f["relative_path"]] = "ERROR"
        
        print(f"   Hashed {count:,} files")
        return hashes
    
    def compute_merkle_root(self, hashes: Dict[str, str]) -> str:
        """Compute a Merkle root from all file hashes."""
        sorted_hashes = sorted(h for h in hashes.values() if h != "ERROR")
        if not sorted_hashes:
            return "0" * 64
        
        # Build Merkle tree
        current = [bytes.fromhex(h) for h in sorted_hashes]
        while len(current) > 1:
            next_level = []
            for i in range(0, len(current), 2):
                left = current[i]
                right = current[i + 1] if i + 1 < len(current) else left
                combined = hashlib.sha256(left + right).digest()
                next_level.append(combined)
            current = next_level
        
        return current[0].hex()

# ============================================================
# CORPUS INDEXER (RAG Layer)
# ============================================================

class CorpusIndexer:
    """Indexes text files into chunks, stores in SQLite, creates embeddings."""
    
    CHUNK_SIZE = 1000  # characters per chunk
    CHUNK_OVERLAP = 200
    
    def __init__(self, db_path: Path = CORPUS_DIR / "chunks.sqlite"):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self._create_tables()
        self.embedder = self._init_embedder()
    
    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                relative_path TEXT UNIQUE NOT NULL,
                sha256 TEXT,
                category TEXT,
                complexity TEXT,
                line_count INTEGER,
                char_count INTEGER,
                indexed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                char_start INTEGER,
                char_end INTEGER,
                FOREIGN KEY (file_id) REFERENCES files(id),
                UNIQUE(file_id, chunk_index)
            );
            CREATE TABLE IF NOT EXISTS embeddings (
                chunk_id INTEGER PRIMARY KEY,
                embedding BLOB,
                model TEXT,
                FOREIGN KEY (chunk_id) REFERENCES chunks(id)
            );
            CREATE INDEX IF NOT EXISTS idx_files_category ON files(category);
            CREATE INDEX IF NOT EXISTS idx_files_complexity ON files(complexity);
            CREATE INDEX IF NOT EXISTS idx_chunks_file ON chunks(file_id);
        """)
        self.conn.commit()
    
    def _init_embedder(self):
        """Initialize embedding model. Falls back to None if unavailable."""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            print("   ✅ Embedding model: all-MiniLM-L6-v2 (384-dim)")
            return model
        except ImportError:
            print("   ⚠️  sentence-transformers not installed. Embeddings disabled.")
            print("   Install: pip install sentence-transformers")
            return None
        except Exception as e:
            print(f"   ⚠️  Embedding model error: {e}")
            return None
    
    def _chunk_text(self, text: str) -> List[Tuple[int, int, str]]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        idx = 0
        while start < len(text):
            end = min(start + self.CHUNK_SIZE, len(text))
            chunk = text[start:end]
            chunks.append((start, end, chunk))
            start += self.CHUNK_SIZE - self.CHUNK_OVERLAP
            idx += 1
        return chunks
    
    def index_file(self, file_info: Dict) -> int:
        """Index a single file: store metadata, chunk it, create embeddings."""
        path = Path(file_info["path"])
        
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            return -1
        
        line_count = content.count('\n')
        char_count = len(content)
        complexity = self._estimate_complexity(file_info, line_count)
        
        # Insert file record
        self.conn.execute("""
            INSERT OR REPLACE INTO files (relative_path, sha256, category, complexity, line_count, char_count, indexed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            file_info["relative_path"],
            file_info.get("sha256", ""),
            file_info.get("category", "unknown"),
            complexity,
            line_count,
            char_count,
            datetime.now(timezone.utc).isoformat()
        ))
        
        file_id = self.conn.execute(
            "SELECT id FROM files WHERE relative_path = ?",
            (file_info["relative_path"],)
        ).fetchone()[0]
        
        # Delete old chunks
        self.conn.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
        self.conn.execute("DELETE FROM embeddings WHERE chunk_id IN (SELECT id FROM chunks WHERE file_id = ?)", (file_id,))
        
        # Chunk and store
        chunks = self._chunk_text(content)
        for idx, (cstart, cend, chunk_text) in enumerate(chunks):
            self.conn.execute("""
                INSERT OR REPLACE INTO chunks (file_id, chunk_index, content, char_start, char_end)
                VALUES (?, ?, ?, ?, ?)
            """, (file_id, idx, chunk_text, cstart, cend))
        
        # Create embeddings if model available
        if self.embedder and chunks:
            chunk_texts = [c[2] for c in chunks]
            try:
                embeddings = self.embedder.encode(chunk_texts, show_progress_bar=False)
                for idx, emb in enumerate(embeddings):
                    chunk_id = self.conn.execute(
                        "SELECT id FROM chunks WHERE file_id = ? AND chunk_index = ?",
                        (file_id, idx)
                    ).fetchone()[0]
                    self.conn.execute(
                        "INSERT OR REPLACE INTO embeddings (chunk_id, embedding, model) VALUES (?, ?, ?)",
                        (chunk_id, emb.tobytes(), "all-MiniLM-L6-v2")
                    )
            except Exception as e:
                pass  # Embedding failed, continue without
        
        self.conn.commit()
        return file_id
    
    def _estimate_complexity(self, file_info: Dict, line_count: int) -> str:
        suffix = file_info.get("suffix", "")
        if suffix in (".py", ".js", ".ts", ".tsx", ".sol", ".rs", ".go"):
            if line_count > 500: return "advanced"
            if line_count > 150: return "complex"
            if line_count > 50: return "moderate"
            return "simple"
        if line_count > 300: return "complex"
        if line_count > 100: return "moderate"
        return "simple"
    
    def index_all(self, files: List[Dict], limit: int = None) -> Dict:
        """Index all text files."""
        text_files = [f for f in files if f.get("is_text")]
        if limit:
            text_files = text_files[:limit]
        
        print(f"📝 Indexing {len(text_files):,} text files...")
        indexed = 0
        errors = 0
        
        for i, f in enumerate(text_files):
            try:
                file_id = self.index_file(f)
                if file_id > 0:
                    indexed += 1
                else:
                    errors += 1
            except Exception:
                errors += 1
            
            if (i + 1) % 200 == 0:
                print(f"   {i+1:,}/{len(text_files):,}...")
        
        print(f"   Indexed: {indexed:,} files, {errors} errors")
        return {"indexed": indexed, "errors": errors, "total_text_files": len(text_files)}
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """Semantic search over the corpus using embeddings."""
        if not self.embedder:
            # Fallback: keyword search
            return self._keyword_search(query, top_k)
        
        # Encode query
        query_emb = self.embedder.encode([query], show_progress_bar=False)[0]
        
        # Get all embeddings (for small corpora) or use approximate search
        rows = self.conn.execute("""
            SELECT c.id, c.content, c.file_id, f.relative_path, f.category, e.embedding
            FROM embeddings e
            JOIN chunks c ON e.chunk_id = c.id
            JOIN files f ON c.file_id = f.id
        """).fetchall()
        
        if not rows:
            return self._keyword_search(query, top_k)
        
        # Compute cosine similarity
        import numpy as np
        query_vec = query_emb / np.linalg.norm(query_emb)
        
        results = []
        for row in rows:
            chunk_id, content, file_id, rel_path, category, emb_blob = row
            emb = np.frombuffer(emb_blob, dtype=np.float32)
            emb = emb / np.linalg.norm(emb)
            similarity = float(np.dot(query_vec, emb))
            results.append({
                "chunk_id": chunk_id,
                "content": content[:500],
                "file": rel_path,
                "category": category,
                "similarity": round(similarity, 4)
            })
        
        results.sort(key=lambda r: r["similarity"], reverse=True)
        return results[:top_k]
    
    def _keyword_search(self, query: str, top_k: int = 10) -> List[Dict]:
        """Fallback keyword search using SQLite FTS-like matching."""
        terms = query.lower().split()
        results = []
        
        for term in terms:
            rows = self.conn.execute("""
                SELECT c.id, c.content, f.relative_path, f.category
                FROM chunks c
                JOIN files f ON c.file_id = f.id
                WHERE LOWER(c.content) LIKE ?
                LIMIT ?
            """, (f"%{term}%", top_k)).fetchall()
            
            for row in rows:
                chunk_id, content, rel_path, category = row
                # Count occurrences for relevance
                count = content.lower().count(term)
                results.append({
                    "chunk_id": chunk_id,
                    "content": content[:500],
                    "file": rel_path,
                    "category": category,
                    "similarity": count / max(len(content), 1)
                })
        
        # Deduplicate and sort
        seen = set()
        unique = []
        for r in sorted(results, key=lambda r: r["similarity"], reverse=True):
            if r["chunk_id"] not in seen:
                seen.add(r["chunk_id"])
                unique.append(r)
        
        return unique[:top_k]
    
    def get_stats(self) -> Dict:
        """Get indexing statistics."""
        files = self.conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        chunks = self.conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        embeddings = self.conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
        categories = self.conn.execute(
            "SELECT category, COUNT(*) as cnt FROM files GROUP BY category ORDER BY cnt DESC"
        ).fetchall()
        
        return {
            "files_indexed": files,
            "chunks": chunks,
            "embeddings": embeddings,
            "categories": [{"name": c[0], "count": c[1]} for c in categories]
        }
    
    def close(self):
        self.conn.close()

# ============================================================
# CORPUS MANIFEST BUILDER
# ============================================================

class ManifestBuilder:
    """Builds the corpus manifest, proof files, and system cards."""
    
    def __init__(self, scanner: CorpusScanner, indexer: CorpusIndexer):
        self.scanner = scanner
        self.indexer = indexer
    
    def build_manifest(self, hashes: Dict[str, str], merkle_root: str) -> Dict:
        """Build the full corpus manifest."""
        stats = self.indexer.get_stats()
        
        # Category breakdown
        categories = defaultdict(lambda: {"files": 0, "size_bytes": 0, "complexities": defaultdict(int)})
        for f in self.scanner.files:
            cat = f.get("category", "unknown")
            categories[cat]["files"] += 1
            categories[cat]["size_bytes"] += f.get("size_bytes", 0)
        
        manifest = {
            "membra_version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scan_root": str(self.scanner.root),
            "merkle_root": merkle_root,
            "totals": {
                "files_discovered": len(self.scanner.files),
                "files_hashed": len([h for h in hashes.values() if h != "ERROR"]),
                "files_indexed": stats["files_indexed"],
                "chunks": stats["chunks"],
                "embeddings": stats["embeddings"],
                "total_size_bytes": sum(f.get("size_bytes", 0) for f in self.scanner.files),
                "categories": len(categories),
            },
            "categories": {
                cat: {
                    "files": data["files"],
                    "size_bytes": data["size_bytes"],
                    "size_mb": round(data["size_bytes"] / (1024 * 1024), 2)
                }
                for cat, data in sorted(categories.items())
            },
            "indexing_stats": stats,
            "excluded_patterns": EXCLUDE_PATTERNS,
            "excluded_dirs": list(EXCLUDE_DIRS),
        }
        
        path = CORPUS_DIR / "manifest.json"
        path.write_text(json.dumps(manifest, indent=2))
        print(f"📋 Manifest: {path} ({path.stat().st_size:,} bytes)")
        return manifest
    
    def build_file_hashes(self, hashes: Dict[str, str]):
        """Save file hashes registry."""
        path = CORPUS_DIR / "file_hashes.json"
        path.write_text(json.dumps({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "merkle_root": self.scanner.compute_merkle_root(hashes),
            "files": hashes
        }, indent=2))
        print(f"🔐 File hashes: {path} ({path.stat().st_size:,} bytes)")
    
    def build_system_cards(self):
        """Generate system cards for top-level directories."""
        # Group files by top-level directory
        systems = defaultdict(list)
        for f in self.scanner.files:
            parts = f["relative_path"].split('/')
            top = parts[0] if parts else "root"
            systems[top].append(f)
        
        for sys_name, files in sorted(systems.items()):
            card = {
                "system": sys_name,
                "files": len(files),
                "size_bytes": sum(f.get("size_bytes", 0) for f in files),
                "categories": list(set(f.get("category", "unknown") for f in files)),
                "extensions": list(set(f.get("suffix", "") for f in files)),
                "sample_files": [f["relative_path"] for f in files[:10]],
            }
            
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', sys_name)
            path = CORPUS_DIR / "system_cards" / f"{safe_name}.json"
            path.write_text(json.dumps(card, indent=2))
        
        print(f"🃏 System cards: {len(systems)} systems")
    
    def build_proof(self, hashes: Dict[str, str], merkle_root: str):
        """Build proof-of-corpus file."""
        proof = {
            "proof_type": "MEMBRA_CORPUS_PROOF_V1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "merkle_root": merkle_root,
            "file_count": len(hashes),
            "verification": "All files SHA-256 hashed. Merkle root commits to entire corpus state.",
            "instructions": "Verify: python3 -c 'import json,hashlib; ...' and compare merkle_root"
        }
        
        path = CORPUS_DIR / "proofs" / "corpus_proof.json"
        path.write_text(json.dumps(proof, indent=2))
        print(f"✅ Proof: {path}")
    
    def build_public_export(self, manifest: Dict):
        """Build a public-safe export (no paths, no hashes, just stats)."""
        export = {
            "app": "MEMBRA",
            "version": manifest["membra_version"],
            "generated_at": manifest["generated_at"],
            "totals": manifest["totals"],
            "categories": manifest["categories"],
            "indexing_stats": manifest["indexing_stats"],
            "note": "Public export — no file paths or hashes included. Full proof available on request."
        }
        
        path = CORPUS_DIR / "public_export" / "corpus_public.json"
        path.write_text(json.dumps(export, indent=2))
        print(f"🌐 Public export: {path}")

# ============================================================
# CORPUS QUERY ENGINE
# ============================================================

class CorpusQueryEngine:
    """High-level query interface for the corpus."""
    
    def __init__(self, indexer: CorpusIndexer):
        self.indexer = indexer
    
    def ask(self, question: str, top_k: int = 5) -> str:
        """Ask a question, get answer from corpus."""
        results = self.indexer.search(question, top_k)
        
        if not results:
            return "No relevant content found in the corpus."
        
        lines = [f"📚 CORPUS RESULTS for: \"{question}\"\n"]
        for i, r in enumerate(results):
            lines.append(f"\n{i+1}. [{r['category']}] {r['file']}")
            lines.append(f"   Similarity: {r['similarity']}")
            lines.append(f"   {r['content'][:300]}...")
        
        return "\n".join(lines)
    
    def most_valuable_systems(self, top_k: int = 10) -> str:
        """Find the most valuable systems by complexity and size."""
        rows = self.indexer.conn.execute("""
            SELECT relative_path, category, complexity, line_count, char_count
            FROM files
            WHERE complexity IN ('advanced', 'complex')
            ORDER BY line_count DESC
            LIMIT ?
        """, (top_k,)).fetchall()
        
        if not rows:
            return "No indexed systems found."
        
        lines = [f"🏆 TOP {len(rows)} MOST VALUABLE SYSTEMS:\n"]
        for i, row in enumerate(rows):
            path, cat, comp, lines_count, chars = row
            lines.append(f"{i+1}. [{comp.upper()}] {path}")
            lines.append(f"   Category: {cat} | Lines: {lines_count:,} | Chars: {chars:,}")
        
        return "\n".join(lines)

# ============================================================
# MAIN PIPELINE
# ============================================================

def run_full_pipeline(limit_files: int = None):
    """Run the complete corpus pipeline."""
    print("""
╔══════════════════════════════════════════════════════════╗
║  MEMBRA CORPUS ENGINE — Knowledge-Backed Liquidity       ║
║  Files → Hashes → Index → Proof → Agent → Revenue        ║
╚══════════════════════════════════════════════════════════╝
""")
    
    t0 = time.time()
    
    # 1. Scan
    scanner = CorpusScanner()
    files = scanner.scan()
    
    # 2. Hash
    hashes = scanner.hash_files()
    merkle_root = scanner.compute_merkle_root(hashes)
    print(f"🌳 Merkle root: {merkle_root[:16]}...")
    
    # 3. Index
    indexer = CorpusIndexer()
    indexer.index_all(files, limit=limit_files)
    
    # 4. Build manifest & proofs
    builder = ManifestBuilder(scanner, indexer)
    manifest = builder.build_manifest(hashes, merkle_root)
    builder.build_file_hashes(hashes)
    builder.build_system_cards()
    builder.build_proof(hashes, merkle_root)
    builder.build_public_export(manifest)
    
    # 5. Query engine
    query = CorpusQueryEngine(indexer)
    
    elapsed = time.time() - t0
    print(f"\n✅ Pipeline complete in {elapsed:.1f}s")
    print(f"   Corpus: {CORPUS_DIR}")
    print(f"   Manifest: {CORPUS_DIR / 'manifest.json'}")
    print(f"   Chunks DB: {CORPUS_DIR / 'chunks.sqlite'}")
    
    indexer.close()
    return scanner, indexer, query

# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Membra Corpus Engine")
    parser.add_argument("action", nargs="?", default="pipeline",
                        choices=["pipeline", "scan", "hash", "index", "ask", "stats", "valuable"])
    parser.add_argument("--query", "-q", type=str, help="Query for 'ask' action")
    parser.add_argument("--limit", "-l", type=int, help="Limit files for indexing")
    args = parser.parse_args()
    
    if args.action == "pipeline":
        run_full_pipeline(limit_files=args.limit)
    
    elif args.action == "scan":
        scanner = CorpusScanner()
        scanner.scan()
        print(f"\nCategories: {dict(scanner.stats)}")
    
    elif args.action == "stats":
        indexer = CorpusIndexer()
        stats = indexer.get_stats()
        print(json.dumps(stats, indent=2))
        indexer.close()
    
    elif args.action == "ask":
        if not args.query:
            print("Usage: corpus ask --query 'your question'")
            sys.exit(1)
        indexer = CorpusIndexer()
        query = CorpusQueryEngine(indexer)
        print(query.ask(args.query))
        indexer.close()
    
    elif args.action == "valuable":
        indexer = CorpusIndexer()
        query = CorpusQueryEngine(indexer)
        print(query.most_valuable_systems())
        indexer.close()
    
    elif args.action == "index":
        scanner = CorpusScanner()
        scanner.scan()
        scanner.hash_files()
        indexer = CorpusIndexer()
        indexer.index_all(scanner.files, limit=args.limit)
        indexer.close()
