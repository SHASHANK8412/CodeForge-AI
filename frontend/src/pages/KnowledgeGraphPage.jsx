import React, { useState, useEffect } from "react";
import { 
  FaBrain, FaProjectDiagram, FaSearch, FaBook, FaLayerGroup, 
  FaArrowRight, FaCheckCircle, FaExclamationTriangle, FaFilter, 
  FaPlus, FaLightbulb, FaDatabase, FaServer, FaShieldAlt, FaCode
} from "react-icons/fa";
import { fetchFullGraph, queryGraphRAG, fetchEntityNeighbors } from "../services/knowledgeGraphApi";
import { saveOutputItem } from "../utils/workspaceStorage";
import toast from "react-hot-toast";

const SAMPLE_QUERIES = [
  "What technologies are indirectly affected if Apache Kafka fails?",
  "Show authentication security policies and database storage dependencies for FastAPI Gateway",
  "How are React Frontend and Redis Streams connected?",
  "What systems depend on PostgreSQL Database for ACID ledger guarantees?"
];

export default function KnowledgeGraphPage({ setView, activeProjectId = "aiforge-fooddelivery-ai" }) {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [entityDetails, setEntityDetails] = useState(null);

  // Graph RAG Query State
  const [nlQuery, setNlQuery] = useState("");
  const [isQuerying, setIsQuerying] = useState(false);
  const [ragResult, setRagResult] = useState(null);
  const [activeFilter, setActiveFilter] = useState("ALL"); // "ALL", "Service", "Technology", "Database", "SecurityPolicy"

  const loadData = async () => {
    try {
      const g = await fetchFullGraph(activeProjectId);
      setGraphData(g);
      if (g?.nodes?.length > 0 && !selectedEntity) {
        handleSelectEntity(g.nodes[0]);
      }
    } catch (err) {
      console.error("Error loading knowledge graph:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeProjectId]);

  const handleSelectEntity = async (node) => {
    setSelectedEntity(node);
    try {
      const details = await fetchEntityNeighbors(node.id);
      setEntityDetails(details);
    } catch (err) {
      setEntityDetails(null);
    }
  };

  const handleRunGraphQuery = async (queryToRun) => {
    const q = queryToRun || nlQuery;
    if (!q.trim()) return;
    setIsQuerying(true);
    setNlQuery(q);
    toast("Traversing Knowledge Graph & Synthesizing Multi-Hop Evidence...", { icon: "🧠" });
    try {
      const res = await queryGraphRAG({
        query: q.trim(),
        projectId: activeProjectId,
        maxHops: 2
      });
      setRagResult(res);
      toast.success("Graph RAG Synthesis Complete!", { icon: "✓" });
    } catch (err) {
      toast.error("Graph RAG query failed");
    } finally {
      setIsQuerying(false);
    }
  };

  const handleSaveToLibrary = () => {
    if (!ragResult) return;
    saveOutputItem({
      title: `Graph RAG: ${ragResult.query}`,
      category: "Research",
      content: ragResult.synthesis_answer,
      language: "markdown"
    });
    toast.success("Saved Graph RAG Report to Library!", { icon: "📑" });
  };

  const filteredNodes = (graphData?.nodes || []).filter(n => {
    if (activeFilter === "ALL") return true;
    return n.entity_type === activeFilter;
  });

  return (
    <div className="h-full flex flex-col bg-[#0B0F19] text-[#F5F7FA] font-sans overflow-hidden">
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-4 bg-[#0F172A] border-b border-gray-800 text-xs">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-cyan-500 text-white shadow-lg shadow-purple-500/20">
            <FaProjectDiagram size={18} />
          </div>
          <div>
            <h1 className="text-base font-bold text-white flex items-center gap-2">
              Knowledge Graph & Graph RAG
              <span className="px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 font-mono text-[10px] font-bold">
                Relationship-Aware Intelligence
              </span>
            </h1>
            <p className="text-xs text-gray-400">
              Entity Discovery, Multi-Hop Dependency Traversal, Provenance Tracking & Grounded Inference
            </p>
          </div>
        </div>

        {/* Global Node Counts */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="px-3 py-1.5 bg-[#151821] border border-gray-800 rounded-xl text-gray-300">
            {graphData?.nodes_count || 0} Entities
          </span>
          <span className="px-3 py-1.5 bg-[#151821] border border-gray-800 rounded-xl text-purple-300">
            {graphData?.edges_count || 0} Relationships
          </span>
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Graph Explorer & Natural Language Graph RAG (65%) */}
        <div className="flex-1 bg-[#0B0F19] overflow-y-auto p-6 space-y-6 custom-scrollbar border-r border-[#242833]">
          {/* Natural Language Graph RAG Search Box */}
          <div className="p-5 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-3 shadow-xl">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-purple-400 uppercase font-bold flex items-center gap-1.5">
                <FaSearch size={10} /> Ask Graph RAG (Multi-Hop Traversal)
              </span>
              <span className="text-[10px] font-mono text-gray-500">Max Depth: 2 Hops</span>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="text"
                value={nlQuery}
                onChange={(e) => setNlQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleRunGraphQuery()}
                placeholder="e.g. What breaks if Kafka fails? Or show dependencies of FastAPI..."
                className="flex-1 bg-[#08090D] border border-[#242833] focus:border-purple-500 rounded-xl p-3 text-xs text-white outline-none"
              />
              <button
                onClick={() => handleRunGraphQuery()}
                disabled={isQuerying || !nlQuery.trim()}
                className="px-4 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:bg-gray-800 text-white rounded-xl font-bold transition shadow cursor-pointer text-xs"
              >
                {isQuerying ? "Traversing..." : "Query Graph"}
              </button>
            </div>

            {/* Starter Query Pills */}
            <div className="flex flex-wrap gap-1.5 pt-1">
              {SAMPLE_QUERIES.map((sq, i) => (
                <button
                  key={i}
                  onClick={() => handleRunGraphQuery(sq)}
                  className="px-2.5 py-1 rounded-lg bg-[#08090D] hover:bg-[#151821] border border-[#1C202B] text-[10px] text-gray-400 hover:text-purple-300 font-mono transition cursor-pointer text-left truncate max-w-xs"
                >
                  💡 {sq}
                </button>
              ))}
            </div>
          </div>

          {/* Graph RAG Synthesis Results (If Present) */}
          {ragResult && (
            <div className="p-6 rounded-3xl bg-gradient-to-b from-[#151226] to-[#0F1117] border border-purple-500/40 space-y-4 shadow-2xl animate-fade-in">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-purple-300 uppercase font-bold flex items-center gap-1.5">
                  <FaBrain size={11} /> Grounded Multi-Hop Answer ({ragResult.duration_seconds}s)
                </span>
                <button
                  onClick={handleSaveToLibrary}
                  className="px-3 py-1.5 bg-[#1E293B] hover:bg-[#334155] text-purple-300 rounded-xl text-xs font-semibold border border-purple-500/30 cursor-pointer"
                >
                  Save to Library
                </button>
              </div>

              {/* 3 Evidence Categories Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                {/* 1. Direct Evidence */}
                <div className="p-3.5 rounded-2xl bg-[#08090D] border border-[#1C202B] space-y-2">
                  <span className="text-[9px] font-mono text-cyan-400 font-bold uppercase block">
                    1. Direct Evidence
                  </span>
                  <div className="space-y-1.5">
                    {ragResult.direct_evidence.map((de, idx) => (
                      <div key={idx} className="p-2 rounded-lg bg-black/40 border border-[#1C202B] text-[10px] space-y-0.5">
                        <span className="text-cyan-300 font-mono font-bold block">{de.citation_ref}</span>
                        <p className="text-gray-400 line-clamp-2">{de.text_snippet}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 2. Derived Relationships */}
                <div className="p-3.5 rounded-2xl bg-[#08090D] border border-[#1C202B] space-y-2">
                  <span className="text-[9px] font-mono text-purple-400 font-bold uppercase block">
                    2. Derived Traversal Hops
                  </span>
                  <div className="space-y-1.5">
                    {ragResult.derived_relationships.map((dr, idx) => (
                      <div key={idx} className="p-2 rounded-lg bg-black/40 border border-[#1C202B] text-[10px] space-y-0.5">
                        <div className="flex items-center gap-1 font-mono text-purple-300 font-bold">
                          <span>{dr.source}</span>
                          <span className="text-gray-500">→</span>
                          <span>{dr.target}</span>
                        </div>
                        <span className="text-gray-500 text-[9px] block">[{dr.relation}] • Ref: {dr.evidence_ref}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 3. Analytical Inferences */}
                <div className="p-3.5 rounded-2xl bg-[#08090D] border border-[#1C202B] space-y-2">
                  <span className="text-[9px] font-mono text-amber-400 font-bold uppercase block">
                    3. Impact Inferences
                  </span>
                  <div className="space-y-1.5">
                    {ragResult.inferences.map((inf, idx) => (
                      <div key={idx} className="p-2 rounded-lg bg-black/40 border border-[#1C202B] text-[10px]">
                        <p className="text-amber-200/90 leading-relaxed">⚠️ {inf}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Interactive Node Graph Explorer */}
          <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-[10px] font-mono text-gray-400 uppercase font-bold">
                Project Topology & Entity Matrix
              </span>
              {/* Type Filters */}
              <div className="flex items-center gap-1">
                {["ALL", "Service", "Technology", "Database", "SecurityPolicy"].map((f) => (
                  <button
                    key={f}
                    onClick={() => setActiveFilter(f)}
                    className={`px-2.5 py-1 rounded-lg text-[10px] font-mono font-bold transition cursor-pointer ${
                      activeFilter === f ? "bg-purple-600 text-white" : "bg-[#151821] text-gray-400 hover:text-white"
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>

            {/* Entity Nodes Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {filteredNodes.map((node) => (
                <div
                  key={node.id}
                  onClick={() => handleSelectEntity(node)}
                  className={`p-4 rounded-2xl cursor-pointer transition space-y-2 ${
                    selectedEntity?.id === node.id
                      ? "bg-[#1B172E] border border-purple-500 shadow-xl"
                      : "bg-[#0F1117] hover:bg-[#151821] border border-[#242833]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono text-[9px] font-bold">
                      {node.entity_type}
                    </span>
                    <span className="text-[10px] font-mono text-emerald-400 font-bold">
                      {Math.round((node.confidence || 0.95) * 100)}% Conf
                    </span>
                  </div>
                  <h3 className="font-bold text-xs text-white">{node.name}</h3>
                  <p className="text-[11px] text-gray-400 line-clamp-2 leading-relaxed">
                    {node.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Side: Entity Provenance & Neighborhood Panel (35%) */}
        <div className="w-96 bg-[#0F1117] overflow-y-auto p-6 space-y-5 custom-scrollbar">
          {selectedEntity ? (
            <div className="space-y-5">
              <div className="space-y-1.5 pb-4 border-b border-[#1C202B]">
                <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono text-[10px] font-bold">
                  {selectedEntity.entity_type}
                </span>
                <h2 className="text-base font-bold text-white">{selectedEntity.name}</h2>
                <p className="text-xs text-gray-400 leading-relaxed">{selectedEntity.description}</p>
                {selectedEntity.aliases?.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-1">
                    {selectedEntity.aliases.map((a, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-[#08090D] border border-[#1C202B] text-[9px] font-mono text-gray-400">
                        {a}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Outgoing Downstream Dependencies */}
              <div className="space-y-2">
                <span className="text-[10px] font-mono text-purple-400 uppercase font-bold block">
                  Outgoing Connections ({entityDetails?.outgoing?.length || 0})
                </span>
                <div className="space-y-2">
                  {(entityDetails?.outgoing || []).map((out, idx) => (
                    <div key={idx} className="p-3 bg-[#08090D] border border-[#1C202B] rounded-xl space-y-1 text-xs">
                      <div className="flex items-center justify-between font-mono text-[10px]">
                        <span className="text-purple-300 font-bold">[{out.edge.relation_type}]</span>
                        <span className="text-gray-500">{out.edge.evidence_document}</span>
                      </div>
                      <span className="font-bold text-white block">{out.target_node?.name}</span>
                      {out.edge.description && (
                        <p className="text-[10px] text-gray-400 leading-relaxed">{out.edge.description}</p>
                      )}
                    </div>
                  ))}
                  {(!entityDetails?.outgoing || entityDetails.outgoing.length === 0) && (
                    <div className="text-[11px] text-gray-500 italic">No outgoing connections.</div>
                  )}
                </div>
              </div>

              {/* Incoming Upstream Dependencies */}
              <div className="space-y-2 pt-3 border-t border-[#1C202B]">
                <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold block">
                  Incoming Connections ({entityDetails?.incoming?.length || 0})
                </span>
                <div className="space-y-2">
                  {(entityDetails?.incoming || []).map((inc, idx) => (
                    <div key={idx} className="p-3 bg-[#08090D] border border-[#1C202B] rounded-xl space-y-1 text-xs">
                      <div className="flex items-center justify-between font-mono text-[10px]">
                        <span className="text-cyan-300 font-bold">[{inc.edge.relation_type}]</span>
                        <span className="text-gray-500">{inc.edge.evidence_document}</span>
                      </div>
                      <span className="font-bold text-white block">{inc.source_node?.name}</span>
                    </div>
                  ))}
                  {(!entityDetails?.incoming || entityDetails.incoming.length === 0) && (
                    <div className="text-[11px] text-gray-500 italic">No incoming connections.</div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500 text-xs">
              Select an entity to inspect provenance & neighborhood
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
