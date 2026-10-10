import { BACKEND_URL } from '../../config/backend';
import React, { useState, useEffect } from 'react';
import {
  FaClipboardList,
  FaCheckCircle,
  FaExclamationTriangle,
  FaFileCode,
  FaVial,
  FaShieldAlt,
  FaUsers,
  FaCodeBranch,
  FaSearch,
  FaPlusCircle
} from 'react-icons/fa';
import axios from 'axios';

const API_BASE = `${BACKEND_URL}`;

export default function ProductSpecPanel({ generationId = 'TodoApp', onClose, onSelectFile }) {
  const [spec, setSpec] = useState(null);
  const [selectedReq, setSelectedReq] = useState(null);
  const [changePrompt, setChangePrompt] = useState('');
  const [changeImpact, setChangeImpact] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchSpecification();
  }, [generationId]);

  const fetchSpecification = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/projects/${generationId}/spec/traceability`);
      setSpec(res.data);
      if (res.data?.functional_requirements?.length > 0) {
        setSelectedReq(res.data.functional_requirements[0]);
      }
    } catch (err) {
      console.error('Fetch spec error:', err);
    }
  };

  const handleAnalyzeChange = async () => {
    if (!changePrompt.trim()) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/api/projects/${generationId}/spec/impact`, {
        change_request: changePrompt
      });
      setChangeImpact(res.data.impact);
      setSpec(res.data.updated_specification);
      setChangePrompt('');
    } catch (err) {
      console.error('Change impact error:', err);
    } finally {
      setLoading(false);
    }
  };

  const allReqs = [
    ...(spec?.functional_requirements || []),
    ...(spec?.security_requirements || []),
    ...(spec?.data_requirements || [])
  ];

  const getTraceabilityForItem = (reqId) => {
    return spec?.traceability_matrix?.find((m) => m.requirement_id === reqId) || {
      implementation_files: [],
      test_files: [],
      status: 'NOT_IMPLEMENTED'
    };
  };

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div className="bg-[#090d16] border border-slate-800 rounded-2xl w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl font-sans text-slate-100 overflow-hidden">
        {/* Header Bar */}
        <div className="px-6 py-4 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-600/30 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
              <FaClipboardList className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Product Specification & Requirements Engine
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Project: <strong className="text-white">{spec?.project_name || generationId}</strong> | Spec Version: <span className="text-cyan-400 font-bold">v{spec?.version || '1.0'}</span>
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-xs font-mono text-slate-400 hover:text-white bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700 transition"
          >
            ✕ Close
          </button>
        </div>

        {/* Top Metric Cards */}
        <div className="grid grid-cols-5 gap-3 p-4 bg-slate-950 border-b border-slate-800 text-xs font-mono">
          <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[10px]">Total Requirements</div>
            <div className="text-lg font-bold text-white mt-0.5">{allReqs.length}</div>
          </div>

          <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[10px]">Coverage Score</div>
            <div className="text-lg font-bold text-cyan-400 mt-0.5">{spec?.coverage_score || 0}%</div>
          </div>

          <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[10px]">User Stories</div>
            <div className="text-lg font-bold text-indigo-400 mt-0.5">{spec?.user_stories?.length || 0}</div>
          </div>

          <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[10px]">Security Controls</div>
            <div className="text-lg font-bold text-emerald-400 mt-0.5">{spec?.security_requirements?.length || 0}</div>
          </div>

          <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[10px]">Open Ambiguities</div>
            <div className="text-lg font-bold text-amber-400 mt-0.5">{spec?.open_questions?.length || 0}</div>
          </div>
        </div>

        {/* 2-Column Explorer */}
        <div className="flex-1 flex min-h-0 overflow-hidden">
          {/* Left Column: Requirements List */}
          <div className="w-1/3 border-r border-slate-800 bg-slate-950 p-3 overflow-y-auto custom-scrollbar space-y-2">
            <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-400 mb-2">
              Requirement Explorer
            </div>

            {allReqs.map((req) => {
              const trace = getTraceabilityForItem(req.id);
              const isSel = selectedReq?.id === req.id;
              return (
                <div
                  key={req.id}
                  onClick={() => setSelectedReq(req)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    isSel
                      ? 'bg-slate-900 border-cyan-500/60 text-white shadow-md'
                      : 'bg-slate-900/50 border-slate-800/80 text-slate-300 hover:bg-slate-900/90'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-xs font-bold text-cyan-400">{req.id}</span>
                    <span
                      className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-bold ${
                        trace.status === 'VERIFIED'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : trace.status === 'IMPLEMENTED'
                          ? 'bg-cyan-500/20 text-cyan-400'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {trace.status}
                    </span>
                  </div>
                  <div className="text-xs font-semibold truncate">{req.title}</div>
                </div>
              );
            })}
          </div>

          {/* Right Column: Requirement Traceability Detail & Change Request Input */}
          <div className="flex-1 p-5 overflow-y-auto custom-scrollbar space-y-5">
            {selectedReq ? (
              <div className="space-y-4">
                {/* Requirement Overview */}
                <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm font-extrabold text-cyan-400">{selectedReq.id} — {selectedReq.title}</span>
                    <span className="text-xs font-mono bg-slate-800 px-2 py-0.5 rounded text-amber-400 font-bold">
                      Priority: {selectedReq.priority}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">{selectedReq.description}</p>
                </div>

                {/* User Story & Acceptance Criteria */}
                <div className="space-y-2">
                  <h4 className="text-xs font-mono font-bold uppercase text-slate-400">User Story & Acceptance Criteria</h4>
                  {spec?.user_stories
                    ?.filter((u) => u.requirement_ids.includes(selectedReq.id))
                    .map((us) => (
                      <div key={us.id} className="p-3 bg-slate-900/60 rounded-lg border border-slate-800 text-xs text-slate-200">
                        <div className="font-mono font-bold text-indigo-400 mb-1">{us.id}</div>
                        <div>As a <strong>{us.as_a}</strong>, I want <strong>{us.i_want}</strong>, so that <strong>{us.so_that}</strong>.</div>
                      </div>
                    ))}
                </div>

                {/* Code & Test Mapping */}
                <div className="space-y-2 font-mono text-xs">
                  <h4 className="font-bold uppercase text-slate-400 text-[11px]">Traceability Mapping</h4>

                  <div className="bg-slate-900 p-3 rounded-lg border border-slate-800 space-y-2">
                    <div className="text-slate-400 text-[11px] flex items-center gap-1.5">
                      <FaFileCode className="text-cyan-400" /> Implementation Files
                    </div>
                    {getTraceabilityForItem(selectedReq.id).implementation_files.length > 0 ? (
                      getTraceabilityForItem(selectedReq.id).implementation_files.map((f, i) => (
                        <div key={i} className="text-cyan-300 hover:underline cursor-pointer" onClick={() => onSelectFile && onSelectFile(f)}>
                          {f}
                        </div>
                      ))
                    ) : (
                      <div className="text-slate-500 italic text-[11px]">No mapped implementation files.</div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-slate-500 italic text-center p-8">Select a requirement from the left panel to inspect details.</div>
            )}

            {/* Incremental Change Request Input */}
            <div className="pt-4 border-t border-slate-800 space-y-3 font-mono">
              <h4 className="text-xs font-bold uppercase text-slate-400 flex items-center gap-1.5">
                <FaPlusCircle className="text-cyan-400" /> Incremental Feature Change Request
              </h4>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="e.g. Add Google OAuth 2.0 Login..."
                  value={changePrompt}
                  onChange={(e) => setChangePrompt(e.target.value)}
                  className="flex-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-100 text-xs focus:outline-none focus:border-cyan-500"
                />
                <button
                  onClick={handleAnalyzeChange}
                  disabled={loading}
                  className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold rounded-lg transition"
                >
                  Analyze Impact
                </button>
              </div>

              {changeImpact && (
                <div className="p-3 bg-cyan-950/30 border border-cyan-800/50 rounded-lg text-xs space-y-1">
                  <div className="font-bold text-cyan-400">Impact Analysis Summary:</div>
                  <div className="text-slate-300">New Requirements: {changeImpact.new_requirements?.map((r) => r.id).join(', ')}</div>
                  <div className="text-slate-300">Affected Files: {changeImpact.affected_files?.join(', ') || 'None'}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
