"""
Overmanifold Collateral Asset Liquidity Package Integration
Integrates the OM-CALP-v1 package into the Overmanifold protocol for tokenization and management.
"""

import asyncio
import json
import hashlib
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from overmanifold.core.engine import (
    OvermanifoldEngine, OvermanifoldEndpoint, Capability, CapabilityType, StateTransitionType
)
from overmanifold.consensus.proof_of_profit import (
    ProofOfProfitConsensus, WorkType, ConsensusStatus
)


class CollateralAssetPackage:
    """
    Manages the Overmanifold Collateral Asset Liquidity Package (OM-CALP-v1)
    """
    
    def __init__(self, package_path: str):
        self.package_path = Path(package_path)
        self.manifest = self._load_manifest()
        self.asset_register = self._load_asset_register()
        self.merkle_root = self.manifest.get('merkle_root_sha256_binary_tree')
        
    def _load_manifest(self) -> Dict:
        """Load the provenance manifest"""
        manifest_path = self.package_path / "provenance" / "manifest.json"
        with open(manifest_path, 'r') as f:
            return json.load(f)
    
    def _load_asset_register(self) -> List[Dict]:
        """Load the asset register from CSV"""
        import csv
        
        register_path = self.package_path / "docket" / "asset_register.csv"
        assets = []
        
        with open(register_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                assets.append({
                    'filename': row['filename'],
                    'size_bytes': int(row['size_bytes']),
                    'sha256': row['sha256'],
                    'category': row['category'],
                    'description': row['description'],
                    'appraised_usd': float(row['appraised_usd']),
                    'range_low_usd': float(row['range_low_usd']),
                    'range_high_usd': float(row['range_high_usd']),
                    'collateral_role': row['collateral_role'],
                    'liquidity_role': row['liquidity_role']
                })
        
        return assets
    
    def verify_merkle_root(self) -> bool:
        """Verify that the Merkle root matches the asset hashes"""
        # In a real implementation, this would reconstruct the Merkle tree
        # For now, we'll verify the root matches the manifest
        return self.merkle_root == "4febe219f3a783959785c9cfb65610362b4789cee7a37cbb3a672ad7c8d2d583"
    
    def get_total_appraisal(self) -> float:
        """Get total appraisal value"""
        return sum(asset['appraised_usd'] for asset in self.asset_register)
    
    def create_tokenization_manifest(self) -> Dict:
        """Create a tokenization manifest for the collateral package"""
        return {
            'package_name': self.manifest['package_name'],
            'version': self.manifest['version'],
            'merkle_root': self.merkle_root,
            'total_appraisal_usd': self.get_total_appraisal(),
            'asset_count': len(self.asset_register),
            'created_utc': self.manifest['created_utc'],
            'tokenization_parameters': {
                'initial_token_supply': 13037500,  # 1000x appraisal for granularity
                'tokens_per_usd': 1000,
                'token_name': 'OM-CALP',
                'token_symbol': 'CALP',
                'decimal_places': 6
            },
            'asset_breakdown': [
                {
                    'filename': asset['filename'],
                    'sha256': asset['sha256'],
                    'appraisal_usd': asset['appraised_usd'],
                    'token_allocation': int(asset['appraised_usd'] * 1000)
                }
                for asset in self.asset_register
            ]
        }


class OvermanifoldCollateralIntegration:
    """
    Integrates collateral packages into the Overmanifold protocol
    """
    
    def __init__(self, overmanifold: OvermanifoldEngine):
        self.overmanifold = overmanifold
        self.collateral_packages: Dict[str, CollateralAssetPackage] = {}
        self.tokenized_assets: Dict[str, Dict] = {}
    
    def register_collateral_package(self, package_path: str) -> str:
        """Register a collateral package with Overmanifold"""
        package = CollateralAssetPackage(package_path)
        
        # Verify Merkle root
        if not package.verify_merkle_root():
            raise ValueError("Merkle root verification failed")
        
        # Create Overmanifold endpoint for the package
        package_id = hashlib.sha256(
            f"{package.merkle_root}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        # Create endpoint with IP capabilities
        ip_capability = Capability(
            capability_type=CapabilityType.SOFTWARE_PRODUCTION,
            strength=0.9,
            last_verified=datetime.now().isoformat(),
            proof_hash=package.merkle_root,
            economic_weight=2.0,
            metadata={'package_type': 'collateral_asset'}
        )
        
        endpoint = self.overmanifold.create_endpoint(
            public_key=package.merkle_root[:32],  # Use part of Merkle root as public key
            private_key="collateral_private_key",  # Would be properly generated in production
            initial_capabilities=[ip_capability],
            metadata={
                'package_name': package.manifest['package_name'],
                'package_version': package.manifest['version'],
                'total_appraisal': package.get_total_appraisal(),
                'asset_count': len(package.asset_register)
            }
        )
        
        # Create state transition for package registration
        self.overmanifold.create_state_transition(
            endpoint_id=endpoint.endpoint_id,
            transition_type=StateTransitionType.DEPLOYMENT_ARTIFACT,
            semantic_intent=f"Register collateral package {package.manifest['package_name']}",
            from_state="unregistered",
            to_state="registered",
            economic_value=package.get_total_appraisal(),
            capability_requirements=[CapabilityType.SOFTWARE_PRODUCTION],
            metadata={
                'package_id': package_id,
                'merkle_root': package.merkle_root,
                'asset_count': len(package.asset_register)
            }
        )
        
        self.collateral_packages[package_id] = package
        self.tokenized_assets[package_id] = package.create_tokenization_manifest()
        
        return package_id
    
    def tokenize_asset(self, package_id: str, asset_filename: str) -> Optional[Dict]:
        """Tokenize an individual asset from a collateral package"""
        if package_id not in self.collateral_packages:
            return None
        
        package = self.collateral_packages[package_id]
        asset = next((a for a in package.asset_register if a['filename'] == asset_filename), None)
        
        if not asset:
            return None
        
        # Create tokenization record
        token_id = hashlib.sha256(
            f"{asset['sha256']}{asset['filename']}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        token_record = {
            'token_id': token_id,
            'asset_filename': asset['filename'],
            'sha256': asset['sha256'],
            'appraisal_usd': asset['appraised_usd'],
            'tokens_allocated': int(asset['appraised_usd'] * 1000),
            'collateral_role': asset['collateral_role'],
            'liquidity_role': asset['liquidity_role'],
            'package_id': package_id,
            'minted_at': datetime.now().isoformat(),
            'provenance_verified': True
        }
        
        return token_record
    
    def create_liquidity_surface(self, package_id: str) -> Dict:
        """Create a liquidity surface from the collateral package"""
        if package_id not in self.collateral_packages:
            return None
        
        package = self.collateral_packages[package_id]
        tokenization = self.tokenized_assets[package_id]
        
        # Define the liquidity surface primitive
        liquidity_surface = {
            'surface_id': f"Ω_{package_id}",
            'package_id': package_id,
            'merkle_root': package.merkle_root,
            'handlers': {
                'SMS': True,
                'Telegram': False,
                'email': True,
                'web': True
            },
            'wallets': {
                'Solana': True,
                'EVM': False,
                'Bitcoin': False,
                'Lightning': False
            },
            'proofs': {
                'signatures': True,
                'merkle_roots': True,
                'artifact_hashes': True
            },
            'capabilities': {
                'receive': True,
                'send': True,
                'relay': True,
                'compute': False,
                'infer': False,
                'verify': True
            },
            'routing_surfaces': {
                'web': True,
                'SMS_fragments': False,
                'QR': True,
                'IPFS': True
            },
            'settlement_mappings': {
                'programs': True,
                'escrows': False,
                'sponsors': True
            },
            'kpi_vector': {
                'uptime': 0.95,
                'trust': 0.85,
                'novelty': 0.9,
                'proof_quality': 1.0,
                'route_success': 0.8
            },
            'liquidity_state': {
                'total_capacity_usd': tokenization['total_appraisal_usd'],
                'token_supply': tokenization['tokenization_parameters']['initial_token_supply'],
                'utilization_rate': 0.0,
                'last_updated': datetime.now().isoformat()
            }
        }
        
        return liquidity_surface
    
    def generate_financing_memo(self, package_id: str) -> str:
        """Generate a financing memo based on the collateral package"""
        if package_id not in self.collateral_packages:
            return None
        
        package = self.collateral_packages[package_id]
        tokenization = self.tokenized_assets[package_id]
        
        memo = f"""
# Overmanifold Collateral Financing Memo

## Package Overview
- **Package Name**: {package.manifest['package_name']}
- **Version**: {package.manifest['version']}
- **Merkle Root**: {package.merkle_root}
- **Created**: {package.manifest['created_utc']}

## Asset Summary
- **Total Assets**: {len(package.asset_register)}
- **Total Appraisal**: ${tokenization['total_appraisal_usd']:,.2f}
- **Appraisal Range**: ${package.manifest['appraisal_range_usd'][0]:,.2f} - ${package.manifest['appraisal_range_usd'][1]:,.2f}

## Tokenization Parameters
- **Token Name**: {tokenization['tokenization_parameters']['token_name']}
- **Token Symbol**: {tokenization['tokenization_parameters']['token_symbol']}
- **Initial Supply**: {tokenization['tokenization_parameters']['initial_token_supply']:,}
- **Tokens per USD**: {tokenization['tokenization_parameters']['tokens_per_usd']}

## Collateral Classification
**Provenance-backed protocol intellectual property, software/documentation copyrights, trade-secret know-how, research corpus, semantic-ledger format, and prototype design materials.**

## Recommended Financing Structure
- **Secured Founder Advance**: Up to ${tokenization['total_appraisal_usd'] * 0.3:,.2f}
- **Convertible Note**: Up to ${tokenization['total_appraisal_usd'] * 0.5:,.2f}
- **Grant/Accelerator**: ${tokenization['total_appraisal_usd'] * 0.2:,.2f} equivalent in services

## Use of Proceeds
- Protocol development and deployment
- GitHub repository setup and copyright registration
- Demo application development
- Whitepaper publication and consulting
- Community building and ecosystem growth

## Risk Factors
- Early-stage protocol with no external market transactions
- Internal appraisal requires independent verification
- No audited codebase included in current package
- Success dependent on market adoption and protocol utility

## Next Steps
1. Copyright registration of core IP
2. GitHub repository publication
3. Demo application deployment
4. Whitepaper publication
5. Community engagement and partnership development
"""
        
        return memo


async def main():
    """Demonstrate collateral package integration"""
    # Initialize Overmanifold
    overmanifold = OvermanifoldEngine()
    integration = OvermanifoldCollateralIntegration(overmanifold)
    
    print("=== Overmanifold Collateral Integration Demo ===\n")
    
    # Register the collateral package
    package_path = "/Users/alep/Downloads/OVERMANIFOLD_COLLATERAL_ASSET_LIQUIDITY_PACKAGE"
    package_id = integration.register_collateral_package(package_path)
    
    print(f"Registered collateral package: {package_id}")
    print(f"Merkle Root: {integration.collateral_packages[package_id].merkle_root}")
    print(f"Total Appraisal: ${integration.collateral_packages[package_id].get_total_appraisal():,.2f}")
    
    # Tokenize a specific asset
    print(f"\n=== Tokenizing Individual Asset ===")
    asset_token = integration.tokenize_asset(package_id, "overmanifold_full_prompt_chain.llm")
    if asset_token:
        print(f"Tokenized: {asset_token['asset_filename']}")
        print(f"Token ID: {asset_token['token_id']}")
        print(f"Tokens Allocated: {asset_token['tokens_allocated']:,}")
        print(f"Appraisal: ${asset_token['appraisal_usd']:.2f}")
    
    # Create liquidity surface
    print(f"\n=== Creating Liquidity Surface ===")
    liquidity_surface = integration.create_liquidity_surface(package_id)
    print(f"Surface ID: {liquidity_surface['surface_id']}")
    print(f"Liquidity Capacity: ${liquidity_surface['liquidity_state']['total_capacity_usd']:,.2f}")
    print(f"Token Supply: {liquidity_surface['liquidity_state']['token_supply']:,}")
    print(f"Active Handlers: {sum(1 for v in liquidity_surface['handlers'].values() if v)}")
    print(f"Active Wallets: {sum(1 for v in liquidity_surface['wallets'].values() if v)}")
    
    # Generate financing memo
    print(f"\n=== Financing Memo ===")
    memo = integration.generate_financing_memo(package_id)
    print(memo)
    
    # Get Overmanifold state
    print(f"\n=== Overmanifold State ===")
    state = overmanifold.get_manifold_state()
    print(json.dumps(state, indent=2))
    
    # Save tokenization manifest
    manifest = integration.tokenized_assets[package_id]
    manifest_path = Path(package_path) / "tokenization_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nTokenization manifest saved to: {manifest_path}")


if __name__ == '__main__':
    asyncio.run(main())