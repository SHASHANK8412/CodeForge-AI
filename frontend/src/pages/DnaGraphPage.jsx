import React, { useState, useEffect } from 'react';
import { FaDna, FaSpinner, FaSearch, FaProjectDiagram, FaExclamationTriangle, FaShieldAlt, FaSyncAlt, FaLink, FaBug, FaCodeBranch, FaCheckCircle, FaTimesCircle, FaLightbulb } from 'react-icons/fa';
import {
  fetchDNAGraph,
  runImpactAnalysis,
  fetchRequirementTrace,
  fetchDeadCode,
  fetchCircularDependencies,
  fetchGraphDiff,
  explainGraphNode
} from '../services/dna';

export default function DnaGraphPage({ projectId = 'aiforge-demo' }) {
  const [graph, setGraph] = useState(null);
  const [loading, setLoading] = useState(true);

  // Tabs & Controls State
  const [activeTab, setActiveTab] = useState('graph'); // graph, requirements, deadcode, diff
  const [filterKind, setFilterKind] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Impact Analysis State
  const [selectedNode, setSelectedNode] = useState(null);
  const [impactResult, setImpactResult] = useState(null);
  const [nodeExplanation, setNodeExplanation] = useState('');
  const [analyzingImpact, setAnalyzingImpact] = useState(false);

  // Additional Subsystems Data
  const [reqTraces, setReqTraces] = useState([]);
  const [deadCode, setDeadCode] = useState([]);
  const [circularDeps, setCircularDeps] = useState([]);
  const [diffResult, setDiffResult] = useState(null);

  useEffect(() => {
    loadAllData();
  }, [projectId]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [gRes, reqRes, deadRes, circRes] = await Promise.all([
        fetchDNAGraph(projectId),
        fetchRequirementTrace(projectId),
        fetchDeadCode(projectId),
        fetchCircularDependencies(projectId)
      ]);

      if (gRes?.graph) setGraph(gRes.graph);
      if (reqRes?.traces) setReqTraces(reqRes.traces);
      if (deadRes?.dead_code) setDeadCode(deadRes.dead_code);
      if (circRes?.circular_dependencies) setCircularDeps(circRes.circular_dependencies);
    } catch (err) {
      console.warn('Failed to load DNA graph data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectNode = async (node) => {
    setSelectedNode(node);
    setImpactResult(null);
    setNodeExplanation('');
    try {
      const expRes = await explainGraphNode(projectId, node.id);
      setNodeExplanation(expRes.explanation);
    } catch (err) {
      console.warn('Explain failed:', err);
    }
  };

  const handleRunImpact = async () => {
    if (!selectedNode) return;
    setAnalyzingImpact(true);
    try {
      const res = await runImpactAnalysis(projectId, selectedNode.id, 'modify');
      setImpactResult(res.impact);
    } catch (err) {
      alert(`Impact analysis failed: ${err.message}`);
    } finally {
      setAnalyzingImpact(false);
    }
  };

  const handleFetchDiff = async () => {
    try {
      const res = await fetchGraphDiff(projectId, 1, 2);
      setDiffResult(res.diff);
      setActiveTab('diff');
    } catch (err) {
      alert(`Diff failed: ${err.message}`);
    }
  };

  // Node filtering
  const nodes = graph?.nodes || [];
  const edges = graph?.edges || [];

  const filteredNodes = nodes.filter((n) => {
    const matchesKind = filterKind === 'ALL' || n.kind === filterKind || (filterKind === 'SECURITY' && n.security_critical);
    const matchesSearch = !searchQuery || n.label.toLowerCase().includes(searchQuery.toLowerCase()) || (n.file_path && n.file_path.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesKind && matchesSearch;
  });

  const securityCount = nodes.filter((n) => n.security_critical).length;
  const apisCount = nodes.filter((n) => n.kind === 'API').length;
  const compCount = nodes.filter((n) => n.kind === 'COMPONENT').length;
  const dbCount = nodes.filter((n) => n.kind === 'DATABASE_MODEL' || n.kind === 'DATABASE_TABLE').length;
  const testCount = nodes.filter((n) => n.kind === 'TEST').length;

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6 select-none">
      {/* Top Header */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl flex items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-cyan-600/20 border border-cyan-500/40 rounded-xl text-cyan-400">
            <FaDna className="w-7 h-7 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              🧬 Engineering DNA & Dependency Intelligence
              <span className="text-xs px-2.5 py-0.5 bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 rounded-full font-mono">
                GRAPH ENGINE V2
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Deterministic AST Dependency Mapping, Transitive Impact Simulator & Requirement Traceability.
            </p>
          </div>
        </div>

        <button
          onClick={handleFetchDiff}
          className="px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-bold rounded-xl shadow transition flex items-center gap-2"
        >
          <FaCodeBranch className="text-purple-400" /> Compare Graph Versions
        </button>
      </div>

      {/* Engineering DNA Dashboard Counter Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 lg:grid-cols-10 gap-3 font-mono text-center">
        <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
          <span className="text-[9px] text-slate-400 uppercase block">Nodes</span>
          <span className="text-lg font-extrabold text-white">{nodes.length}</span>
        </div>
        <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
          <span className="text-[9px] text-slate-400 uppercase block">Edges</span>
          <span className="text-lg font-extrabold text-cyan-400">{edges.length}</span>
        </div>
        <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
          <span className="text-[9px] text-slate-400 uppercase block">APIs</span>
          <span className="text-lg font-extrabold text-indigo-400">{apisCount}</span>
        </div>
        <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
          <span className="text-[9px] text-slate-400 uppercase block">Components</span>
          <span className="text-lg font-extrabold text-blue-400">{compCount}</span>
        </div>
        <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
          <span className="text-[9px] text-slate-400 uppercase block">DB Models</span>
          <span className="text-lg font-extrabold text-purple-400">{dbCount}</span>
        </div>
        <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
          <span className="text-[9px] text-slate-400 uppercase block">Tests</span>
          <span className="text-lg font-extrabold text-emerald-400">{testCount}</span>
        </div>
        <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
          <span className="text-[9px] text-slate-400 uppercase block">Requirements</span>
          <span className="text-lg font-extrabold text-amber-400">{reqTraces.length}</span>
        </div>
        <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
          <span className="text-[9px] text-slate-400 uppercase block">Dead Code</span>
          <span className="text-lg font-extrabold text-rose-400">{deadCode.length}</span>
        </div>
        <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
          <span className="text-[9px] text-slate-400 uppercase block">Circular</span>
          <span className="text-lg font-extrabold text-amber-500">{circularDeps.length}</span>
        </div>
        <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
          <span className="text-[9px] text-slate-400 uppercase block">Security</span>
          <span className="text-lg font-extrabold text-emerald-400">{securityCount}</span>
        </div>
      </div>

      {/* Main Tabs Navigation Header */}
      <div className="flex border-b border-slate-800 font-mono text-xs gap-2">
        <button
          onClick={() => setActiveTab('graph')}
          className={`px-4 py-2 font-bold transition rounded-t-xl ${activeTab === 'graph' ? 'bg-slate-950 text-cyan-400 border-t-2 border-cyan-400' : 'text-slate-400 hover:text-slate-200'}`}
        >
          <FaProjectDiagram className="inline mr-1.5" /> Interactive Graph
        </button>
        <button
          onClick={() => setActiveTab('requirements')}
          className={`px-4 py-2 font-bold transition rounded-t-xl ${activeTab === 'requirements' ? 'bg-slate-950 text-amber-400 border-t-2 border-amber-400' : 'text-slate-400 hover:text-slate-200'}`}
        >
          <FaLink className="inline mr-1.5" /> Requirement Traceability ({reqTraces.length})
        </button>
        <button
          onClick={() => setActiveTab('deadcode')}
          className={`px-4 py-2 font-bold transition rounded-t-xl ${activeTab === 'deadcode' ? 'bg-slate-950 text-rose-400 border-t-2 border-rose-400' : 'text-slate-400 hover:text-slate-200'}`}
        >
          <FaBug className="inline mr-1.5" /> Dead Code & Circular ({deadCode.length + circularDeps.length})
        </button>
      </div>

      {/* TAB 1: INTERACTIVE GRAPH CANVAS */}
      {activeTab === 'graph' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Graph Grid Column */}
          <div className="lg:col-span-2 space-y-4">
            {/* Filter & Search Toolbar */}
            <div className="bg-slate-950 border border-slate-800 p-4 rounded-2xl flex flex-wrap gap-2 items-center justify-between">
              <div className="flex items-center gap-1.5 overflow-x-auto text-[11px] font-mono">
                {['ALL', 'FILE', 'COMPONENT', 'API', 'DATABASE_MODEL', 'TEST', 'SECURITY'].map((kind) => (
                  <button
                    key={kind}
                    onClick={() => setFilterKind(kind)}
                    className={`px-2.5 py-1 rounded-lg transition border ${
                      filterKind === kind
                        ? 'bg-indigo-600 border-indigo-500 text-white font-bold'
                        : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    {kind}
                  </button>
                ))}
              </div>

              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search node or file..."
                  className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono w-48"
                />
              </div>
            </div>

            {/* Nodes Render Canvas */}
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-4 shadow-xl min-h-[450px]">
              {loading ? (
                <div className="flex items-center justify-center p-12 text-slate-400">
                  <FaSpinner className="w-6 h-6 animate-spin text-cyan-400 mr-2" /> Building Engineering DNA Graph…
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 max-h-[500px] overflow-y-auto custom-scrollbar p-1">
                  {filteredNodes.map((n) => {
                    const isSelected = selectedNode?.id === n.id;
                    return (
                      <div
                        key={n.id}
                        onClick={() => handleSelectNode(n)}
                        className={`p-3 rounded-xl border transition cursor-pointer font-mono text-xs relative ${
                          isSelected
                            ? 'bg-indigo-600/30 border-cyan-400 shadow-lg shadow-cyan-500/10'
                            : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900'
                        }`}
                      >
                        {n.security_critical && (
                          <span className="absolute top-2 right-2 text-emerald-400 text-[10px]" title="Security Critical Node">
                            🛡
                          </span>
                        )}
                        <div className="font-bold text-white truncate pr-4">{n.label}</div>
                        <div className="text-[10px] text-cyan-400 uppercase mt-0.5">{n.kind}</div>
                        {n.file_path && <div className="text-[9px] text-slate-500 truncate mt-1">{n.file_path}</div>}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Node Details & Impact Sidebar Column */}
          <div className="bg-slate-950 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-4 font-mono text-xs">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-2">
              Node Details & Impact Engine
            </h3>

            {selectedNode ? (
              <div className="space-y-4">
                <div>
                  <div className="text-[10px] text-slate-500 uppercase">Selected Node</div>
                  <div className="font-bold text-white text-sm">{selectedNode.label}</div>
                  <div className="text-[10px] text-cyan-400 font-mono">{selectedNode.kind}</div>
                  {selectedNode.file_path && (
                    <div className="text-[10px] text-slate-400 mt-1">File: {selectedNode.file_path}</div>
                  )}
                  {selectedNode.security_critical && (
                    <div className="mt-1 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10px] inline-block font-bold">
                      🛡 SECURITY CRITICAL NODE
                    </div>
                  )}
                </div>

                {nodeExplanation && (
                  <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-[11px] text-slate-300 leading-relaxed font-sans">
                    <div className="text-[9px] font-mono text-cyan-400 uppercase font-bold mb-1">AI Node Context</div>
                    {nodeExplanation}
                  </div>
                )}

                <button
                  onClick={handleRunImpact}
                  disabled={analyzingImpact}
                  className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-xl shadow transition flex items-center justify-center gap-2"
                >
                  {analyzingImpact ? <FaSpinner className="animate-spin" /> : <FaSearch />} Calculate Transitive Impact
                </button>

                {impactResult && (
                  <div className="p-3 bg-slate-900 border border-cyan-500/30 rounded-xl space-y-2 text-[11px]">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-white">Impact Analysis</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] ${
                        impactResult.risk_score === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'
                      }`}>
                        Risk: {impactResult.risk_score}
                      </span>
                    </div>

                    <div className="text-slate-300 font-sans">{impactResult.explanation}</div>

                    <div className="space-y-1 text-[10px] text-slate-400 border-t border-slate-800 pt-2 font-mono">
                      <div>Affected Files: {impactResult.affected_files.length}</div>
                      <div>Affected APIs: {impactResult.affected_apis.length}</div>
                      <div>Affected DB Models: {impactResult.affected_database_objects.length}</div>
                      <div>Affected Tests: {impactResult.affected_tests.length}</div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-slate-500 text-center py-12 italic">
                Select any node from the graph to view properties, AI explanation, and dependency impact.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: REQUIREMENT TRACEABILITY */}
      {activeTab === 'requirements' && (
        <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4 font-sans">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 font-mono">
            <FaLink className="text-amber-400" /> Requirement Traceability Matrix ({reqTraces.length} Requirements)
          </h3>

          <div className="space-y-3 font-mono text-xs">
            {reqTraces.map((tr) => (
              <div key={tr.requirement_id} className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-white flex items-center gap-2 font-sans">
                    {tr.status === 'IMPLEMENTED' ? <FaCheckCircle className="text-emerald-400" /> : <FaTimesCircle className="text-rose-400" />}
                    {tr.text}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] ${tr.status === 'IMPLEMENTED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'}`}>
                    {tr.status} ({tr.coverage_percent}%)
                  </span>
                </div>

                {tr.status === 'IMPLEMENTED' ? (
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[10px] text-slate-400 border-t border-slate-800/80 pt-2">
                    <div>Components: {tr.components.join(', ') || 'None'}</div>
                    <div>APIs: {tr.apis.join(', ') || 'None'}</div>
                    <div>Tests: {tr.tests.join(', ') || 'None'}</div>
                  </div>
                ) : (
                  <div className="text-rose-400 text-[11px] font-sans">
                    ⚠ Requirement not traced in project codebase. Unimplemented status.
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: DEAD CODE & CIRCULAR DEPENDENCIES */}
      {activeTab === 'deadcode' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 font-sans">
          {/* Dead Code */}
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 font-mono">
              <FaBug className="text-rose-400" /> Potentially Unused Code ({deadCode.length})
            </h3>
            <div className="space-y-2 font-mono text-xs">
              {deadCode.map((dc, idx) => (
                <div key={idx} className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
                  <div className="font-bold text-rose-300">{dc.name} ({dc.kind})</div>
                  <div className="text-[10px] text-slate-400">{dc.file_path}</div>
                  <div className="text-[10px] text-slate-500 italic">{dc.reason}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Circular Dependencies */}
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 font-mono">
              <FaExclamationTriangle className="text-amber-400" /> Circular Dependencies ({circularDeps.length})
            </h3>
            <div className="space-y-2 font-mono text-xs">
              {circularDeps.map((cd, idx) => (
                <div key={idx} className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
                  <div className="font-bold text-amber-400">Cycle Detected</div>
                  <div className="text-[11px] text-slate-300">{cd.cycle.join(' ➔ ')}</div>
                  <div className="text-[10px] text-slate-400">{cd.recommendation}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
