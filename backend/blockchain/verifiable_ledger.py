"""
AIForge verifiable records: a local, tamper-evident, hash-chained log.

What it is: every record stores the SHA-256 of its canonical content, the hash of the record before it (a chain), and
an HMAC-SHA256 signature made with this installation's secret key (AIFORGE_LEDGER_SIGNING_KEY, or a random key
generated on first use and kept in the data folder - never in the source). verify_record_integrity re-checks a
record's signature and its link to the previous record; get_ledger_status walks the whole chain.

What it is not: a blockchain. Nothing is anchored to an external ledger, so "block_number" is the record's position in
the local chain and "ledger_reference" is a local reference. Records signed with the old key that used to be
published in this file are reported as such - their integrity cannot be trusted.
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.blockchain.verifiable_ledger")
GENESIS = "0" * 64
SIG_PREFIX = "hmac_sha256_"
LEGACY_PREFIX = "sig_ed25519_"
_LEGACY_KEY = b"aiforge_zero_trust_master_signing_key_2026"     # was hardcoded here; only used to recognise old records
_INVENTED_SEED_IDS = {"vrec_sec_01", "vrec_agent_02", "vrec_doc_03"}   # demo records that described events that never happened


class RecordType(str, Enum):
    AI_DECISION = "AI_DECISION"
    AGENT_ACTION = "AGENT_ACTION"
    SECURITY_EVENT = "SECURITY_EVENT"
    SECURITY_INCIDENT = "SECURITY_INCIDENT"
    KNOWLEDGE_UPDATE = "KNOWLEDGE_UPDATE"
    DOCUMENT_PROVENANCE = "DOCUMENT_PROVENANCE"
    AUDIT_EVENT = "AUDIT_EVENT"
    VERIFICATION_RESULT = "VERIFICATION_RESULT"


class VerificationStatus(str, Enum):
    ANCHORED = "ANCHORED"          # legacy value of old records
    RECORDED = "RECORDED"          # appended to the local chain
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


class VerifiableRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"vrec_{uuid.uuid4().hex[:8]}")
    record_type: RecordType = RecordType.AI_DECISION
    entity_id: str
    title: str
    content_hash: str
    previous_hash: str = GENESIS
    signature: str
    signer_id: str = "agent_verifier"
    timestamp: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    metadata_hash: str = ""
    ledger_reference: str = ""                 # "local-chain:<position>": there is no external ledger
    verification_status: VerificationStatus = VerificationStatus.RECORDED
    block_number: int = 0                      # the record's position in the local chain (1-based)
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


def _signing_key(storage_dir: Path) -> bytes:
    env = os.environ.get("AIFORGE_LEDGER_SIGNING_KEY", "").strip()
    if env:
        return env.encode("utf-8")
    key_file = storage_dir / "signing.key"
    try:
        if key_file.is_file():
            return key_file.read_bytes().strip()
        key = secrets.token_hex(32).encode("ascii")
        key_file.write_bytes(key)
        try:
            os.chmod(key_file, 0o600)
        except OSError:
            pass
        return key
    except OSError as e:  # noqa: PERF203 - an unwritable folder still gets a (per-process) secret key
        _logger.warning("ledger signing key could not be stored (%s); using a per-process key", e)
        return secrets.token_hex(32).encode("ascii")


class CryptographicEngine:
    """SHA-256 canonical hashing and HMAC-SHA256 signatures (with a key that is not in the source)."""

    def __init__(self, key: bytes):
        self._key = key

    @staticmethod
    def canonical_hash(data: Any) -> str:
        if isinstance(data, dict):
            serialized = json.dumps(data, sort_keys=True, separators=(',', ':'))
        elif isinstance(data, str):
            serialized = data
        else:
            serialized = str(data)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def sign_hash(self, content_hash: str, signer_id: str) -> str:
        sig = hmac.new(self._key, f"{signer_id}:{content_hash}".encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{SIG_PREFIX}{sig}"

    def verify_signature(self, content_hash: str, signature: str, signer_id: str) -> str:
        """'valid' | 'legacy_key' (signed with the old published key: not trustworthy) | 'invalid'."""
        if signature.startswith(SIG_PREFIX):
            return "valid" if hmac.compare_digest(self.sign_hash(content_hash, signer_id), signature) else "invalid"
        if signature.startswith(LEGACY_PREFIX):
            legacy = hmac.new(_LEGACY_KEY, f"{signer_id}:{content_hash}".encode("utf-8"), hashlib.sha256).hexdigest()
            return "legacy_key" if hmac.compare_digest(f"{LEGACY_PREFIX}{legacy[:32]}", signature) else "invalid"
        return "invalid"


class VerifiableLedgerService:
    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir) if storage_dir else Path(__file__).resolve().parent.parent / "data" / "verifiable_ledger"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.records_file = self.storage_dir / "verifiable_records.json"
        self.crypto = CryptographicEngine(_signing_key(self.storage_dir))
        self._records: Dict[str, VerifiableRecord] = {}
        self._load()

    def _load(self):
        if not self.records_file.exists():
            return
        try:
            data = json.loads(self.records_file.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            _logger.error("verifiable records could not be read: %s", e)
            return
        for item in data:
            if item.get("id") in _INVENTED_SEED_IDS:
                continue
            try:
                rec = VerifiableRecord(**item)
            except Exception as e:  # noqa: BLE001 - a malformed record is skipped and reported, not repaired
                _logger.error("skipping malformed verifiable record %s: %s", item.get("id"), e)
                continue
            self._records[rec.id] = rec

    def _save(self):
        try:
            tmp = self.records_file.with_suffix(".tmp")
            tmp.write_text(json.dumps([r.model_dump(mode="json") for r in self._chain()], indent=2), encoding="utf-8")
            os.replace(tmp, self.records_file)
        except OSError as e:
            _logger.error("Error saving verifiable records: %s", e)

    def _chain(self) -> List[VerifiableRecord]:
        """Records in the order they were appended."""
        return sorted(self._records.values(), key=lambda r: (r.block_number, r.created_at))

    def list_records(self) -> List[VerifiableRecord]:
        return list(reversed(self._chain()))

    def get_record(self, record_id: str) -> Optional[VerifiableRecord]:
        return self._records.get(record_id)

    def create_and_anchor_record(
        self,
        title: str,
        entity_id: str,
        record_type: RecordType = RecordType.AI_DECISION,
        content_payload: Any = "",
        signer_id: str = "agent_verifier"
    ) -> VerifiableRecord:
        """Append a signed record to the local chain (no external anchoring exists)."""
        content_hash = self.crypto.canonical_hash(content_payload)
        chain = self._chain()
        position = (chain[-1].block_number if chain else 0) + 1
        rec = VerifiableRecord(
            record_type=record_type, entity_id=entity_id, title=title, content_hash=content_hash,
            previous_hash=chain[-1].content_hash if chain else GENESIS,
            signature=self.crypto.sign_hash(content_hash, signer_id), signer_id=signer_id,
            ledger_reference=f"local-chain:{position}", verification_status=VerificationStatus.RECORDED,
            block_number=position,
        )
        self._records[rec.id] = rec
        self._save()
        return rec

    def _link_ok(self, rec: VerifiableRecord) -> bool:
        chain = self._chain()
        i = chain.index(rec)
        return rec.previous_hash == (chain[i - 1].content_hash if i else GENESIS)

    def verify_record_integrity(self, record_id: str) -> Dict[str, Any]:
        rec = self.get_record(record_id)
        if not rec:
            return {"valid": False, "message": "Record not found"}
        sig = self.crypto.verify_signature(rec.content_hash, rec.signature, rec.signer_id)
        link = self._link_ok(rec)
        valid = sig == "valid" and link
        trust = ("VERIFIED_LOCAL_HASH_CHAIN" if valid else
                 "UNTRUSTED_LEGACY_KEY" if sig == "legacy_key" else
                 "TAMPER_DETECTED" if sig == "invalid" else "CHAIN_BROKEN")
        return {
            "valid": valid, "record_id": rec.id, "entity_id": rec.entity_id, "content_hash": rec.content_hash,
            "signature_valid": sig == "valid", "signature_check": sig, "chain_link_valid": link,
            "signer_identity": rec.signer_id, "ledger_anchor": rec.ledger_reference, "block_number": rec.block_number,
            "timestamp": rec.timestamp, "trust_status": trust,
            "note": "Local hash chain with HMAC signatures; no external blockchain anchoring.",
        }

    def get_ledger_status(self) -> Dict[str, Any]:
        chain = self._chain()
        broken = [r.id for i, r in enumerate(chain) if r.previous_hash != (chain[i - 1].content_hash if i else GENESIS)]
        bad_sig = [r.id for r in chain if self.crypto.verify_signature(r.content_hash, r.signature, r.signer_id) != "valid"]
        return {
            "ledger_provider": "Local hash-chained log (HMAC-SHA256 signatures; no external blockchain)",
            "network_status": "LOCAL",
            "total_anchored_records": len(chain),
            "latest_block_number": chain[-1].block_number if chain else 0,
            "integrity_chain_valid": not broken and not bad_sig,
            "broken_links": broken,
            "records_failing_signature_check": bad_sig,
            "consensus_mechanism": "None (single local writer)",
        }


global_verifiable_ledger = VerifiableLedgerService()
