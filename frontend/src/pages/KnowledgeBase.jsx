import React, { useState, useEffect } from 'react';
import { FaBook, FaTrash, FaCheckCircle, FaProjectDiagram } from 'react-icons/fa';
import UploadBox from '../components/UploadBox';
import DocumentList from '../components/DocumentList';
import ChatWindow from '../components/ChatWindow';
import ChatInput from '../components/ChatInput';

export default function KnowledgeBase() {
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchDocuments = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/documents');
      if (res.ok) {
        const data = await res.json();
        setDocuments(data || []);
      }
    } catch {
      // Fallback initial list
      setDocuments([
        { filename: 'sample_prd.md', size_bytes: 420, upload_time: '2026-07-26 12:00:00' },
        { filename: 'FastAPI Guide.md', size_bytes: 580, upload_time: '2026-07-26 12:00:00' },
        { filename: 'JWT Authentication.md', size_bytes: 610, upload_time: '2026-07-26 12:00:00' }
      ]);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleDeleteDocument = async (filename) => {
    try {
      await fetch(`http://127.0.0.1:8000/api/documents/${filename}`, {
        method: 'DELETE',
      });
      fetchDocuments();
    } catch (err) {
      console.error('Delete document failed:', err);
    }
  };

  const handleSendQuery = async (question) => {
    setMessages((prev) => [...prev, { sender: 'user', text: question }]);
    setLoading(true);

    try {
      const res = await fetch('http://127.0.0.1:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          sender: 'ai',
          text: data.answer || 'Answer generated from uploaded documents.',
          sources: data.sources || []
        }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'ai',
          text: `❌ Error querying knowledge base: ${err.message}`
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="bg-indigo-600 p-3 rounded-lg text-white">
            <FaBook className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white uppercase tracking-wide">
              Knowledge Base & RAG Assistant
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Upload project documents and chat with AI agents grounded in your documentation.
            </p>
          </div>
        </div>

        <button
          onClick={() => setMessages([])}
          className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs px-3.5 py-2 rounded-lg transition active:scale-95 cursor-pointer w-fit"
        >
          <FaTrash className="w-3 h-3 text-slate-400" /> Clear Chat
        </button>
      </div>

      {/* Main 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Upload & Document List */}
        <div className="lg:col-span-5 space-y-6">
          <UploadBox onUploadSuccess={() => fetchDocuments()} />
          <DocumentList documents={documents} onDeleteDocument={handleDeleteDocument} />
        </div>

        {/* Right Column: AI Chat */}
        <div className="lg:col-span-7 space-y-4">
          <ChatWindow messages={messages} />
          <ChatInput onSend={handleSendQuery} loading={loading} />
        </div>
      </div>
    </div>
  );
}
