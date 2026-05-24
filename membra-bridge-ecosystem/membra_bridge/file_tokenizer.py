"""
Hierarchical Merkle Root Taxonomy - File Tokenization Module
Scans file systems, generates cryptographic hashes, and creates hierarchical merkle trees.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FileMetadata:
    """Metadata for a tokenized file"""
    path: str
    size: int
    hash: str
    modified: str
    merkle_proof: List[str]
    token_id: Optional[str] = None
    ipfs_cid: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class MerkleNode:
    """Node in the merkle tree"""
    hash: str
    left: Optional['MerkleNode'] = None
    right: Optional['MerkleNode'] = None
    is_leaf: bool = False
    file_path: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'hash': self.hash,
            'left': self.left.hash if self.left else None,
            'right': self.right.hash if self.right else None,
            'is_leaf': self.is_leaf,
            'file_path': self.file_path
        }


class HierarchicalMerkleTree:
    """Hierarchical merkle tree for file system tokenization"""
    
    def __init__(self, hash_algorithm: str = 'sha256'):
        self.hash_algorithm = hash_algorithm
        self.root: Optional[MerkleNode] = None
        self.leaves: List[MerkleNode] = []
        self.proofs: Dict[str, List[str]] = {}
        
    def _hash(self, data: str) -> str:
        """Hash data using specified algorithm"""
        if self.hash_algorithm == 'sha256':
            return hashlib.sha256(data.encode()).hexdigest()
        elif self.hash_algorithm == 'md5':
            return hashlib.md5(data.encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {self.hash_algorithm}")
    
    def _hash_pair(self, left: str, right: str) -> str:
        """Hash a pair of hashes"""
        return self._hash(left + right)
    
    def build_tree(self, file_hashes: List[Tuple[str, str]]) -> MerkleNode:
        """Build merkle tree from file hashes (path, hash) tuples"""
        self.leaves = []
        
        # Create leaf nodes
        for file_path, file_hash in file_hashes:
            node = MerkleNode(
                hash=file_hash,
                is_leaf=True,
                file_path=file_path
            )
            self.leaves.append(node)
        
        # Build tree bottom-up
        level = self.leaves[:]
        while len(level) > 1:
            next_level = []
            
            # Process pairs
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else left
                
                parent_hash = self._hash_pair(left.hash, right.hash)
                parent = MerkleNode(
                    hash=parent_hash,
                    left=left,
                    right=right,
                    is_leaf=False
                )
                next_level.append(parent)
            
            level = next_level
        
        self.root = level[0] if level else None
        return self.root
    
    def generate_proof(self, file_path: str) -> List[str]:
        """Generate merkle proof for a specific file"""
        if not self.root:
            return []
        
        # Find the leaf node
        leaf = None
        for node in self.leaves:
            if node.file_path == file_path:
                leaf = node
                break
        
        if not leaf:
            return []
        
        # Generate proof by walking up the tree
        proof = []
        current = leaf
        while current != self.root:
            parent = self._find_parent(current)
            if not parent:
                break
            
            # Add sibling hash
            if parent.left == current:
                proof.append(parent.right.hash if parent.right else parent.left.hash)
            else:
                proof.append(parent.left.hash)
            
            current = parent
        
        self.proofs[file_path] = proof
        return proof
    
    def _find_parent(self, node: MerkleNode) -> Optional[MerkleNode]:
        """Find parent of a node using BFS"""
        if not self.root:
            return None
        
        from collections import deque
        queue = deque([self.root])
        
        while queue:
            current = queue.popleft()
            if current.left == node or current.right == node:
                return current
            if current.left:
                queue.append(current.left)
            if current.right:
                queue.append(current.right)
        
        return None
    
    def verify_proof(self, file_hash: str, proof: List[str], root_hash: str) -> bool:
        """Verify merkle proof"""
        current = file_hash
        
        for sibling_hash in proof:
            current = self._hash_pair(current, sibling_hash)
        
        return current == root_hash
    
    def get_root_hash(self) -> Optional[str]:
        """Get root hash of the tree"""
        return self.root.hash if self.root else None


class FileTokenizer:
    """Main file tokenization engine"""
    
    def __init__(self, root_path: str, hash_algorithm: str = 'sha256'):
        self.root_path = Path(root_path)
        self.hash_algorithm = hash_algorithm
        self.merkle_tree = HierarchicalMerkleTree(hash_algorithm)
        self.file_metadata: Dict[str, FileMetadata] = {}
        self.directory_trees: Dict[str, HierarchicalMerkleTree] = {}
        
    def _hash_file(self, file_path: Path) -> str:
        """Hash a single file"""
        hasher = hashlib.new(self.hash_algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def scan_directory(self, directory: Path, pattern: str = '*') -> List[Path]:
        """Scan directory for files matching pattern"""
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return []
        
        files = []
        for file_path in directory.rglob(pattern):
            if file_path.is_file():
                files.append(file_path)
        
        return files
    
    def tokenize_file(self, file_path: Path) -> FileMetadata:
        """Tokenize a single file"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_hash = self._hash_file(file_path)
        stat = file_path.stat()
        
        metadata = FileMetadata(
            path=str(file_path.relative_to(self.root_path)),
            size=stat.st_size,
            hash=file_hash,
            modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            merkle_proof=[]
        )
        
        self.file_metadata[str(file_path)] = metadata
        return metadata
    
    def build_hierarchical_tree(self) -> Tuple[str, Dict[str, HierarchicalMerkleTree]]:
        """Build hierarchical merkle trees for directory structure"""
        # First, build tree for each directory
        directory_hashes = {}
        
        for directory in self.root_path.rglob('*'):
            if directory.is_dir():
                files = self.scan_directory(directory)
                if not files:
                    continue
                
                file_hashes = []
                for file_path in files:
                    try:
                        metadata = self.tokenize_file(file_path)
                        file_hashes.append((str(file_path), metadata.hash))
                    except Exception as e:
                        logger.error(f"Error tokenizing {file_path}: {e}")
                
                if file_hashes:
                    tree = HierarchicalMerkleTree(self.hash_algorithm)
                    tree.build_tree(file_hashes)
                    self.directory_trees[str(directory)] = tree
                    directory_hashes[str(directory)] = tree.get_root_hash()
        
        # Build root tree from directory hashes
        root_file_hashes = [(path, hash_val) for path, hash_val in directory_hashes.items()]
        self.merkle_tree.build_tree(root_file_hashes)
        
        return self.merkle_tree.get_root_hash(), self.directory_trees
    
    def scan_and_tokenize(self) -> Dict:
        """Main method to scan and tokenize entire file system"""
        logger.info(f"Starting tokenization of {self.root_path}")
        
        start_time = datetime.now()
        
        # Build hierarchical trees
        root_hash, directory_trees = self.build_hierarchical_tree()
        
        # Generate proofs for all files
        for file_path, metadata in self.file_metadata.items():
            # Find which directory tree this file belongs to
            for dir_path, tree in directory_trees.items():
                if file_path.startswith(dir_path):
                    metadata.merkle_proof = tree.generate_proof(file_path)
                    break
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result = {
            'root_hash': root_hash,
            'total_files': len(self.file_metadata),
            'total_directories': len(directory_trees),
            'duration_seconds': duration,
            'timestamp': datetime.now().isoformat(),
            'files': {path: metadata.to_dict() for path, metadata in self.file_metadata.items()},
            'directory_roots': {path: tree.get_root_hash() for path, tree in directory_trees.items()}
        }
        
        logger.info(f"Tokenization complete: {len(self.file_metadata)} files in {duration:.2f}s")
        return result
    
    async def scan_and_tokenize_async(self, max_workers: int = 4) -> Dict:
        """Async version of scan_and_tokenize for better performance"""
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Run scanning in thread pool
            result = await loop.run_in_executor(executor, self.scan_and_tokenize)
        
        return result
    
    def get_tokenization_report(self) -> Dict:
        """Generate a summary report of tokenization"""
        if not self.file_metadata:
            return {'error': 'No files tokenized yet'}
        
        total_size = sum(metadata.size for metadata in self.file_metadata.values())
        
        return {
            'root_path': str(self.root_path),
            'total_files': len(self.file_metadata),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'root_hash': self.merkle_tree.get_root_hash(),
            'hash_algorithm': self.hash_algorithm,
            'directory_count': len(self.directory_trees)
        }


def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python file_tokenizer.py <directory_path>")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    tokenizer = FileTokenizer(directory_path)
    
    # Scan and tokenize
    result = tokenizer.scan_and_tokenize()
    
    # Print summary
    print(f"\n=== Tokenization Summary ===")
    print(f"Root Hash: {result['root_hash']}")
    print(f"Total Files: {result['total_files']}")
    print(f"Total Directories: {result['total_directories']}")
    print(f"Duration: {result['duration_seconds']:.2f}s")
    
    # Save result to JSON
    output_file = Path(directory_path) / 'tokenization_result.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResult saved to {output_file}")


if __name__ == '__main__':
    main()