"""
AIForge REST API — Phase 5: Blockchain Trust Layer & Verifiable AI
==================================================================
Endpoints:
- GET  /api/verification/records
- GET  /api/verification/records/{record_id}
- POST /api/verification/records/{record_id}/verify
- GET  /api/verification/ledger/status
- POST /api/verification/records/anchor
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from backend.blockchain.verifiable_ledger import global_verifiable_ledger, RecordType

router = APIRouter(prefix="/api/verification", tags=["AIForge Blockchain Trust Layer & Verifiable AI"])


class AnchorRecordPayload(BaseModel):
    title: str
    entity_id: str
    record_type: Optional[str] = "AI_DECISION"
    content_payload: Optional[str] = ""
    signer_id: Optional[str] = "agent_verifier"


@router.get("/records")
def list_verifiable_records():
    records = global_verifiable_ledger.list_records()
    return {
        "success": True,
        "count": len(records),
        "records": [r.model_dump() for r in records]
    }


@router.get("/records/{record_id}")
def get_verifiable_record(record_id: str):
    rec = global_verifiable_ledger.get_record(record_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Verifiable Record '{record_id}' not found")
    return {
        "success": True,
        "record": rec.model_dump()
    }


@router.post("/records/{record_id}/verify")
def verify_record_integrity(record_id: str):
    res = global_verifiable_ledger.verify_record_integrity(record_id)
    if not res.get("valid"):
        raise HTTPException(status_code=400, detail="Cryptographic verification failed or record tampered")
    return {
        "success": True,
        "verification": res
    }


@router.get("/ledger/status")
def get_ledger_status():
    return {
        "success": True,
        "status": global_verifiable_ledger.get_ledger_status()
    }


@router.post("/records/anchor", status_code=status.HTTP_201_CREATED)
def anchor_new_record(payload: AnchorRecordPayload):
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    rec = global_verifiable_ledger.create_and_anchor_record(
        title=payload.title,
        entity_id=payload.entity_id,
        record_type=RecordType(payload.record_type or "AI_DECISION"),
        content_payload=payload.content_payload or payload.title,
        signer_id=payload.signer_id or "agent_verifier"
    )
    return {
        "success": True,
        "record": rec.model_dump()
    }
