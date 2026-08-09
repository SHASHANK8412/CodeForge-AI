import React, { useState, useEffect } from 'react';
import {
  FaBookOpen, FaFileUpload, FaTrash, FaCheckCircle,
  FaSpinner, FaFileCode, FaDatabase, FaLayerGroup, FaInfoCircle
} from 'react-icons/fa';
import { uploadProjectDocuments, deleteProjectDocument, fetchProjectRAGStats } from '../../services/rag';

export default function RAGKnowledgeDashboard({ projectId = 'default_project' }) {
  const [stats, setStats] = useState({ total_chunks: 0, unique_documents: 0, sources: [] });
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState(null);
  const [selectedFiles, setSelectedFiles] = useState(null);

  useEffect(() => {
    loadStats();
  }, [projectId]);

  const loadStats = async () => {
    setLoading(true);
    try {
      const res = await fetchProjectRAGStats(projectId);
      setStats(res);
    } catch (err) {
      console.warn('Failed to load RAG stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFiles(e.target.files);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFiles || selectedFiles.length === 0) return;

    setUploading(true);
    setUploadMessage(null);
    try {
      const res = await uploadProjectDocuments(projectId, selectedFiles);
      setUploadMessage({ type: 'success', text: `Indexed ${res.chunks_indexed} chunk(s) across ${res.files.length} file(s)` });
      setSelectedFiles(null);
      await loadStats();
    } catch (err) {
      setUploadMessage({ type: 'error', text: err.message || 'Upload failed' });
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteSource = async (docName) => {
    if (!window.confirm(`Delete '${docName}'? This will remove its vector embeddings.`)) return;
    try {
      await deleteProjectDocument(projectId, docName);
      await loadStats();
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl flex items-center justify-center space-x-3 text-slate-400">
        <FaSpinner className="w-5 h-5 animate-spin text-indigo-400" />
        <span className="text-sm font-medium">Loading RAG Knowledge Engine…</span>
      </div>
    );
  }

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <FaBookOpen className="text-indigo-400 w-5 h-5" />
            Knowledge & RAG Intelligence Engine
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Project-isolated vector knowledge, document chunking, and code context retrieval
          </p>
        </div>

        {/* Stats Pills */}
        <div className="flex items-center gap-3 font-mono text-xs">
          <div className="bg-slate-900 border border-slate-800 px-3.5 py-1.5 rounded-xl">
            <span className="text-slate-400">Documents: </span>
            <span className="font-bold text-indigo-400">{stats.unique_documents || 0}</span>
          </div>
          <div className="bg-slate-900 border border-slate-800 px-3.5 py-1.5 rounded-xl">
            <span className="text-slate-400">Indexed Chunks: </span>
            <span className="font-bold text-cyan-400">{stats.total_chunks || 0}</span>
          </div>
        </div>
      </div>

      {/* Upload Zone & Knowledge Checklist */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Upload Form */}
        <form onSubmit={handleUpload} className="md:col-span-7 bg-slate-900/60 border border-slate-800 rounded-xl p-4 space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
            <FaFileUpload className="text-indigo-400" />
            Upload Project Documentation & Code
          </h3>
          <p className="text-[11px] text-slate-400">
            Supported: PDF, DOCX, MD, TXT, JSON, Python, JS, TS, SQL, HTML, CSS, YAML
          </p>

          <div className="flex items-center gap-3">
            <input
              type="file"
              multiple
              onChange={handleFileChange}
              className="text-xs text-slate-300 file:mr-3 file:py-1.5 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
            />
            <button
              type="submit"
              disabled={uploading || !selectedFiles}
              className="px-4 py-1.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl transition flex items-center gap-1.5 shrink-0"
            >
              {uploading ? <FaSpinner className="w-3 h-3 animate-spin" /> : 'Index Files'}
            </button>
          </div>

          {uploadMessage && (
            <div className={`text-xs p-2 rounded-lg ${uploadMessage.type === 'success' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'}`}>
              {uploadMessage.text}
            </div>
          )}
        </form>

        {/* Knowledge Sources Checklist */}
        <div className="md:col-span-5 bg-slate-900/40 border border-slate-800 rounded-xl p-4 space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
            <FaCheckCircle className="text-emerald-400" />
            RAG Knowledge Sources
          </h3>
          <ul className="space-y-1.5 text-[11px] font-mono text-slate-400">
            <li className="flex items-center gap-2"><FaCheckCircle className="text-emerald-400 w-3 h-3" /> Requirements & Discovery</li>
            <li className="flex items-center gap-2"><FaCheckCircle className="text-emerald-400 w-3 h-3" /> Architecture & Data Schema</li>
            <li className="flex items-center gap-2"><FaCheckCircle className="text-emerald-400 w-3 h-3" /> REST API Specifications</li>
            <li className="flex items-center gap-2"><FaCheckCircle className="text-emerald-400 w-3 h-3" /> Project Decisions Memory</li>
            <li className="flex items-center gap-2"><FaCheckCircle className="text-emerald-400 w-3 h-3" /> Generated Source Code</li>
          </ul>
        </div>
      </div>

      {/* Indexed Document Files List */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <FaFileCode className="text-cyan-400" />
          Indexed Project Document Sources ({(stats.sources || []).length})
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
          {(stats.sources || []).length > 0 ? (
            stats.sources.map((src, idx) => (
              <div key={idx} className="bg-slate-900/70 border border-slate-800/80 rounded-xl p-3 flex items-center justify-between">
                <span className="text-xs font-mono text-slate-300 truncate max-w-[180px]">{src}</span>
                <button
                  onClick={() => handleDeleteSource(src)}
                  className="text-slate-500 hover:text-rose-400 text-xs p-1 transition"
                  title="Delete Document"
                >
                  <FaTrash />
                </button>
              </div>
            ))
          ) : (
            <div className="col-span-3 text-xs text-slate-500 italic p-3 text-center bg-slate-900/30 rounded-xl border border-slate-800/50">
              No custom project documentation uploaded yet. Default architecture knowledge active.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
