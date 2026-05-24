"""MEMBRA Mobile Demo Shell — owner-side proof app simulator.

This Hugging Face/Gradio shell represents the mobile app flows before Expo/React Native implementation:
onboard owner, register surface/asset, submit proof, scan QR/NFC, request relay, and view wallet readiness.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sqlite3
import uuid
from pathlib import Path
from typing import Any

import gradio as gr
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

APP_NAME = "MEMBRA Mobile Shell"
DB_PATH = Path(os.getenv("APP_DB_PATH", "/tmp/membra_mobile.sqlite3"))
API_BASE_URL = os.getenv("MEMBRA_API_BASE_URL", "")
api = FastAPI(title=APP_NAME, version="1.0.0")

class OwnerAction(BaseModel):
    owner_email: str
    action_type: str
    subject_type: str
    subject_id: str = ""
    evidence_url: str = ""
    notes: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS mobile_events(
          event_id TEXT PRIMARY KEY,
          owner_email TEXT,
          action_type TEXT,
          subject_type TEXT,
          subject_id TEXT,
          evidence_url TEXT,
          notes TEXT,
          metadata_json TEXT,
          event_hash TEXT,
          status TEXT,
          created_at TEXT
        );
        """)

init_db()


def hash_event(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def record_action(data: OwnerAction) -> dict[str, Any]:
    event_id = new_id("mob")
    payload = data.model_dump() | {"event_id": event_id, "created_at": now()}
    row = {
        "event_id": event_id,
        "owner_email": data.owner_email,
        "action_type": data.action_type,
        "subject_type": data.subject_type,
        "subject_id": data.subject_id,
        "evidence_url": data.evidence_url,
        "notes": data.notes,
        "metadata_json": json.dumps(data.metadata, default=str),
        "event_hash": hash_event(payload),
        "status": "captured_pending_sync" if API_BASE_URL else "captured_local_demo",
        "created_at": payload["created_at"],
    }
    with db() as conn:
        conn.execute("INSERT INTO mobile_events VALUES(?,?,?,?,?,?,?,?,?,?,?)", tuple(row.values()))
    return row


def events() -> list[dict[str, Any]]:
    with db() as conn:
        rows = conn.execute("SELECT * FROM mobile_events ORDER BY created_at DESC LIMIT 250").fetchall()
    return [dict(r) for r in rows]

@api.get("/api/health")
def health():
    return {"ok": True, "app": APP_NAME, "api_base_configured": bool(API_BASE_URL)}

@api.post("/api/mobile-events")
def create_event(data: OwnerAction):
    return record_action(data)

@api.get("/api/mobile-events")
def list_events():
    return {"mobile_events": events()}


def ui_record(email, action, subject_type, subject_id, evidence_url, notes, metadata_json):
    try:
        metadata = json.loads(metadata_json or "{}")
        out = record_action(OwnerAction(owner_email=email, action_type=action, subject_type=subject_type, subject_id=subject_id, evidence_url=evidence_url, notes=notes, metadata=metadata))
        return out, events()
    except Exception as exc:
        return {"error": str(exc)}, events()

with gr.Blocks(title=APP_NAME) as demo:
    gr.Markdown("# MEMBRA Mobile Shell\nOwner-side proof app simulator: register assets, accept campaigns, confirm media kits, submit proof, scan QR/NFC, request relay, and check wallet readiness.")
    email = gr.Textbox(label="Owner email")
    action = gr.Dropdown(["owner_onboarded", "asset_registered", "campaign_offer_viewed", "campaign_accepted", "media_kit_received", "proof_photo_submitted", "qr_test_scan", "relay_requested", "claim_submitted", "wallet_readiness_checked"], value="asset_registered", label="Mobile action")
    subject_type = gr.Dropdown(["owner", "asset", "campaign", "wear_kit", "relay_job", "artifact", "wallet"], value="asset", label="Subject type")
    subject_id = gr.Textbox(label="Subject ID")
    evidence_url = gr.Textbox(label="Evidence URL")
    notes = gr.Textbox(label="Notes", lines=3)
    metadata = gr.Code(label="Metadata JSON", language="json", value="{}")
    button = gr.Button("Capture mobile event", variant="primary")
    out = gr.JSON(label="Captured event")
    table = gr.Dataframe(label="Mobile event log", value=events, interactive=False)
    button.click(ui_record, [email, action, subject_type, subject_id, evidence_url, notes, metadata], [out, table])
    gr.Markdown("Production next step: replace this shell with Expo/React Native screens that call `Membra_api`, `Membra_proofbook`, `Membra_wallet`, and `membra-qr-gateway`.")

app = gr.mount_gradio_app(api, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "7860")))
