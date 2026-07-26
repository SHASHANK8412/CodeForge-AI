import React, { useState } from 'react';
import { FaPaperPlane } from 'react-icons/fa';

export default function ChatInput({ onSend, loading }) {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim() || loading) return;
    onSend(text);
    setText('');
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Ask a question about uploaded PRD & project docs..."
        disabled={loading}
        className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={!text.trim() || loading}
        className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-semibold text-xs px-4 py-2.5 rounded-lg transition flex items-center gap-2 cursor-pointer shadow"
      >
        <FaPaperPlane className="w-3 h-3" />
        <span>Ask AI</span>
      </button>
    </form>
  );
}
