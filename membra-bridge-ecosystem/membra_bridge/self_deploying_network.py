"""
Self-Deploying Network with Permalinks
Automated deployment system with permalink generation and network coordination.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import hashlib
import subprocess
import aiohttp
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NetworkNode:
    """Network node information"""
    node_id: str
    ip_address: str
    port: int
    role: str  # 'validator', 'oracle', 'liquidity_provider', 'full_node'
    wallet_address: str
    stake_amount: int
    permalink: str
    status: str  # 'online', 'offline', 'deploying'
    last_heartbeat: str
    capabilities: Dict
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DeploymentManifest:
    """Deployment manifest for a network node"""
    manifest_id: str
    node_id: str
    docker_compose_config: Dict
    environment_variables: Dict
    deployment_script: str
    permalink: str
    checksum: str
    created_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Permalink:
    """Permanent link for network resource"""
    permalink_id: str
    resource_type: str  # 'node', 'contract', 'api', 'dashboard'
    resource_id: str
    url: str
    qr_code: str
    expires_at: Optional[str]
    access_count: int
    created_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class PermalinkGenerator:
    """Generates permalinks for network resources"""
    
    def __init__(self, base_url: str = "https://membra.network"):
        self.base_url = base_url
        self.permalinks: Dict[str, Permalink] = {}
    
    def generate_permalink(
        self,
        resource_type: str,
        resource_id: str,
        expires_in_hours: Optional[int] = None
    ) -> Permalink:
        """Generate a permalink for a resource"""
        permalink_id = hashlib.sha256(
            f"{resource_type}{resource_id}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Generate URL
        url = f"{self.base_url}/{resource_type}/{permalink_id}"
        
        # Generate QR code (simplified - would use actual QR library)
        qr_code = f"QR_CODE_{permalink_id}"
        
        # Calculate expiration
        expires_at = None
        if expires_in_hours:
            expires_at = (datetime.now() + timedelta(hours=expires_in_hours)).isoformat()
        
        permalink = Permalink(
            permalink_id=permalink_id,
            resource_type=resource_type,
            resource_id=resource_id,
            url=url,
            qr_code=qr_code,
            expires_at=expires_at,
            access_count=0,
            created_at=datetime.now().isoformat()
        )
        
        self.permalinks[permalink_id] = permalink
        logger.info(f"Generated permalink {permalink_id} for {resource_type}/{resource_id}")
        
        return permalink
    
    def get_permalink(self, permalink_id: str) -> Optional[Permalink]:
        """Get permalink by ID"""
        return self.permalinks.get(permalink_id)
    
    def access_permalink(self, permalink_id: str) -> bool:
        """Record access to permalink"""
        permalink = self.permalinks.get(permalink_id)
        if not permalink:
            return False
        
        # Check expiration
        if permalink.expires_at:
            if datetime.fromisoformat(permalink.expires_at) < datetime.now():
                return False
        
        permalink.access_count += 1
        return True


class DockerDeploymentManager:
    """Manages Docker deployments for network nodes"""
    
    def __init__(self):
        self.deployments: Dict[str, DeploymentManifest] = {}
        self.running_containers: Dict[str, List[str]] = {}
    
    def generate_docker_compose_config(
        self,
        node_id: str,
        role: str,
        wallet_address: str,
        port: int
    ) -> Dict:
        """Generate docker-compose configuration for a node"""
        
        config = {
            'version': '3.8',
            'services': {
                f'membra-{role}': {
                    'image': f'membra/{role}:latest',
                    'container_name': f'membra-{node_id}',
                    'ports': [f'{port}:8000'],
                    'environment': {
                        'NODE_ID': node_id,
                        'ROLE': role,
                        'WALLET_ADDRESS': wallet_address,
                        'NETWORK_ID': 'membra-mainnet'
                    },
                    'volumes': [
                        f'{node_id}_data:/app/data',
                        f'{node_id}_logs:/app/logs'
                    ],
                    'restart': 'unless-stopped',
                    'networks': ['membra-network']
                }
            },
            'networks': {
                'membra-network': {
                    'driver': 'bridge'
                }
            },
            'volumes': {
                f'{node_id}_data': None,
                f'{node_id}_logs': None
            }
        }
        
        return config
    
    def generate_deployment_script(
        self,
        node_id: str,
        config: Dict
    ) -> str:
        """Generate deployment script for a node"""
        
        script = f"""#!/bin/bash
