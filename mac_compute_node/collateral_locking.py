"""
Compute Resource Collateral Locking System
Locks RAM, CPU, and GPU resources as collateral for token minting on MEMBRA network
"""
import asyncio
import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import hashlib
import psutil

from marketplace.compute_market import ComputeMarket, ComputeOffer


@dataclass
class ResourceLock:
    """Represents locked compute resources as collateral"""
    lock_id: str
    node_id: str
    cpu_cores_locked: int
    memory_gb_locked: float
    gpu_locked: bool
    collateral_value: float  # in token units
    lock_start_time: float
    lock_duration_sec: int
    lock_purpose: str  # "token_mint", "zk_compute", "network_task"
    associated_tx: Optional[str] = None
    unlock_signature: Optional[str] = None
    status: str = "locked"  # "locked", "unlocked", "expired"


class ResourceLocker:
    """Manages locking and unlocking of compute resources as collateral"""
    
    def __init__(self, node_id: str, compute_market: ComputeMarket):
        self.node_id = node_id
        self.compute_market = compute_market
        self.locked_resources: Dict[str, ResourceLock] = {}
        self.lock_history: List[Dict] = []
        self.state_file = os.path.expanduser("~/.mac_compute_node/collateral_state.json")
        self._load_state()
        
        # Resource limits (prevent locking all resources)
        self.max_cpu_lock_ratio = 0.8  # Can lock max 80% of CPU
        self.max_memory_lock_ratio = 0.8  # Can lock max 80% of RAM
        
    def _load_state(self):
        """Load lock state from disk"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file) as f:
                    state = json.load(f)
                    self.lock_history = state.get("lock_history", [])
                    # Restore active locks
                    for lock_data in state.get("active_locks", []):
                        lock = ResourceLock(**lock_data)
                        # Check if lock has expired
                        if lock.lock_start_time + lock.lock_duration_sec > time.time():
                            self.locked_resources[lock.lock_id] = lock
                        else:
                            lock.status = "expired"
                            self.lock_history.append(asdict(lock))
            except Exception as e:
                print(f"Error loading collateral state: {e}")
    
    def _save_state(self):
        """Save lock state to disk"""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        state = {
            "active_locks": [asdict(lock) for lock in self.locked_resources.values()],
            "lock_history": self.lock_history[-100:]  # Keep last 100 history entries
        }
        with open(self.state_file, "w") as f:
            json.dump(state, f)
    
    def get_available_resources(self) -> Dict:
        """Get currently available resources for locking"""
        total_cpu = psutil.cpu_count()
        total_memory_gb = psutil.virtual_memory().total / (1024**3)
        gpu_available = self._check_gpu_available()
        
        # Calculate locked resources
        locked_cpu = sum(lock.cpu_cores_locked for lock in self.locked_resources.values())
        locked_memory_gb = sum(lock.memory_gb_locked for lock in self.locked_resources.values())
        locked_gpu = any(lock.gpu_locked for lock in self.locked_resources.values())
        
        return {
            "total_cpu_cores": total_cpu,
            "available_cpu_cores": max(0, total_cpu - locked_cpu),
            "total_memory_gb": total_memory_gb,
            "available_memory_gb": max(0, total_memory_gb - locked_memory_gb),
            "gpu_available": gpu_available and not locked_gpu,
            "locked_cpu_cores": locked_cpu,
            "locked_memory_gb": locked_memory_gb,
            "locked_gpu": locked_gpu
        }
    
    def _check_gpu_available(self) -> bool:
        """Check if GPU is available"""
        try:
            # Try to detect GPU (simplified - in production use proper GPU detection)
            import subprocess
            result = subprocess.run(['sysctl', 'machdep.cpu.brand_string'], 
                                  capture_output=True, text=True)
            return 'apple' in result.stdout.lower() and 'm' in result.stdout.lower()
        except Exception:
            return False
    
    def calculate_collateral_value(
        self,
        cpu_cores: int,
        memory_gb: float,
        gpu: bool,
        lock_duration_sec: int
    ) -> float:
        """Calculate collateral value based on locked resources and duration"""
        # Get current market pricing
        pricing = self.compute_market.pricing
        
        # Calculate hourly value
        cpu_value = cpu_cores * pricing.get("cpu_per_core", 0.05)
        memory_value = memory_gb * pricing.get("memory_per_gb", 0.02)
        gpu_value = 2.0 if gpu else 0.0
        
        hourly_value = cpu_value + memory_value + gpu_value
        
        # Calculate total value for lock duration
        duration_hours = lock_duration_sec / 3600
        total_value = hourly_value * duration_hours
        
        return round(total_value, 6)
    
    def lock_resources(
        self,
        cpu_cores: int,
        memory_gb: float,
        gpu: bool,
        lock_duration_sec: int,
        purpose: str = "token_mint",
        associated_tx: str = None
    ) -> Tuple[bool, str]:
        """
        Lock compute resources as collateral
        
        Returns:
            Tuple[success, lock_id or error_message]
        """
        available = self.get_available_resources()
        
        # Validate resource availability
        if cpu_cores > available["available_cpu_cores"]:
            return False, f"Insufficient CPU cores. Available: {available['available_cpu_cores']}"
        
        if memory_gb > available["available_memory_gb"]:
            return False, f"Insufficient memory. Available: {available['available_memory_gb']}GB"
        
        if gpu and not available["gpu_available"]:
            return False, "GPU not available or already locked"
        
        # Enforce maximum lock ratios
        total_cpu = psutil.cpu_count()
        total_memory_gb = psutil.virtual_memory().total / (1024**3)
        
        if (available["locked_cpu_cores"] + cpu_cores) / total_cpu > self.max_cpu_lock_ratio:
            return False, f"Would exceed maximum CPU lock ratio of {self.max_cpu_lock_ratio}"
        
        if (available["locked_memory_gb"] + memory_gb) / total_memory_gb > self.max_memory_lock_ratio:
            return False, f"Would exceed maximum memory lock ratio of {self.max_memory_lock_ratio}"
        
        # Calculate collateral value
        collateral_value = self.calculate_collateral_value(
            cpu_cores, memory_gb, gpu, lock_duration_sec
        )
        
        # Generate lock ID
        lock_id = hashlib.sha256(
            f"{self.node_id}{time.time()}{cpu_cores}{memory_gb}{gpu}".encode()
        ).hexdigest()[:16]
        
        # Create resource lock
        lock = ResourceLock(
            lock_id=lock_id,
            node_id=self.node_id,
            cpu_cores_locked=cpu_cores,
            memory_gb_locked=memory_gb,
            gpu_locked=gpu,
            collateral_value=collateral_value,
            lock_start_time=time.time(),
            lock_duration_sec=lock_duration_sec,
            lock_purpose=purpose,
            associated_tx=associated_tx,
            status="locked"
        )
        
        self.locked_resources[lock_id] = lock
        self._save_state()
        
        return True, lock_id
    
    def unlock_resources(
        self,
        lock_id: str,
        unlock_signature: str = None
    ) -> Tuple[bool, str]:
        """
        Unlock previously locked resources
        
        Returns:
            Tuple[success, message]
        """
        if lock_id not in self.locked_resources:
            return False, "Lock ID not found"
        
        lock = self.locked_resources[lock_id]
        
        # Verify unlock signature if required
        if unlock_signature:
            # In production, verify cryptographic signature
            lock.unlock_signature = unlock_signature
        
        # Update lock status
        lock.status = "unlocked"
        
        # Move to history
        self.lock_history.append(asdict(lock))
        del self.locked_resources[lock_id]
        
        self._save_state()
        
        return True, f"Resources unlocked. Collateral value: {lock.collateral_value}"
    
    def auto_unlock_expired_locks(self) -> int:
        """Automatically unlock expired locks"""
        current_time = time.time()
        expired_locks = []
        
        for lock_id, lock in self.locked_resources.items():
            if lock.lock_start_time + lock.lock_duration_sec <= current_time:
                lock.status = "expired"
                expired_locks.append(lock_id)
                self.lock_history.append(asdict(lock))
        
        # Remove expired locks
        for lock_id in expired_locks:
            del self.locked_resources[lock_id]
        
        if expired_locks:
            self._save_state()
        
        return len(expired_locks)
    
    def get_lock_status(self, lock_id: str) -> Optional[Dict]:
        """Get status of a specific lock"""
        if lock_id in self.locked_resources:
            lock = self.locked_resources[lock_id]
            return {
                **asdict(lock),
                "time_remaining_sec": max(0, lock.lock_start_time + lock.lock_duration_sec - time.time()),
                "is_expired": lock.lock_start_time + lock.lock_duration_sec <= time.time()
            }
        return None
    
    def get_all_locks(self) -> List[Dict]:
        """Get status of all locks"""
        locks = []
        current_time = time.time()
        
        for lock in self.locked_resources.values():
            lock_dict = asdict(lock)
            lock_dict["time_remaining_sec"] = max(0, lock.lock_start_time + lock.lock_duration_sec - current_time)
            lock_dict["is_expired"] = lock.lock_start_time + lock.lock_duration_sec <= current_time
            locks.append(lock_dict)
        
        return locks
    
    def get_total_collateral_value(self) -> float:
        """Get total value of all currently locked resources"""
        return sum(lock.collateral_value for lock in self.locked_resources.values())


class CollateralManager:
    """High-level manager for collateral operations"""
    
    def __init__(self, node_id: str = None):
        self.node_id = node_id or self._generate_node_id()
        
        # Initialize compute market
        config = {
            "pricing": {
                "cpu_per_core": 0.05,
                "memory_per_gb": 0.02
            },
            "token_symbol": "COMPUTE"
        }
        self.compute_market = ComputeMarket(config)
        
        # Initialize resource locker
        self.resource_locker = ResourceLocker(self.node_id, self.compute_market)
        
        # Background task for auto-unlock
        self.running = False
    
    def _generate_node_id(self) -> str:
        """Generate unique node ID"""
        machine = f"{os.uname().nodename}-{psutil.cpu_count()}-{psutil.virtual_memory().total}"
        return hashlib.sha256(machine.encode()).hexdigest()[:12]
    
    async def start_background_tasks(self):
        """Start background tasks for collateral management"""
        self.running = True
        while self.running:
            # Auto-unlock expired locks every minute
            expired_count = self.resource_locker.auto_unlock_expired_locks()
            if expired_count > 0:
                print(f"[COLLATERAL] Auto-unlocked {expired_count} expired locks")
            
            await asyncio.sleep(60)
    
    def stop_background_tasks(self):
        """Stop background tasks"""
        self.running = False
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            "node_id": self.node_id,
            "available_resources": self.resource_locker.get_available_resources(),
            "active_locks": len(self.resource_locker.locked_resources),
            "total_collateral_value": self.resource_locker.get_total_collateral_value(),
            "lock_history_count": len(self.resource_locker.lock_history),
            "market_stats": self.compute_market.get_market_stats()
        }


# Factory function
def create_collateral_manager(node_id: str = None) -> CollateralManager:
    """Create collateral manager with default configuration"""
    return CollateralManager(node_id)


if __name__ == "__main__":
    # Example usage
    manager = create_collateral_manager()
    
    print("=" * 70)
    print("  MEMBRA Compute Resource Collateral System")
    print(f"  Node: {manager.node_id}")
    print("=" * 70)
    
    # Get available resources
    available = manager.resource_locker.get_available_resources()
    print(f"\nAvailable Resources:")
    print(f"  CPU Cores: {available['available_cpu_cores']}/{available['total_cpu_cores']}")
    print(f"  Memory: {available['available_memory_gb']:.1f}GB/{available['total_memory_gb']:.1f}GB")
    print(f"  GPU: {'Available' if available['gpu_available'] else 'Not Available'}")
    
    # Lock some resources
    print(f"\nLocking resources as collateral...")
    success, result = manager.resource_locker.lock_resources(
        cpu_cores=2,
        memory_gb=4.0,
        gpu=False,
        lock_duration_sec=3600,  # 1 hour
        purpose="token_mint"
    )
    
    if success:
        print(f"  Lock successful! Lock ID: {result}")
        lock_status = manager.resource_locker.get_lock_status(result)
        print(f"  Collateral Value: {lock_status['collateral_value']} COMPUTE")
    else:
        print(f"  Lock failed: {result}")
    
    # Get system status
    status = manager.get_system_status()
    print(f"\nSystem Status:")
    print(f"  Active Locks: {status['active_locks']}")
    print(f"  Total Collateral: {status['total_collateral_value']} COMPUTE")