"""
IPFS Manager Module - Handles IPFS backup and content-addressed storage
Integrates with IPFS nodes for distributed file storage and retrieval.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import asyncio
import aiohttp
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class IPFSBackupResult:
    """Result of IPFS backup operation"""
    file_path: str
    cid: str
    size: int
    timestamp: str
    gateways: List[str]
    success: bool
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class IPFSRetrievalResult:
    """Result of IPFS retrieval operation"""
    cid: str
    file_path: str
    size: int
    timestamp: str
    success: bool
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class IPFSManager:
    """Manages IPFS operations for file backup and retrieval"""
    
    def __init__(
        self,
        ipfs_node_url: str = "http://127.0.0.1:5001",
        public_gateways: List[str] = None,
        timeout: int = 300
    ):
        self.ipfs_node_url = ipfs_node_url.rstrip('/')
        self.timeout = timeout
        
        # Default public gateways for redundancy
        self.public_gateways = public_gateways or [
            "https://ipfs.io/ipfs/",
            "https://gateway.pinata.cloud/ipfs/",
            "https://cloudflare-ipfs.com/ipfs/",
            "https://dweb.link/ipfs/"
        ]
        
        self.backup_history: Dict[str, IPFSBackupResult] = {}
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def check_node_status(self) -> Dict:
        """Check if IPFS node is running and accessible"""
        try:
            async with self.session.get(f"{self.ipfs_node_url}/api/v0/version") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'status': 'online',
                        'version': data.get('Version', 'unknown'),
                        'commit': data.get('Commit', 'unknown'),
                        'repository': data.get('Repo', 'unknown')
                    }
                else:
                    return {
                        'status': 'error',
                        'error': f'HTTP {response.status}'
                    }
        except Exception as e:
            return {
                'status': 'offline',
                'error': str(e)
            }
    
    async def backup_file(self, file_path: str) -> IPFSBackupResult:
        """Backup a single file to IPFS"""
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            return IPFSBackupResult(
                file_path=file_path,
                cid="",
                size=0,
                timestamp=datetime.now().isoformat(),
                gateways=[],
                success=False,
                error="File not found"
            )
        
        try:
            # Add file to IPFS
            with open(file_path_obj, 'rb') as f:
                files = {'file': f}
                async with self.session.post(f"{self.ipfs_node_url}/api/v0/add", data=files) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return IPFSBackupResult(
                            file_path=file_path,
                            cid="",
                            size=0,
                            timestamp=datetime.now().isoformat(),
                            gateways=[],
                            success=False,
                            error=f"IPFS add failed: {error_text}"
                        )
                    
                    result = await response.json()
                    cid = result.get('Hash', '')
                    size = result.get('Size', 0)
            
            # Generate gateway URLs
            gateways = [f"{gateway}{cid}" for gateway in self.public_gateways]
            
            # Create backup result
            backup_result = IPFSBackupResult(
                file_path=file_path,
                cid=cid,
                size=int(size),
                timestamp=datetime.now().isoformat(),
                gateways=gateways,
                success=True
            )
            
            self.backup_history[file_path] = backup_result
            logger.info(f"Successfully backed up {file_path} to IPFS: {cid}")
            
            return backup_result
            
        except Exception as e:
            logger.error(f"Error backing up {file_path}: {e}")
            return IPFSBackupResult(
                file_path=file_path,
                cid="",
                size=0,
                timestamp=datetime.now().isoformat(),
                gateways=[],
                success=False,
                error=str(e)
            )
    
    async def backup_directory(self, directory_path: str, pattern: str = '*') -> List[IPFSBackupResult]:
        """Backup all files in a directory to IPFS"""
        directory_path_obj = Path(directory_path)
        
        if not directory_path_obj.exists() or not directory_path_obj.is_dir():
            logger.error(f"Directory not found: {directory_path}")
            return []
        
        results = []
        files = list(directory_path_obj.rglob(pattern))
        
        logger.info(f"Starting backup of {len(files)} files from {directory_path}")
        
        # Backup files concurrently
        tasks = [self.backup_file(str(file_path)) for file_path in files if file_path.is_file()]
        results = await asyncio.gather(*tasks)
        
        successful = sum(1 for r in results if r.success)
        logger.info(f"Backup complete: {successful}/{len(results)} files successful")
        
        return results
    
    async def retrieve_file(self, cid: str, output_path: str) -> IPFSRetrievalResult:
        """Retrieve a file from IPFS by CID"""
        try:
            # Try local IPFS node first
            async with self.session.post(f"{self.ipfs_node_url}/api/v0/cat", data={'arg': cid}) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    # Write to output path
                    output_path_obj = Path(output_path)
                    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(output_path_obj, 'wb') as f:
                        f.write(content)
                    
                    return IPFSRetrievalResult(
                        cid=cid,
                        file_path=output_path,
                        size=len(content),
                        timestamp=datetime.now().isoformat(),
                        success=True
                    )
                else:
                    # Try public gateways as fallback
                    for gateway in self.public_gateways:
                        try:
                            gateway_url = f"{gateway}{cid}"
                            async with self.session.get(gateway_url) as gateway_response:
                                if gateway_response.status == 200:
                                    content = await gateway_response.read()
                                    
                                    output_path_obj = Path(output_path)
                                    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
                                    
                                    with open(output_path_obj, 'wb') as f:
                                        f.write(content)
                                    
                                    return IPFSRetrievalResult(
                                        cid=cid,
                                        file_path=output_path,
                                        size=len(content),
                                        timestamp=datetime.now().isoformat(),
                                        success=True
                                    )
                        except Exception:
                            continue
                    
                    return IPFSRetrievalResult(
                        cid=cid,
                        file_path=output_path,
                        size=0,
                        timestamp=datetime.now().isoformat(),
                        success=False,
                        error="Failed to retrieve from IPFS node and all gateways"
                    )
                    
        except Exception as e:
            logger.error(f"Error retrieving CID {cid}: {e}")
            return IPFSRetrievalResult(
                cid=cid,
                file_path=output_path,
                size=0,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=str(e)
            )
    
    async def pin_file(self, cid: str) -> bool:
        """Pin a file to the local IPFS node to prevent garbage collection"""
        try:
            async with self.session.post(f"{self.ipfs_node_url}/api/v0/pin/add", data={'arg': cid}) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Pinned CID {cid}: {result}")
                    return True
                else:
                    logger.error(f"Failed to pin {cid}: HTTP {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error pinning {cid}: {e}")
            return False
    
    async def verify_cid(self, cid: str, expected_hash: str) -> bool:
        """Verify that CID matches expected hash"""
        try:
            # Retrieve file content
            async with self.session.post(f"{self.ipfs_node_url}/api/v0/cat", data={'arg': cid}) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    # Calculate hash
                    file_hash = hashlib.sha256(content).hexdigest()
                    
                    return file_hash == expected_hash
                else:
                    return False
        except Exception as e:
            logger.error(f"Error verifying CID {cid}: {e}")
            return False
    
    async def get_file_info(self, cid: str) -> Dict:
        """Get information about a file by CID"""
        try:
            async with self.session.post(f"{self.ipfs_node_url}/api/v0/ls", data={'arg': cid}) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    return {'error': f'HTTP {response.status}'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_backup_summary(self) -> Dict:
        """Get summary of backup operations"""
        if not self.backup_history:
            return {
                'total_files': 0,
                'successful_backups': 0,
                'failed_backups': 0,
                'total_size_bytes': 0
            }
        
        successful = [r for r in self.backup_history.values() if r.success]
        failed = [r for r in self.backup_history.values() if not r.success]
        total_size = sum(r.size for r in successful)
        
        return {
            'total_files': len(self.backup_history),
            'successful_backups': len(successful),
            'failed_backups': len(failed),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'latest_backup': max((r.timestamp for r in successful), default=None)
        }


class IPFSTokenizationBridge:
    """Bridge between file tokenization and IPFS backup"""
    
    def __init__(self, ipfs_manager: IPFSManager):
        self.ipfs_manager = ipfs_manager
        self.file_cid_map: Dict[str, str] = {}  # file_path -> cid
        self.cid_file_map: Dict[str, str] = {}  # cid -> file_path
    
    async def tokenize_and_backup(self, file_metadata: Dict) -> Dict:
        """Tokenize file metadata and backup to IPFS"""
        file_path = file_metadata.get('path')
        file_hash = file_metadata.get('hash')
        
        if not file_path:
            return {'error': 'No file path in metadata'}
        
        # Backup file to IPFS
        backup_result = await self.ipfs_manager.backup_file(file_path)
        
        if backup_result.success:
            # Update mappings
            self.file_cid_map[file_path] = backup_result.cid
            self.cid_file_map[backup_result.cid] = file_path
            
            # Verify CID matches expected hash
            is_valid = await self.ipfs_manager.verify_cid(backup_result.cid, file_hash)
            
            return {
                'file_path': file_path,
                'file_hash': file_hash,
                'ipfs_cid': backup_result.cid,
                'verified': is_valid,
                'gateways': backup_result.gateways,
                'size': backup_result.size
            }
        else:
            return {
                'file_path': file_path,
                'error': backup_result.error
            }
    
    async def batch_tokenize_and_backup(self, file_metadata_list: List[Dict]) -> List[Dict]:
        """Batch tokenize and backup multiple files"""
        tasks = [self.tokenize_and_backup(metadata) for metadata in file_metadata_list]
        return await asyncio.gather(*tasks)


async def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ipfs_manager.py <file_or_directory_path>")
        sys.exit(1)
    
    target_path = sys.argv[1]
    target_path_obj = Path(target_path)
    
    async with IPFSManager() as ipfs:
        # Check node status
        status = await ipfs.check_node_status()
        print(f"IPFS Node Status: {status}")
        
        if status['status'] != 'online':
            print("IPFS node is not running. Please start it with 'ipfs daemon'")
            sys.exit(1)
        
        if target_path_obj.is_file():
            # Backup single file
            result = await ipfs.backup_file(target_path)
            print(f"\nBackup Result: {result.to_dict()}")
        elif target_path_obj.is_dir():
            # Backup directory
            results = await ipfs.backup_directory(target_path)
            print(f"\nBacked up {len(results)} files")
            
            # Print summary
            summary = ipfs.get_backup_summary()
            print(f"\n=== Backup Summary ===")
            print(f"Total Files: {summary['total_files']}")
            print(f"Successful: {summary['successful_backups']}")
            print(f"Failed: {summary['failed_backups']}")
            print(f"Total Size: {summary['total_size_mb']:.2f} MB")
        else:
            print(f"Path not found: {target_path}")
            sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())