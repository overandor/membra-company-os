"""MEMBRA CompanyOS — WorldBridge service."""
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.worldbridge import WorldAsset, AssetType, AssetStatus, AssetListing, AssetReservation, AssetProof, Vendor, Person, Route
from app.schemas.worldbridge import WorldAssetCreate, AssetListingCreate, AssetReservationCreate, AssetProofCreate, VendorCreate, PersonCreate, RouteCreate
from app.core.logging import get_logger
from app.services.proofbook import ProofBookService

logger = get_logger(__name__)


class WorldBridgeService:
    def __init__(self, db: Session):
        self.db = db
        self.proof = ProofBookService(db)

    def register_asset(self, data: WorldAssetCreate) -> WorldAsset:
        asset = WorldAsset(
            company_id=UUID(data.company_id) if data.company_id else None,
            owner_wallet=data.owner_wallet,
            asset_type=AssetType(data.asset_type),
            name=data.name,
            description=data.description,
            location_json=data.location_json or {},
            attributes=data.attributes or {},
            media_cids=data.media_cids or [],
            metadata_json=data.metadata_json or {},
        )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        self.proof.write_entry(
            entry_type="ASSET_RESERVED",
            resource_type="world_asset",
            resource_id=asset.id,
            actor_type="human",
            actor_id=UUID("00000000-0000-0000-0000-000000000000"),
            description=f"Asset registered: {data.name} ({data.asset_type})",
            data={"asset_type": data.asset_type, "owner": data.owner_wallet},
        )
        return asset

    def update_asset_status(self, asset_id: str, status: str) -> WorldAsset:
        asset = self.db.query(WorldAsset).filter(WorldAsset.id == UUID(asset_id)).first()
        if not asset:
            raise ValueError("Asset not found")
        asset.status = AssetStatus(status)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def create_listing(self, data: AssetListingCreate) -> AssetListing:
        listing = AssetListing(
            asset_id=UUID(data.asset_id),
            listing_type=data.listing_type,
            title=data.title,
            description=data.description,
            price=data.price,
            currency=data.currency,
            visibility=data.visibility,
            expires_at=data.expires_at,
        )
        self.db.add(listing)
        self.db.commit()
        self.db.refresh(listing)
        return listing

    def approve_listing(self, listing_id: str) -> AssetListing:
        listing = self.db.query(AssetListing).filter(AssetListing.id == UUID(listing_id)).first()
        if not listing:
            raise ValueError("Listing not found")
        listing.governance_approved = True
        if listing.owner_consent:
            listing.status = "published"
            listing.published_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(listing)
        self.proof.write_entry(
            entry_type="LISTING_PUBLISHED",
            resource_type="asset_listing",
            resource_id=listing.id,
            actor_type="system",
            actor_id=UUID("00000000-0000-0000-0000-000000000000"),
            description=f"Listing approved and published",
            data={"asset_id": str(listing.asset_id)},
        )
        return listing

    def create_reservation(self, data: AssetReservationCreate) -> AssetReservation:
        res = AssetReservation(
            asset_id=UUID(data.asset_id),
            reserved_by=UUID(data.reserved_by) if data.reserved_by else None,
            reservation_type=data.reservation_type,
            start_time=data.start_time,
            end_time=data.end_time,
            cost=data.cost or 0,
        )
        self.db.add(res)
        self.db.commit()
        self.db.refresh(res)
        return res

    def submit_asset_proof(self, data: AssetProofCreate) -> AssetProof:
        proof = AssetProof(
            asset_id=UUID(data.asset_id),
            proof_type=data.proof_type,
            proof_data=data.proof_data or {},
            ipfs_cid=data.ipfs_cid,
            proof_hash=data.proof_hash,
        )
        self.db.add(proof)
        self.db.commit()
        self.db.refresh(proof)
        return proof

    def create_vendor(self, data: VendorCreate) -> Vendor:
        vendor = Vendor(
            company_id=UUID(data.company_id) if data.company_id else None,
            name=data.name,
            vendor_type=data.vendor_type,
            contact_json=data.contact_json or {},
            wallet_address=data.wallet_address,
            service_areas=data.service_areas or [],
            metadata_json=data.metadata_json or {},
        )
        self.db.add(vendor)
        self.db.commit()
        self.db.refresh(vendor)
        return vendor

    def create_person(self, data: PersonCreate) -> Person:
        person = Person(
            user_id=UUID(data.user_id) if data.user_id else None,
            wallet_address=data.wallet_address,
            display_name=data.display_name,
            skills=data.skills or [],
            availability_json=data.availability_json or {},
            location_json=data.location_json or {},
            metadata_json=data.metadata_json or {},
        )
        self.db.add(person)
        self.db.commit()
        self.db.refresh(person)
        return person

    def create_route(self, data: RouteCreate) -> Route:
        route = Route(
            company_id=UUID(data.company_id) if data.company_id else None,
            name=data.name,
            route_type=data.route_type,
            waypoints=data.waypoints or [],
            vehicle_asset_id=UUID(data.vehicle_asset_id) if data.vehicle_asset_id else None,
            driver_person_id=UUID(data.driver_person_id) if data.driver_person_id else None,
            schedule_json=data.schedule_json or {},
            estimated_duration_min=data.estimated_duration_min,
        )
        self.db.add(route)
        self.db.commit()
        self.db.refresh(route)
        return route

    def list_assets(self, company_id: Optional[str] = None, asset_type: Optional[str] = None, limit: int = 50) -> List[WorldAsset]:
        q = self.db.query(WorldAsset)
        if company_id:
            q = q.filter(WorldAsset.company_id == UUID(company_id))
        if asset_type:
            q = q.filter(WorldAsset.asset_type == AssetType(asset_type))
        return q.order_by(WorldAsset.created_at.desc()).limit(limit).all()
