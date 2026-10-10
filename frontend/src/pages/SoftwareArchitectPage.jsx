import React, { useState, useEffect } from 'react';
import { FaBuilding, FaSearch, FaProjectDiagram, FaSpinner, FaLayerGroup, FaShieldAlt, FaTachometerAlt, FaCheckCircle, FaExclamationTriangle, FaComments, FaFileAlt, FaLock, FaPaperPlane } from 'react-icons/fa';
import {
  fetchCurrentArchitecture,
  simulateArchitecture,
  simulateFailure,
  runArchitectDebate,
  approveArchitecturePlan,
  fetchArchitectureHistory
} from '../services/architect';

const SAMPLE_PROMPTS = [
  'Should we add Redis?',
  'What if PostgreSQL fails?',
  'What happens if we migrate MongoDB to PostgreSQL?',
  'Simulate 10x traffic load',
  'Should we split backend into microservices?'
];

export default function SoftwareArchitectPage({ projectId = 'aiforge-demo' }) {
  const [currentDiagram, setCurrentDiagram] = useState(null);
  const [simulation, setSimulation] = useState(null);
  const [failureReport, setFailureReport] = useState(null);
  const [debateResult, setDebateResult] = useState(null);
  const [planResult, setPlanResult] = useState(null);
  const [prompt, setPrompt] = useState('Should we add Redis?');
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);

  useEffect(() => {
    loadCurrentArchitecture();
  }, [projectId]);

  const loadCurrentArchitecture = async () => {
    setLoading(true);
    try {
      const res = await fetchCurrentArchitecture(projectId);
      if (res?.architecture) setCurrentDiagram(res.architecture);
    } catch (err) {
      console.warn('Failed to load current architecture:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulate = async (promptToUse = null) => {
    const activePrompt = promptToUse || prompt;
    if (!activePrompt.trim()) return;

    setSimulating(true);
    setFailureReport(null);
    try {
      if (activePrompt.toLowerCase().includes('fail')) {
        const comp = activePrompt.toLowerCase().includes('postgres') ? 'PostgreSQL' : 'OrderService';
        const res = await simulateFailure(projectId, comp);
        if (res?.failure_report) setFailureReport(res.failure_report);
      } else {
        const res = await simulateArchitecture(projectId, activePrompt);
        if (res?.scenario) setSimulation(res);
      }
    } catch (err) {
      alert(`Simulation error: ${err.message}`);
    } finally {
      setSimulating(false);
    }
  };

  const handleRunDebate = async () => {
    if (!simulation?.scenario) return;
    setSimulating(true);
    try {
      const res = await runArchitectDebate(projectId, simulation.scenario.name);
      if (res?.debate_result) setDebateResult(res.debate_result);
    } catch (err) {
      alert(`Debate error: ${err.message}`);
    } finally {
      setSimulating(false);
    }
  };

  const handleApprovePlan = async () => {
    if (!simulation?.scenario) return;
    try {
      const res = await approveArchitecturePlan(projectId, simulation.scenario.id);
      if (res?.plan) setPlanResult(res);
    } catch (err) {
      alert(`Approval error: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6 select-none">
      {/* Top Header */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-amber-600/20 border border-amber-500/40 rounded-xl text-amber-400">
            <FaBuilding className="w-7 h-7 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              🏗️ AI Software Architect Simulator
              <span className="text-xs px-2.5 py-0.5 bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded-full font-mono">
                READ-ONLY SANDBOX V2
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Simulate candidate architectures, SPOF failure propagation, multi-option scoring & ADR generation.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-xl text-slate-300 flex items-center gap-1.5">
            <FaLock className="text-amber-400" /> Read-Only Sandbox Mode
          </span>
        </div>
      </div>

      {/* NATURAL LANGUAGE SIMULATION BAR */}
      <div className="space-y-2">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSimulate();
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ask Architect (e.g. 'Should we add Redis?', 'What if PostgreSQL fails?', 'Simulate 10x traffic')..."
            className="flex-1 bg-slate-950 border border-slate-800 rounded-2xl px-5 py-3.5 text-xs font-mono text-white outline-none focus:border-amber-500 shadow-xl"
          />
          <button
            type="submit"
            disabled={simulating}
            className="px-6 py-3.5 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-2xl shadow-xl transition flex items-center gap-2"
          >
            {simulating ? <FaSpinner className="animate-spin" /> : <FaPaperPlane />} Simulate Scenario
          </button>
        </form>

        {/* Quick Sample Prompts */}
        <div className="flex flex-wrap gap-2 font-mono text-xs">
          {SAMPLE_PROMPTS.map((p) => (
            <button
              key={p}
              onClick={() => {
                setPrompt(p);
                handleSimulate(p);
              }}
              className="px-3 py-1 bg-slate-950 border border-slate-800 hover:border-amber-500/40 text-amber-300 rounded-xl transition text-[11px]"
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12 text-slate-400 font-mono text-xs">
          <FaSpinner className="w-5 h-5 animate-spin text-amber-400 mr-2" /> Inspecting Engineering DNA dependency graph…
        </div>
      ) : (
        <>
          {/* FAILURE PROPAGATION REPORT */}
          {failureReport && (
            <div className="p-6 bg-rose-950/30 border-2 border-rose-500/60 rounded-2xl shadow-2xl space-y-3 font-mono">
              <div className="flex items-center gap-2 text-rose-400 text-sm font-bold">
                <FaExclamationTriangle className="w-5 h-5 animate-pulse" />
                Failure Propagation Report: Component '{failureReport.failed_component}' FAILED
              </div>
              <div className="text-xs text-slate-300">
                Single Point of Failure (SPOF): <span className="text-rose-400 font-bold">{failureReport.single_point_of_failure ? 'YES' : 'NO'}</span>
              </div>
              <div className="text-xs text-slate-300">
                Affected Components: {failureReport.affected_components?.join(', ')}
              </div>
              <div className="p-3 bg-slate-900 rounded-xl border border-rose-500/30 text-xs text-rose-300">
                💡 Mitigation Recommendation: {failureReport.mitigation_recommendation}
              </div>
            </div>
          )}

          {/* SIMULATION RESULT & SIDE-BY-SIDE COMPARISON */}
          {simulation && (
            <div className="space-y-6">
              <div className="bg-slate-950 border border-amber-500/50 rounded-2xl p-6 shadow-2xl space-y-4 font-mono text-xs">
                <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                  <span className="text-sm font-bold text-amber-400">Simulation: {simulation.scenario?.name}</span>
                  <span className="px-2.5 py-0.5 bg-amber-500/10 border border-amber-500/30 text-amber-300 rounded font-bold">
                    {simulation.assessment?.evidence_type} (Confidence: {simulation.assessment?.confidence})
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-sans">
                  <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
                    <span className="text-[10px] text-slate-400 uppercase font-mono block">Performance Impact</span>
                    <span className="text-emerald-400 font-bold">{simulation.assessment?.performance_impact}</span>
                  </div>
                  <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
                    <span className="text-[10px] text-slate-400 uppercase font-mono block">Security Impact</span>
                    <span className="text-amber-400 font-bold">{simulation.assessment?.security_impact}</span>
                  </div>
                </div>

                {/* Scorecard Table */}
                <div className="space-y-2 pt-2">
                  <span className="text-[10px] text-slate-400 uppercase block font-bold">Side-by-Side Architectural Scorecard</span>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-400 font-mono">
                          <th className="py-2">Option</th>
                          <th className="py-2">Perf</th>
                          <th className="py-2">Security</th>
                          <th className="py-2">Scalability</th>
                          <th className="py-2">Complexity</th>
                          <th className="py-2">Cost</th>
                          <th className="py-2">Overall</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800 text-slate-200">
                        <tr>
                          <td className="py-2 font-bold">{simulation.comparison?.current_option?.option_name}</td>
                          <td>{simulation.comparison?.current_option?.performance_score}</td>
                          <td>{simulation.comparison?.current_option?.security_score}</td>
                          <td>{simulation.comparison?.current_option?.scalability_score}</td>
                          <td>{simulation.comparison?.current_option?.complexity_score}</td>
                          <td>{simulation.comparison?.current_option?.cost_score}</td>
                          <td className="font-bold text-amber-400">{simulation.comparison?.current_option?.overall_score}</td>
                        </tr>
                        {(simulation.comparison?.proposed_options || []).map((opt, idx) => (
                          <tr key={idx}>
                            <td className="py-2 font-bold text-emerald-300">{opt.option_name}</td>
                            <td>{opt.performance_score}</td>
                            <td>{opt.security_score}</td>
                            <td>{opt.scalability_score}</td>
                            <td>{opt.complexity_score}</td>
                            <td>{opt.cost_score}</td>
                            <td className="font-bold text-emerald-400">{opt.overall_score}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-slate-300">
                  💡 Recommendation: {simulation.comparison?.recommendation}
                </div>

                {/* Actions */}
                <div className="flex flex-wrap gap-2 pt-2">
                  <button
                    onClick={handleRunDebate}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-xl shadow transition flex items-center gap-1.5"
                  >
                    <FaComments /> Trigger Multi-Agent Debate
                  </button>
                  <button
                    onClick={handleApprovePlan}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow transition flex items-center gap-1.5"
                  >
                    <FaFileAlt /> Generate ADR & 7-Phase Plan
                  </button>
                </div>
              </div>

              {debateResult && (
                <div className="p-5 bg-slate-950 border border-indigo-500/50 rounded-2xl shadow-xl space-y-2 font-mono text-xs">
                  <span className="font-bold text-indigo-400 uppercase">💬 Multi-Agent Debate Complete</span>
                  <div className="text-slate-200">Winner Candidate: {debateResult.winner}</div>
                </div>
              )}

              {planResult && (
                <div className="p-5 bg-slate-950 border border-emerald-500/50 rounded-2xl shadow-xl space-y-2 font-mono text-xs">
                  <span className="font-bold text-emerald-400 uppercase">📄 Generated {planResult.adr?.title}</span>
                  <div className="text-slate-300">7-Phase Implementation Plan Created in Engineering Memory.</div>
                </div>
              )}
            </div>
          )}

          {/* CURRENT ARCHITECTURE DIAGRAM */}
          <div className="bg-slate-950 border border-slate-800 p-6 rounded-2xl shadow-xl space-y-4 font-mono text-xs">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-2 flex items-center gap-2">
              <FaProjectDiagram className="text-amber-400" /> Current Baseline Architecture Diagram
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
              {(currentDiagram?.nodes || []).map((n) => (
                <div key={n.id} className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
                  <span className="text-[9px] text-amber-400 block uppercase font-bold">{n.type}</span>
                  <span className="text-white font-sans text-xs font-bold block">{n.label}</span>
                  <span className="text-[10px] text-slate-400 font-mono block">{n.technology}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
