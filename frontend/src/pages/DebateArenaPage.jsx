import React, { useState, useEffect } from 'react';
import { FaGavel, FaSpinner, FaTrophy, FaLayerGroup, FaCheckCircle, FaTimesCircle, FaExclamationTriangle, FaFileAlt, FaShieldAlt, FaHistory, FaCheck, FaTimes } from 'react-icons/fa';
import {
  startMultiAgentDebate,
  fetchLatestDebate,
  fetchDebateHistory,
  fetchADRs,
  approveDebateDecision,
  rejectDebateDecision
} from '../services/debate';

export default function DebateArenaPage({ projectId = 'aiforge-demo' }) {
  const [session, setSession] = useState(null);
  const [requirementPrompt, setRequirementPrompt] = useState('Build a highly scalable social platform with authentication, user posts, cart, and payments.');
  const [loading, setLoading] = useState(true);
  const [startingDebate, setStartingDebate] = useState(false);
  const [adrs, setAdrs] = useState([]);
  const [showAdrModal, setShowAdrModal] = useState(false);
  const [selectedAdr, setSelectedAdr] = useState(null);

  useEffect(() => {
    loadSession();
    loadADRs();
  }, [projectId]);

  const loadSession = async () => {
    setLoading(true);
    try {
      const res = await fetchLatestDebate(projectId);
      if (res?.session) setSession(res.session);
    } catch (err) {
      console.warn('Failed to load debate session:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadADRs = async () => {
    try {
      const res = await fetchADRs(projectId);
      if (res?.adrs) setAdrs(res.adrs);
    } catch (err) {
      console.warn('Failed to load ADRs:', err);
    }
  };

  const handleStartDebate = async (e) => {
    e.preventDefault();
    if (!requirementPrompt.trim()) return;

    setStartingDebate(true);
    try {
      const res = await startMultiAgentDebate(projectId, requirementPrompt);
      setSession(res.session);
      await loadADRs();
    } catch (err) {
      alert(`Debate failed: ${err.message}`);
    } finally {
      setStartingDebate(false);
    }
  };

  const handleApprove = async () => {
    if (!session) return;
    try {
      await approveDebateDecision(projectId, session.debate_id);
      await loadSession();
      await loadADRs();
    } catch (err) {
      alert(`Approval failed: ${err.message}`);
    }
  };

  const handleReject = async () => {
    if (!session) return;
    try {
      await rejectDebateDecision(projectId, session.debate_id);
      await loadSession();
      await loadADRs();
    } catch (err) {
      alert(`Rejection failed: ${err.message}`);
    }
  };

  const candidates = session?.candidates || [];
  const decision = session?.decision;
  const winnerId = decision?.winner;
  const scores = decision?.scores || {};
  const adr = decision?.adr;

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6 select-none">
      {/* Top Header */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-amber-600/20 border border-amber-500/40 rounded-xl text-amber-400">
            <FaGavel className="w-7 h-7 animate-bounce" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              ⚖️ Multi-Agent Architecture Debate & Decision Engine
              <span className="text-xs px-2.5 py-0.5 bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded-full font-mono">
                JUDGE & ADR V2
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Independent Competing Proposals, Weighted Scoring Matrix, Minority Tradeoffs & ADR Registry.
            </p>
          </div>
        </div>

        <form onSubmit={handleStartDebate} className="flex gap-2 flex-1 max-w-xl">
          <input
            type="text"
            value={requirementPrompt}
            onChange={(e) => setRequirementPrompt(e.target.value)}
            placeholder="Describe architecture goal..."
            className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono text-white outline-none focus:border-amber-500 transition"
          />
          <button
            type="submit"
            disabled={startingDebate}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold rounded-xl shadow transition flex items-center gap-1.5 shrink-0 disabled:opacity-50"
          >
            {startingDebate ? <FaSpinner className="w-3.5 h-3.5 animate-spin" /> : <FaGavel className="w-3.5 h-3.5" />}
            Trigger Debate
          </button>
        </form>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12 text-slate-400 font-mono text-xs">
          <FaSpinner className="w-5 h-5 animate-spin text-amber-400 mr-2" /> Evaluating competing architectures…
        </div>
      ) : (
        <>
          {/* WINNING DECISION CARD */}
          {decision && (
            <div className="bg-gradient-to-r from-amber-950/40 via-slate-950 to-slate-950 border-2 border-amber-500/60 rounded-2xl p-6 shadow-2xl space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-amber-500/30 pb-4">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-amber-500/20 rounded-xl text-yellow-400 border border-amber-500/40">
                    <FaTrophy className="w-7 h-7" />
                  </div>
                  <div>
                    <span className="text-[10px] font-mono font-bold text-amber-400 uppercase tracking-wider block">
                      🏆 JUDGE AGENT VERDICT — CANDIDATE {decision.winner} WINS
                    </span>
                    <h2 className="text-lg font-extrabold text-white mt-0.5">{decision.winning_proposal_name}</h2>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right font-mono">
                    <span className="text-[10px] text-slate-400 block uppercase">Weighted Score</span>
                    <span className="text-2xl font-extrabold text-amber-400">
                      {scores[winnerId]?.total_weighted_score || 94.0} / 100
                    </span>
                  </div>

                  {adr && (
                    <button
                      onClick={() => { setSelectedAdr(adr); setShowAdrModal(true); }}
                      className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl transition flex items-center gap-1.5 shadow"
                    >
                      <FaFileAlt /> View {adr.adr_id}
                    </button>
                  )}
                </div>
              </div>

              {/* Decision Reason & Tradeoffs */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-cyan-400 font-bold uppercase text-[10px]">WHY THIS WON</span>
                  <p className="text-slate-300 font-sans text-xs leading-relaxed">{decision.reason}</p>
                </div>

                <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-amber-400 font-bold uppercase text-[10px]">ACCEPTED TRADEOFFS</span>
                  <ul className="text-slate-300 font-sans text-xs space-y-1">
                    {(decision.tradeoffs || []).map((t, idx) => (
                      <li key={idx} className="flex items-center gap-1.5">
                        <span className="text-amber-400">⚡</span> {t}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Disagreement & Minority Report Callout */}
              {decision.minority_report && (
                <div className="p-3.5 bg-slate-900/90 border border-slate-800 rounded-xl space-y-1 text-xs font-sans">
                  <span className="text-amber-400 font-mono font-bold text-[10px] uppercase block">
                    ARCHITECTURE DISAGREEMENT & MINORITY REPORT
                  </span>
                  <p className="text-slate-300">{decision.minority_report}</p>
                  {decision.disagreement_summary && (
                    <p className="text-slate-400 text-[11px] font-mono mt-1">{decision.disagreement_summary}</p>
                  )}
                </div>
              )}

              {/* Human Approval Gate Bar */}
              {session.status === 'PENDING_APPROVAL' && (
                <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-center justify-between font-mono text-xs">
                  <div className="flex items-center gap-2">
                    <FaExclamationTriangle className="text-amber-400 w-4 h-4" />
                    <span className="font-bold text-amber-300">HUMAN APPROVAL REQUIRED FOR HIGH-IMPACT DECISION</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleReject}
                      className="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-lg transition flex items-center gap-1"
                    >
                      <FaTimes /> Reject
                    </button>
                    <button
                      onClick={handleApprove}
                      className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg transition flex items-center gap-1 shadow"
                    >
                      <FaCheck /> Approve Decision
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 3 CANDIDATE ARCHITECT CARDS GRID */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-sans">
            {candidates.map((cand) => {
              const isWinner = cand.candidate_id === winnerId;
              const candScore = scores[cand.candidate_id]?.total_weighted_score || 90.0;

              return (
                <div
                  key={cand.candidate_id}
                  className={`p-5 rounded-2xl border transition space-y-4 relative ${
                    isWinner
                      ? 'bg-slate-950 border-2 border-amber-500 shadow-2xl shadow-amber-500/10'
                      : 'bg-slate-950/70 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  {isWinner && (
                    <span className="absolute top-3 right-3 bg-amber-500/20 text-amber-400 font-mono text-[9px] font-bold px-2 py-0.5 rounded border border-amber-500/40">
                      🏆 WINNER
                    </span>
                  )}

                  <div className="font-mono">
                    <span className="text-xs font-bold text-amber-400">Architect {cand.candidate_id}</span>
                    <h3 className="text-sm font-bold text-white mt-0.5">{cand.name}</h3>
                    <p className="text-[10px] text-slate-400 mt-1">{cand.architecture}</p>
                  </div>

                  {/* Tech Stack Chips */}
                  <div className="flex flex-wrap gap-1 font-mono text-[10px]">
                    {cand.technology_stack.map((tech, i) => (
                      <span key={i} className="px-2 py-0.5 bg-slate-900 border border-slate-800 text-cyan-300 rounded">
                        {tech}
                      </span>
                    ))}
                  </div>

                  {/* Pros & Cons */}
                  <div className="space-y-2 text-xs font-mono border-t border-slate-800 pt-3">
                    <span className="text-slate-400 uppercase text-[10px] block font-bold">ADVANTAGES</span>
                    <ul className="space-y-1 text-emerald-400 text-[11px] font-sans">
                      {cand.advantages.map((adv, i) => <li key={i}>✓ {adv}</li>)}
                    </ul>

                    <span className="text-slate-400 uppercase text-[10px] block font-bold pt-2">RISKS & DISADVANTAGES</span>
                    <ul className="space-y-1 text-rose-400 text-[11px] font-sans">
                      {cand.disadvantages.map((dis, i) => <li key={i}>✗ {dis}</li>)}
                    </ul>
                  </div>

                  <div className="flex justify-between items-center font-mono text-xs border-t border-slate-800 pt-3">
                    <span className="text-slate-400 text-[10px]">Complexity: {cand.estimated_complexity}</span>
                    <span className="font-extrabold text-amber-400 text-sm">{candScore} / 100</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* CRITERIA COMPARISON MATRIX TABLE */}
          {decision && (
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4 font-mono text-xs">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <FaLayerGroup className="text-cyan-400" /> Evaluation Criteria Matrix & Scoring
              </h3>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 text-[11px]">
                      <th className="py-2.5 px-3">Criteria (Weight)</th>
                      {candidates.map((c) => (
                        <th key={c.candidate_id} className={`py-2.5 px-3 text-center ${c.candidate_id === winnerId ? 'text-amber-400 font-bold bg-amber-500/10' : ''}`}>
                          Candidate {c.candidate_id}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300 text-[11px]">
                    <tr>
                      <td className="py-2 px-3 font-semibold text-slate-200">Requirements Fit (25%)</td>
                      {candidates.map((c) => <td key={c.candidate_id} className="py-2 px-3 text-center">{scores[c.candidate_id]?.requirements_fit}</td>)}
                    </tr>
                    <tr>
                      <td className="py-2 px-3 font-semibold text-slate-200">Scalability (15%)</td>
                      {candidates.map((c) => <td key={c.candidate_id} className="py-2 px-3 text-center">{scores[c.candidate_id]?.scalability}</td>)}
                    </tr>
                    <tr>
                      <td className="py-2 px-3 font-semibold text-slate-200">Security (15%)</td>
                      {candidates.map((c) => <td key={c.candidate_id} className="py-2 px-3 text-center text-emerald-400">{scores[c.candidate_id]?.security}</td>)}
                    </tr>
                    <tr>
                      <td className="py-2 px-3 font-semibold text-slate-200">Maintainability (15%)</td>
                      {candidates.map((c) => <td key={c.candidate_id} className="py-2 px-3 text-center">{scores[c.candidate_id]?.maintainability}</td>)}
                    </tr>
                    <tr>
                      <td className="py-2 px-3 font-semibold text-slate-200">Performance (10%)</td>
                      {candidates.map((c) => <td key={c.candidate_id} className="py-2 px-3 text-center">{scores[c.candidate_id]?.performance}</td>)}
                    </tr>
                    <tr>
                      <td className="py-2 px-3 font-semibold text-slate-200">Complexity (10%)</td>
                      {candidates.map((c) => <td key={c.candidate_id} className="py-2 px-3 text-center">{scores[c.candidate_id]?.complexity}</td>)}
                    </tr>
                    <tr>
                      <td className="py-2 px-3 font-semibold text-slate-200">Cost (5%)</td>
                      {candidates.map((c) => <td key={c.candidate_id} className="py-2 px-3 text-center">{scores[c.candidate_id]?.cost}</td>)}
                    </tr>
                    <tr>
                      <td className="py-2 px-3 font-semibold text-slate-200">AIForge Fit (5%)</td>
                      {candidates.map((c) => <td key={c.candidate_id} className="py-2 px-3 text-center">{scores[c.candidate_id]?.aiforge_fit}</td>)}
                    </tr>
                    <tr className="font-bold text-white bg-slate-900">
                      <td className="py-2.5 px-3">Final Score</td>
                      {candidates.map((c) => (
                        <td key={c.candidate_id} className={`py-2.5 px-3 text-center text-sm ${c.candidate_id === winnerId ? 'text-amber-400 font-extrabold' : ''}`}>
                          {scores[c.candidate_id]?.total_weighted_score}
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* ADR INSPECTOR MODAL */}
      {showAdrModal && selectedAdr && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="bg-slate-950 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-4 font-sans shadow-2xl">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3 font-mono">
              <span className="text-amber-400 font-bold text-sm">{selectedAdr.adr_id} — ARCHITECTURE DECISION RECORD</span>
              <button onClick={() => setShowAdrModal(false)} className="text-slate-400 hover:text-white text-sm font-bold">✕</button>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div>
                <span className="text-slate-500 uppercase text-[10px] block">Title</span>
                <span className="text-white font-bold text-sm">{selectedAdr.title}</span>
              </div>
              <div>
                <span className="text-slate-500 uppercase text-[10px] block">Decision</span>
                <span className="text-emerald-400 font-bold">{selectedAdr.selected_option}</span>
              </div>
              <div>
                <span className="text-slate-500 uppercase text-[10px] block">Context</span>
                <span className="text-slate-300 font-sans">{selectedAdr.context}</span>
              </div>
              <div>
                <span className="text-slate-500 uppercase text-[10px] block">Alternatives Evaluated</span>
                <span className="text-slate-400 font-mono">{selectedAdr.alternatives.join(' | ')}</span>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button onClick={() => setShowAdrModal(false)} className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-xl text-xs">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
