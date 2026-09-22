import React, { useState, useEffect } from 'react';
import { fetchApiKeys, createApiKey, revokeApiKey } from '../services/auth';
import { FaKey, FaPlus, FaTrash, FaCopy, FaCheck, FaSpinner, FaExclamationTriangle } from 'react-icons/fa';

export default function ApiKeys() {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [keyName, setKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState(null);
  const [copied, setCopied] = useState(false);
  const [creating, setCreating] = useState(false);

  const loadKeys = async () => {
    setLoading(true);
    const data = await fetchApiKeys();
    setKeys(data);
    setLoading(false);
  };

  useEffect(() => {
    loadKeys();
  }, []);

  const handleCreateKey = async () => {
    if (!keyName) return;
    setCreating(true);
    try {
      const res = await createApiKey(keyName);
      setCreatedKey(res.raw_key);
      setKeyName('');
      loadKeys();
    } catch (err) {
      console.error(err);
    } finally {
      setCreating(false);
    }
  };

  const handleCopyKey = () => {
    if (createdKey) {
      navigator.clipboard.writeText(createdKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  const handleRevoke = async (keyId) => {
    await revokeApiKey(keyId);
    loadKeys();
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6 selection:bg-cyan-500 selection:text-white">
      <div className="max-w-4xl mx-auto border-b border-slate-800 pb-4">
        <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
          <FaKey className="text-amber-400" /> AIForge API Keys
        </h1>
        <p className="text-xs text-slate-400 mt-1">Use API keys to securely integrate AIForge multi-agent workflows into external applications.</p>
      </div>

      <div className="max-w-4xl mx-auto space-y-6">
        {/* Create API Key Box */}
        <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl space-y-4 font-sans">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">Create New API Key</h3>
          <div className="flex gap-3">
            <input
              type="text"
              value={keyName}
              onChange={(e) => setKeyName(e.target.value)}
              placeholder="e.g. CI/CD Integration Pipeline Key"
              className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-cyan-500"
            />
            <button
              onClick={handleCreateKey}
              disabled={creating || !keyName}
              className="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-cyan-500/20 flex items-center gap-1.5 disabled:opacity-50 shrink-0"
            >
              {creating ? <FaSpinner className="animate-spin" /> : <FaPlus />}
              <span>{creating ? 'Generating...' : 'Create API Key'}</span>
            </button>
          </div>
        </div>

        {/* Display Once Banner for newly generated key */}
        {createdKey && (
          <div className="bg-gradient-to-tr from-emerald-950 via-slate-950 to-slate-950 border border-emerald-500/40 rounded-2xl p-6 shadow-2xl space-y-3 font-sans">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
              <FaCheck /> API Key Generated Successfully
            </div>
            <p className="text-xs text-slate-300">
              Please copy your key now. For your security, this plaintext key will <strong>never be displayed again</strong>.
            </p>
            <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 p-3 rounded-xl font-mono text-xs text-cyan-300 justify-between">
              <span>{createdKey}</span>
              <button
                onClick={handleCopyKey}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 font-sans shrink-0"
              >
                {copied ? <FaCheck /> : <FaCopy />}
                <span>{copied ? 'Copied!' : 'Copy Key'}</span>
              </button>
            </div>
          </div>
        )}

        {/* Keys Table */}
        <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans space-y-4">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-3">Active API Keys</h3>

          {loading ? (
            <div className="py-8 text-center text-xs text-slate-500">Loading API keys...</div>
          ) : keys.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500 italic">No API keys created yet.</div>
          ) : (
            <div className="space-y-2">
              {keys.map((k) => (
                <div key={k.id} className="p-3.5 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-between font-mono text-xs">
                  <div>
                    <h4 className="font-bold text-white font-sans text-xs">{k.name}</h4>
                    <span className="text-slate-500 text-[11px]">{k.key_preview} • Created {k.created_at}</span>
                  </div>
                  <button
                    onClick={() => handleRevoke(k.id)}
                    className="p-2 bg-slate-900 hover:bg-rose-950 text-rose-400 rounded-lg border border-slate-800 hover:border-rose-500/40 transition"
                  >
                    <FaTrash className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
