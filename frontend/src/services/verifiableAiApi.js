/**
 * Verifiable records: a local hash-chained log with HMAC-SHA256 signatures (no external blockchain).
 * Every call goes to the backend with the user's token; a failed call rejects (services/api.js) - nothing is
 * filled in locally, so the page never shows records, verifications or ledger state that do not exist.
 */
import api from './api';

export async function fetchVerifiableRecords() {
  const res = await api.get('/api/verification/records');
  return res?.records || [];
}

export async function fetchLedgerStatus() {
  const res = await api.get('/api/verification/ledger/status');
  return res?.status || null;
}

export async function verifyRecord(recordId) {
  const res = await api.post(`/api/verification/records/${encodeURIComponent(recordId)}/verify`, {});
  return res?.verification;
}

export async function anchorRecord({ title, entityId, recordType = "AI_DECISION", contentPayload = "", signerId = "agent_verifier" }) {
  const res = await api.post('/api/verification/records/anchor', {
    title,
    entity_id: entityId,
    record_type: recordType,
    content_payload: contentPayload,
    signer_id: signerId
  });
  return res?.record;
}
