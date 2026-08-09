import React, { useState } from 'react';
import { FaKey, FaCheckCircle, FaExclamationTriangle, FaPlus, FaCheck } from 'react-icons/fa';

export default function EnvironmentVariables({ envVars = [], onValidate }) {
  const [vars, setVars] = useState(envVars);
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [showAdd, setShowAdd] = useState(false);

  const handleAdd = () => {
    if (!newKey) return;
    setVars([...vars, { name: newKey, value: '••••••••••••••••', status: 'VALID' }]);
    setNewKey('');
    setNewValue('');
    setShowAdd(false);
  };

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <FaKey className="text-amber-400" /> Environment Variables & Vault Config
        </h3>

        <div className="flex items-center gap-2">
          <button
            onClick={onValidate}
            className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-cyan-400 hover:text-white rounded-lg text-xs font-bold transition flex items-center gap-1"
          >
            <FaCheck className="w-3 h-3" /> Validate Configuration
          </button>

          <button
            onClick={() => setShowAdd(!showAdd)}
            className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold transition flex items-center gap-1"
          >
            <FaPlus className="w-3 h-3" /> Add Variable
          </button>
        </div>
      </div>

      {showAdd && (
        <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl mb-4 flex gap-2">
          <input
            type="text"
            placeholder="KEY_NAME"
            value={newKey}
            onChange={(e) => setNewKey(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-xs text-white uppercase font-mono flex-1"
          />
          <input
            type="password"
            placeholder="Secret Value"
            value={newValue}
            onChange={(e) => setNewValue(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-xs text-white font-mono flex-1"
          />
          <button
            onClick={handleAdd}
            className="px-4 py-1.5 bg-emerald-600 text-white font-bold text-xs rounded hover:bg-emerald-500 transition"
          >
            Save
          </button>
        </div>
      )}

      {/* Variables List */}
      <div className="space-y-2 font-mono text-xs">
        {vars.map((v, idx) => (
          <div key={idx} className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-between">
            <span className="font-bold text-white tracking-wide">{v.name}</span>
            <div className="flex items-center gap-4">
              <span className="text-slate-500 text-xs">••••••••••••••••</span>
              <span className="text-emerald-400 text-[11px] font-sans flex items-center gap-1">
                <FaCheckCircle className="w-3 h-3" /> {v.status || 'VALID'}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