# Auto-generated deployment script for node {node_id}

set -e

echo "Deploying MEMBRA node {node_id}..."

# Create docker-compose file
cat > docker-compose.{node_id}.yml << 'EOF'
{json.dumps(config, indent=2)}
EOF

# Pull latest images
echo "Pulling Docker images..."
docker-compose -f docker-compose.{node_id}.yml pull

# Start services
echo "Starting services..."
docker-compose -f docker-compose.{node_id}.yml up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 30

# Check status
echo "Checking service status..."
docker-compose -f docker-compose.{node_id}.yml ps

echo "Deployment complete for node {node_id}"
"""
        return script
    
    def create_deployment_manifest(
        self,
        node_id: str,
        role: str,
        wallet_address: str,
        port: int,
        environment_vars: Dict
    ) -> DeploymentManifest:
        """Create deployment manifest for a node"""
        
        # Generate docker-compose config
        docker_config = self.generate_docker_compose_config(
            node_id, role, wallet_address, port
        )
        
        # Generate deployment script
        deployment_script = self.generate_deployment_script(node_id, docker_config)
        
        # Calculate checksum
        manifest_content = json.dumps(docker_config, sort_keys=True)
        checksum = hashlib.sha256(manifest_content.encode()).hexdigest()
        
        manifest_id = hashlib.sha256(
            f"{node_id}{checksum}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        manifest = DeploymentManifest(
            manifest_id=manifest_id,
            node_id=node_id,
            docker_compose_config=docker_config,
            environment_variables=environment_vars,
            deployment_script=deployment_script,
            permalink=f"https://membra.network/deploy/{manifest_id}",
            checksum=checksum,
            created_at=datetime.now().isoformat()
        )
        
        self.deployments[manifest_id] = manifest
        logger.info(f"Created deployment manifest {manifest_id} for node {node_id}")
        
        return manifest
    
    async def deploy_node(self, manifest: DeploymentManifest) -> bool:
        """Deploy a node using its manifest"""
        try:
            # Write docker-compose file
            compose_file = f"docker-compose.{manifest.node_id}.yml"
            with open(compose_file, 'w') as f:
                json.dump(manifest.docker_compose_config, f, indent=2)
            
            # Write deployment script
            script_file = f"deploy_{manifest.node_id}.sh"
            with open(script_file, 'w') as f:
                f.write(manifest.deployment_script)
            
            # Make script executable
            subprocess.run(['chmod', '+x', script_file], check=True)
            
            # Execute deployment script
            result = subprocess.run(
                ['bash', script_file],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully deployed node {manifest.node_id}")
                
                # Track running containers
                self.running_containers[manifest.node_id] = [
                    f'membra-{manifest.node_id}'
                ]
                
                return True
            else:
                logger.error(f"Deployment failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Deployment timed out for node {manifest.node_id}")
            return False
        except Exception as e:
            logger.error(f"Deployment error: {e}")
            return False
    
    def stop_node(self, node_id: str) -> bool:
        """Stop a running node"""
        try:
            compose_file = f"docker-compose.{node_id}.yml"
            result = subprocess.run(
                ['docker-compose', '-f', compose_file, 'down'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                if node_id in self.running_containers:
                    del self.running_containers[node_id]
                logger.info(f"Stopped node {node_id}")
                return True
            else:
                logger.error(f"Failed to stop node {node_id}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping node {node_id}: {e}")
            return False


class SelfDeployingNetwork:
    """Coordinates self-deploying network with permalinks"""
    
    def __init__(self):
        self.nodes: Dict[str, NetworkNode] = {}
        self.permalink_generator = PermalinkGenerator()
        self.deployment_manager = DockerDeploymentManager()
        self.network_stats = {
            'total_nodes': 0,
            'online_nodes': 0,
            'total_stake': 0
        }
    
    async def register_and_deploy_node(
        self,
        ip_address: str,
        role: str,
        wallet_address: str,
        port: int = 8000,
        stake_amount: int = 1000,
        capabilities: Dict = None
    ) -> Dict:
        """Register and deploy a new network node"""
        
        capabilities = capabilities or {}
        
        # Generate node ID
        node_id = hashlib.sha256(
            f"{ip_address}{role}{wallet_address}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Generate permalink
        permalink = self.permalink_generator.generate_permalink(
            'node', node_id, expires_in_hours=8760  # 1 year
        )
        
        # Create network node
        node = NetworkNode(
            node_id=node_id,
            ip_address=ip_address,
            port=port,
            role=role,
            wallet_address=wallet_address,
            stake_amount=stake_amount,
            permalink=permalink.url,
            status='deploying',
            last_heartbeat=datetime.now().isoformat(),
            capabilities=capabilities
        )
        
        self.nodes[node_id] = node
        
        # Create deployment manifest
        manifest = self.deployment_manager.create_deployment_manifest(
            node_id, role, wallet_address, port, {}
        )
        
        # Deploy node
        deployment_success = await self.deployment_manager.deploy_node(manifest)
        
        if deployment_success:
            node.status = 'online'
            self.network_stats['online_nodes'] += 1
        else:
            node.status = 'offline'
        
        self.network_stats['total_nodes'] = len(self.nodes)
        self.network_stats['total_stake'] += stake_amount
        
        logger.info(f"Registered and deployed node {node_id} with role {role}")
        
        return {
            'node': node.to_dict(),
            'manifest': manifest.to_dict(),
            'permalink': permalink.to_dict(),
            'deployment_success': deployment_success
        }
    
    def update_node_heartbeat(self, node_id: str) -> bool:
        """Update node heartbeat"""
        if node_id not in self.nodes:
            return False
        
        self.nodes[node_id].last_heartbeat = datetime.now().isoformat()
        
        # Check if node was offline and now online
        if self.nodes[node_id].status == 'offline':
            self.nodes[node_id].status = 'online'
            self.network_stats['online_nodes'] += 1
        
        return True
    
    def get_network_topology(self) -> Dict:
        """Get current network topology"""
        nodes_by_role = {}
        for node in self.nodes.values():
            if node.role not in nodes_by_role:
                nodes_by_role[node.role] = []
            nodes_by_role[node.role].append(node.to_dict())
        
        return {
            'network_stats': self.network_stats,
            'nodes_by_role': nodes_by_role,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_node_permalink(self, node_id: str) -> Optional[str]:
        """Get permalink for a node"""
        node = self.nodes.get(node_id)
        if not node:
            return None
        return node.permalink
    
    async def health_check_network(self) -> Dict:
        """Perform health check on all nodes"""
        healthy_nodes = 0
        unhealthy_nodes = []
        
        for node_id, node in self.nodes.items():
            # Check if heartbeat is recent (within 5 minutes)
            last_heartbeat = datetime.fromisoformat(node.last_heartbeat)
            if datetime.now() - last_heartbeat < timedelta(minutes=5):
                healthy_nodes += 1
            else:
                unhealthy_nodes.append(node_id)
                node.status = 'offline'
                if self.network_stats['online_nodes'] > 0:
                    self.network_stats['online_nodes'] -= 1
        
        return {
            'total_nodes': len(self.nodes),
            'healthy_nodes': healthy_nodes,
            'unhealthy_nodes': len(unhealthy_nodes),
            'unhealthy_node_ids': unhealthy_nodes,
            'timestamp': datetime.now().isoformat()
        }


async def main():
    """Example usage"""
    network = SelfDeployingNetwork()
    
    # Deploy a validator node
    result = await network.register_and_deploy_node(
        ip_address="192.168.1.100",
        role="validator",
        wallet_address="0x1234567890abcdef",
        port=8001,
        stake_amount=1500,
        capabilities={"cpu_cores": 8, "memory_gb": 16}
    )
    
    print("=== Node Deployment Result ===")
    print(json.dumps(result, indent=2))
    
    # Get network topology
    topology = network.get_network_topology()
    print("\n=== Network Topology ===")
    print(json.dumps(topology, indent=2))
    
    # Perform health check
    health = await network.health_check_network()
    print("\n=== Network Health ===")
    print(json.dumps(health, indent=2))


if __name__ == '__main__':
    asyncio.run(main())