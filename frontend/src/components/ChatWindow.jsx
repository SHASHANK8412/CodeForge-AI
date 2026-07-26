import React from 'react';
import { FaRobot, FaUser, FaBookOpen } from 'react-icons/fa';

export default function ChatWindow({ messages = [] }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 min-h-[320px] max-h-[460px] overflow-y-auto space-y-4 shadow-xl font-mono text-xs">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center min-h-[260px] text-center space-y-3 text-slate-500">
          <div className="bg-indigo-950/60 p-3 rounded-full border border-indigo-800 text-indigo-400">
            <FaBookOpen className="w-6 h-6" />
          </div>
          <p className="text-xs max-w-sm">
            Ask questions grounded in your uploaded project documents. The RAG pipeline will query ChromaDB and answer directly from context.
          </p>
        </div>
      ) : (
        messages.map((msg, index) => (
          <div
            key={index}
            className={`flex gap-3 p-3.5 rounded-xl border transition ${
              msg.sender === 'user'
                ? 'bg-slate-950 border-slate-800 text-slate-200 ml-8'
                : 'bg-indigo-950/40 border-indigo-800/60 text-indigo-100 mr-8'
            }`}
          >
            <div className="mt-0.5 shrink-0">
              {msg.sender === 'user' ? (
                <div className="bg-slate-800 p-1.5 rounded-full text-slate-300">
                  <FaUser className="w-3.5 h-3.5" />
                </div>
              ) : (
                <div className="bg-indigo-600 p-1.5 rounded-full text-white">
                  <FaRobot className="w-3.5 h-3.5" />
                </div>
              )}
            </div>

            <div className="space-y-1.5 min-w-0 flex-1">
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                {msg.sender === 'user' ? 'You' : 'AIForge RAG Assistant'}
              </div>
              <div className="whitespace-pre-wrap leading-relaxed">{msg.text}</div>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] text-emerald-400">
                  <span className="font-semibold">Sources Cited:</span> {msg.sources.join(', ')}
                </div>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
