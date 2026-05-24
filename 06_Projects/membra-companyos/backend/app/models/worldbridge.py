"""MEMBRA CompanyOS — WorldBridge asset, listing, reservation, proof, vendor, person, route models."""
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, JSON, Numeric, Integer, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base, GUID


class AssetType(PyEnum):
    APARTMENT = "apartment"
    VEHICLE = "vehicle"
    WINDOW = "window"
    WEARABLE = "wearable"
    TOOL = "tool"
    STORAGE = "storage"
    PICKUP_NODE = "pickup_node"
    MICRO_WAREHOUSE = "micro_warehouse"
    SURFACE = "surface"
    DEVICE = "device"
    ROUTE = "route"


class AssetStatus(PyEnum):
    UNREGISTERED = "unregistered"
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class WorldAsset(Base):
    __tablename__ = "world_assets"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=True)
    owner_wallet = Column(String(42), nullable=False, index=True)
    asset_type = Column(Enum(AssetType), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(AssetStatus), default=AssetStatus.UNREGISTERED)
    location_json = Column(JSON, default=dict)
    attributes = Column(JSON, default=dict)
    media_cids = Column(JSON, default=list)
    proof_hash = Column(String(64), nullable=True)
    kpi_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    listings = relationship("AssetListing", back_populates="asset", cascade="all, delete-orphan")
    reservations = relationship("AssetReservation", back_populates="asset", cascade="all, delete-orphan")
    proofs = relationship("AssetProof", back_populates="asset", cascade="all, delete-orphan")


class AssetListing(Base):
    __tablename__ = "asset_listings"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    asset_id = Column(GUID(), ForeignKey("world_assets.id"), nullable=False)
    listing_type = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(20, 6), nullable=True)
    currency = Column(String(3), default="USD")
    visibility = Column(String(32), default="private")
    owner_consent = Column(Boolean, default=False)
    governance_approved = Column(Boolean, default=False)
    status = Column(String(32), default="draft")
    metrics = Column(JSON, default=dict)
    published_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    asset = relationship("WorldAsset", back_populates="listings")


class AssetReservation(Base):
    __tablename__ = "asset_reservations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    asset_id = Column(GUID(), ForeignKey("world_assets.id"), nullable=False)
    reserved_by = Column(GUID(), ForeignKey("users.id"), nullable=True)
    reservation_type = Column(String(64), nullable=False)
    status = Column(String(32), default="pending")
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    cost = Column(Numeric(20, 6), default=0)
    proof_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    asset = relationship("WorldAsset", back_populates="reservations")


class AssetProof(Base):
    __tablename__ = "asset_proofs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    asset_id = Column(GUID(), ForeignKey("world_assets.id"), nullable=False)
    proof_type = Column(String(64), nullable=False)
    proof_data = Column(JSON, default=dict)
    ipfs_cid = Column(String(64), nullable=True)
    verification_status = Column(String(32), default="pending")
    proof_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    asset = relationship("WorldAsset", back_populates="proofs")


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=True)
    name = Column(String(255), nullable=False)
    vendor_type = Column(String(64), nullable=False)
    contact_json = Column(JSON, default=dict)
    wallet_address = Column(String(42), nullable=True)
    service_areas = Column(JSON, default=list)
    rating = Column(Numeric(3, 2), default=0)
    review_count = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Person(Base):
    __tablename__ = "people"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    wallet_address = Column(String(42), nullable=True, index=True)
    display_name = Column(String(255), nullable=True)
    skills = Column(JSON, default=list)
    availability_json = Column(JSON, default=dict)
    location_json = Column(JSON, default=dict)
    reputation_score = Column(Numeric(5, 2), default=0)
    task_completed_count = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Route(Base):
    __tablename__ = "routes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=True)
    name = Column(String(255), nullable=False)
    route_type = Column(String(64), nullable=False)
    waypoints = Column(JSON, default=list)
    vehicle_asset_id = Column(GUID(), ForeignKey("world_assets.id"), nullable=True)
    driver_person_id = Column(GUID(), ForeignKey("people.id"), nullable=True)
    schedule_json = Column(JSON, default=dict)
    estimated_duration_min = Column(Integer, nullable=True)
    status = Column(String(32), default="planned")
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
