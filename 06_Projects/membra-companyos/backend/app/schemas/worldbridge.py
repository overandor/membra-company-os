"""WorldBridge schemas — Asset, Listing, Reservation, Proof, Vendor, Person, Route."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class WorldAssetCreate(BaseModel):
    company_id: Optional[str] = None
    owner_wallet: str
    asset_type: str
    name: str
    description: Optional[str] = None
    location_json: Optional[Dict[str, Any]] = {}
    attributes: Optional[Dict[str, Any]] = {}
    media_cids: Optional[List[str]] = []
    metadata_json: Optional[Dict[str, Any]] = {}


class WorldAssetRead(BaseModel):
    id: str
    company_id: Optional[str] = None
    owner_wallet: str
    asset_type: str
    name: str
    description: Optional[str] = None
    status: str
    location_json: Optional[Dict[str, Any]] = {}
    attributes: Optional[Dict[str, Any]] = {}
    media_cids: Optional[List[str]] = []
    kpi_json: Optional[Dict[str, Any]] = {}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetListingCreate(BaseModel):
    asset_id: str
    listing_type: str
    title: str
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = "USD"
    visibility: Optional[str] = "private"
    expires_at: Optional[datetime] = None


class AssetReservationCreate(BaseModel):
    asset_id: str
    reserved_by: Optional[str] = None
    reservation_type: str
    start_time: datetime
    end_time: datetime
    cost: Optional[float] = 0


class AssetProofCreate(BaseModel):
    asset_id: str
    proof_type: str
    proof_data: Optional[Dict[str, Any]] = {}
    ipfs_cid: Optional[str] = None
    proof_hash: str


class VendorCreate(BaseModel):
    company_id: Optional[str] = None
    name: str
    vendor_type: str
    contact_json: Optional[Dict[str, Any]] = {}
    wallet_address: Optional[str] = None
    service_areas: Optional[List[str]] = []
    metadata_json: Optional[Dict[str, Any]] = {}


class PersonCreate(BaseModel):
    user_id: Optional[str] = None
    wallet_address: Optional[str] = None
    display_name: Optional[str] = None
    skills: Optional[List[str]] = []
    availability_json: Optional[Dict[str, Any]] = {}
    location_json: Optional[Dict[str, Any]] = {}
    metadata_json: Optional[Dict[str, Any]] = {}


class RouteCreate(BaseModel):
    company_id: Optional[str] = None
    name: str
    route_type: str
    waypoints: Optional[List[Dict[str, Any]]] = []
    vehicle_asset_id: Optional[str] = None
    driver_person_id: Optional[str] = None
    schedule_json: Optional[Dict[str, Any]] = {}
    estimated_duration_min: Optional[int] = None
