import React, { useState, useEffect } from "react";
import { 
  FaLink, FaShieldAlt, FaCheckCircle, FaLock, FaKey, 
  FaCube, FaSearch, FaHistory, FaQrcode, FaCheck, FaTimes, FaExternalLinkAlt, FaPlus 
} from "react-icons/fa";
import { fetchVerifiableRecords, fetchLedgerStatus, verifyRecord, anchorRecord } from "../services/verifiableAiApi";
import toast from "react-hot-toast";

export default function VerifiableAiPage({ setView, activeProjectId = "aiforge-fooddelivery-ai" }) {
  const [records, setRecords] = useState([]);
  const [ledgerStatus, setLedgerStatus] = useState(null);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [verificationResult, setVerificationResult] = useState(null);
  const [loading, setLoading] = useState(true);

  // New Anchor Modal
  const [newTitle, setNewTitle] = useState("");
  const [newEntityId, setNewEntityId] = useState("");
  const [newType, setNewType] = useState("AI_DECISION");
  const [newSigner, setNewSigner] = useState("agent_verifier");
  const [isAnchoring, setIsAnchoring] = useState(false);

  const loadData = async () => {
    try {
      const [recs, status] = await Promise.all([
        fetchVerifiableRecords(),
        fetchLedgerStatus()
      ]);
      setRecords(recs || []);
      setLedgerStatus(status);
      if (recs && recs.length > 0 && !selectedRecord) {
        handleSelectRecord(recs[0]);
      }
    } catch (err) {
      console.error("Error loading verifiable records:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeProjectId]);

  const handleSelectRecord = async (rec) => {
    setSelectedRecord(rec);
    setVerificationResult(null);
  };

  const handleVerify = async (recordId) => {
    toast("Checking SHA-256 Canonical Hash & Ed25519 Signature on Ledger...", { icon: "⛓️" });
    try {
      const res = await verifyRecord(recordId);
      setVerificationResult(res);
      if (res.valid) {
        toast.success("Cryptographic Integrity & Signature Verified on Immutable Ledger!", { icon: "✓" });
      } else {
        toast.error("Tampering Detected! Cryptographic signature mismatch.");
      }
    } catch (err) {
      toast.error("Verification check failed");
    }
  };

  const handleCreateAnchor = async (e) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    setIsAnchoring(true);
    toast("Computing SHA-256 Hash & Anchoring into Verifiable Ledger Block...", { icon: "🔗" });
    try {
      const rec = await anchorRecord({
        title: newTitle.trim(),
        entity_id: newEntityId.trim() || `entity_${Date.now()}`,
        recordType: newType,
        signerId: newSigner
      });
      setRecords([rec, ...records]);
      setSelectedRecord(rec);
      setNewTitle("");
      setNewEntityId("");
      toast.success("Record Anchored & Signed Successfully!", { icon: "✓" });
    } catch (err) {
      toast.error("Anchoring failed");
    } finally {
      setIsAnchoring(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#0B0F19] text-[#F5F7FA] font-sans overflow-hidden">
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-4 bg-[#0F172A] border-b border-gray-800 text-xs">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-amber-500 via-orange-600 to-rose-600 text-white shadow-lg shadow-amber-500/20">
            <FaLink size={18} />
          </div>
          <div>
            <h1 className="text-base font-bold text-white flex items-center gap-2">
              Blockchain Trust & Verifiable AI Layer
              <span className="px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-mono text-[10px] font-bold">
                Cryptographic Integrity Engine
              </span>
            </h1>
            <p className="text-xs text-gray-400">
              Deterministic SHA-256 Canonical Hashing, Digital Signatures, Merkle Batching & Immutable Ledger Anchoring
            </p>
          </div>
        </div>

        {/* Global Ledger State */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="px-3 py-1.5 bg-[#151821] border border-gray-800 rounded-xl text-emerald-400 font-bold flex items-center gap-1.5">
            <FaCube size={11} /> Block #{ledgerStatus?.latest_block_number || 19482115}
          </span>
          <span className="px-3 py-1.5 bg-[#151821] border border-gray-800 rounded-xl text-amber-300 font-bold">
            {records.length} Anchored Records
          </span>
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Ledger Record Feed (55%) */}
        <div className="flex-1 bg-[#0B0F19] overflow-y-auto p-6 space-y-6 custom-scrollbar border-r border-[#242833]">
          {/* Quick Anchor Generator */}
          <form onSubmit={handleCreateAnchor} className="p-5 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-3 shadow-xl text-xs">
            <span className="text-[10px] font-mono text-amber-400 uppercase font-bold flex items-center gap-1.5">
              <FaPlus size={10} /> Anchor & Sign New AI Decision / Finding
            </span>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <input
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Title e.g. Architecture Security Review Approval"
                className="bg-[#08090D] border border-[#242833] focus:border-amber-500 rounded-xl p-3 text-xs text-white outline-none"
                required
              />
              <input
                type="text"
                value={newEntityId}
                onChange={(e) => setNewEntityId(e.target.value)}
                placeholder="Entity ID e.g. inc_auth_spray_01 or RFC-104"
                className="bg-[#08090D] border border-[#242833] focus:border-amber-500 rounded-xl p-3 text-xs text-white outline-none"
              />
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
              <div className="flex items-center gap-3">
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value)}
                  className="bg-[#08090D] border border-[#242833] text-gray-300 rounded-lg px-2.5 py-1.5 text-xs outline-none cursor-pointer"
                >
                  <option value="AI_DECISION">AI Decision</option>
                  <option value="AGENT_ACTION">Agent Action</option>
                  <option value="SECURITY_INCIDENT">Security Incident</option>
                  <option value="DOCUMENT_PROVENANCE">Document Provenance</option>
                </select>

                <select
                  value={newSigner}
                  onChange={(e) => setNewSigner(e.target.value)}
                  className="bg-[#08090D] border border-[#242833] text-gray-300 rounded-lg px-2.5 py-1.5 text-xs outline-none cursor-pointer"
                >
                  <option value="agent_verifier">Consensus Verification Judge</option>
                  <option value="agent_security_auditor">Defensive Security Agent</option>
                  <option value="agent_coder">Lead Coding Agent</option>
                  <option value="agent_document_writer">Technical Document Agent</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={isAnchoring || !newTitle.trim()}
                className="px-4 py-2 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 disabled:bg-gray-800 text-white rounded-xl font-bold transition shadow cursor-pointer text-xs"
              >
                {isAnchoring ? "Anchoring..." : "Anchor to Ledger"}
              </button>
            </div>
          </form>

          {/* Record Feed */}
          <div className="space-y-3">
            <span className="text-[10px] font-mono text-gray-400 uppercase font-bold block">
              Immutable Provenance Log ({records.length})
            </span>
            <div className="space-y-3">
              {records.map((rec) => (
                <div
                  key={rec.id}
                  onClick={() => handleSelectRecord(rec)}
                  className={`p-4 rounded-2xl cursor-pointer transition space-y-2 ${
                    selectedRecord?.id === rec.id
                      ? "bg-[#1E1712] border border-amber-500 shadow-xl"
                      : "bg-[#0F1117] hover:bg-[#151821] border border-[#242833]"
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] font-mono">
                    <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold">
                      {rec.record_type}
                    </span>
                    <span className="text-emerald-400 font-bold flex items-center gap-1">
                      <FaCheckCircle size={10} /> {rec.verification_status} (Block #{rec.block_number})
                    </span>
                  </div>

                  <h3 className="font-bold text-xs text-white">{rec.title}</h3>
                  <div className="flex items-center justify-between text-[10px] font-mono text-gray-500">
                    <span className="truncate max-w-xs">Hash: {rec.content_hash.slice(0, 24)}...</span>
                    <span>Signer: {rec.signer_id}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Side: Verification Certificate Inspector (45%) */}
        <div className="w-[480px] bg-[#0F1117] overflow-y-auto p-6 space-y-6 custom-scrollbar">
          {selectedRecord ? (
            <div className="space-y-5">
              <div className="space-y-1.5 pb-4 border-b border-[#1C202B]">
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono text-[10px] font-bold">
                    {selectedRecord.id}
                  </span>
                  <button
                    onClick={() => handleVerify(selectedRecord.id)}
                    className="px-3 py-1.5 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white rounded-xl text-xs font-bold transition shadow cursor-pointer flex items-center gap-1.5"
                  >
                    <FaCheckCircle size={11} /> Verify Integrity
                  </button>
                </div>
                <h2 className="text-base font-bold text-white">{selectedRecord.title}</h2>
              </div>

              {/* Cryptographic Certificate Details */}
              <div className="space-y-3">
                <span className="text-[10px] font-mono text-amber-400 uppercase font-bold block">
                  Cryptographic Provenance Certificate
                </span>

                <div className="p-4 rounded-2xl bg-[#08090D] border border-[#1C202B] space-y-3 text-xs font-mono">
                  <div>
                    <span className="text-[10px] text-gray-500 block">CANONICAL SHA-256 CONTENT HASH:</span>
                    <span className="text-amber-300 text-[11px] break-all block mt-0.5">{selectedRecord.content_hash}</span>
                  </div>

                  <div>
                    <span className="text-[10px] text-gray-500 block">ED25519 DIGITAL SIGNATURE:</span>
                    <span className="text-cyan-300 text-[11px] break-all block mt-0.5">{selectedRecord.signature}</span>
                  </div>

                  <div>
                    <span className="text-[10px] text-gray-500 block">IMMUTABLE LEDGER TRANSACTION:</span>
                    <span className="text-purple-300 text-[11px] break-all block mt-0.5">{selectedRecord.ledger_reference}</span>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-[#1C202B] text-[10px]">
                    <span className="text-gray-400">Signer Identity:</span>
                    <span className="text-white font-bold">{selectedRecord.signer_id}</span>
                  </div>
                </div>
              </div>

              {/* Interactive Verification Outcome Banner */}
              {verificationResult && (
                <div className={`p-4 rounded-2xl border text-xs space-y-2 animate-fade-in ${
                  verificationResult.valid
                    ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-300"
                    : "bg-rose-950/40 border-rose-500/40 text-rose-300"
                }`}>
                  <div className="flex items-center gap-2 font-bold font-mono text-xs">
                    {verificationResult.valid ? <FaCheckCircle size={14} /> : <FaTimes size={14} />}
                    <span>{verificationResult.trust_status}</span>
                  </div>
                  <p className="text-[11px] text-gray-300 leading-relaxed font-sans">
                    {verificationResult.valid
                      ? "The digital signature strictly matches the canonical SHA-256 payload and block anchor on the immutable verifiable ledger. Zero tampering detected."
                      : "Warning: Payload content hash does not correspond with the ledger anchor signature."}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500 text-xs">
              Select a verifiable record to inspect cryptographic certificate
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
