"""WorldBridge API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.base import get_db
from app.services.worldbridge import WorldBridgeService
from app.schemas.worldbridge import (
    WorldAssetCreate, WorldAssetRead, AssetListingCreate, AssetReservationCreate,
    AssetProofCreate, VendorCreate, PersonCreate, RouteCreate
)
from app.schemas.common import BaseResponse, PaginatedResponse

router = APIRouter()


@router.post("/assets", response_model=BaseResponse)
def register_asset(data: WorldAssetCreate, db: Session = Depends(get_db)):
    svc = WorldBridgeService(db)
    asset = svc.register_asset(data)
    return BaseResponse(data={"id": str(asset.id), "type": asset.asset_type.value, "status": asset.status.value})


@router.get("/assets", response_model=PaginatedResponse)
def list_assets(
    company_id: Optional[str] = None,
    asset_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    svc = WorldBridgeService(db)
    items = svc.list_assets(company_id=company_id, asset_type=asset_type, limit=limit)
    return PaginatedResponse(
        items=[WorldAssetRead.model_validate(a) for a in items],
        total=len(items),
        page=1,
        page_size=limit,
        pages=1,
    )


@router.patch("/assets/{asset_id}/status")
def update_asset_status(asset_id: str, status: str, db: Session = Depends(get_db)):
    svc = WorldBridgeService(db)
    asset = svc.update_asset_status(asset_id, status)
    return BaseResponse(data={"id": str(asset.id), "status": asset.status.value})


@router.post("/listings", response_model=BaseResponse)
def create_listing(data: AssetListingCreate, db: Session = Depends(get_db)):
    svc = WorldBridgeService(db)
    listing = svc.create_listing(data)
    return BaseResponse(data={"id": str(listing.id), "status": listing.status})


@router.post("/listings/{listing_id}/approve", response_model=BaseResponse)
def approve_listing(listing_id: str, db: Session = Depends(get_db)):
    svc = WorldBridgeService(db)
    listing = svc.approve_listing(listing_id)
    return BaseResponse(data={"id": str(listing.id), "status": listing.status})


@router.post("/reservations", response_model=BaseResponse)
def create_reservation(data: AssetReservationCreate, db: Session = Depends(get_db)):
    svc = WorldBridgeService(db)
    res = svc.create_reservation(data)
    return BaseResponse(data={"id": str(res.id), "status": res.status})


@router.post("/proofs", response_model=BaseResponse)
def submit_asset_proof(data: AssetProofCreate, db: Session = Depends(get_db)):
    svc = WorldBridgeService(db)
    proof = svc.submit_asset_proof(data)
    return BaseResponse(data={"id": str(proof.id), "hash": proof.proof_hash})


@router.post("/vendors", response_model=BaseResponse)
def create_vendor(data: VendorCreate, db: Session = Depends(get_db)):
    svc = WorldBridgeService(db)
    vendor = svc.create_vendor(data)
    return BaseResponse(data={"id": str(vendor.id), "name": vendor.name})


@router.post("/people", response_model=BaseResponse)
def create_person(data: PersonCreate, db: Session = Depends(get_db)):
    svc = WorldBridgeService(db)
    person = svc.create_person(data)
    return BaseResponse(data={"id": str(person.id), "name": person.display_name})


@router.post("/routes", response_model=BaseResponse)
def create_route(data: RouteCreate, db: Session = Depends(get_db)):
    svc = WorldBridgeService(db)
    route = svc.create_route(data)
    return BaseResponse(data={"id": str(route.id), "name": route.name})
