import React, { useState } from 'react';
import { HiSparkles } from 'react-icons/hi2';
import { FaSpinner } from 'react-icons/fa';
import { enhancePromptApi } from '../../services/api';

export default function ProjectDescription({ description, setDescription }) {
  const [enhancing, setEnhancing] = useState(false);

  const handleEnhance = async () => {
    setEnhancing(true);
    try {
      const enhanced = await enhancePromptApi(description);
      setDescription(enhanced);
    } catch (err) {
      console.error('Enhance error:', err);
    } finally {
      setEnhancing(false);
    }
  };

  const placeholderText = `Example:\n\nBuild a full-stack food delivery application.\n\nUsers should be able to register and log in,\nbrowse restaurants, search for food, add items\nto a cart, place orders, and track order status.\n\nInclude an admin dashboard for restaurant and\norder management.`;

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl backdrop-blur-md font-sans">
      <div className="flex items-center justify-between mb-3">
        <label className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          What do you want to build?
        </label>
        <button
          type="button"
          onClick={handleEnhance}
          disabled={enhancing}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-cyan-300 hover:text-white bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 rounded-lg transition disabled:opacity-50"
        >
          {enhancing ? <FaSpinner className="w-3 h-3 animate-spin text-cyan-400" /> : <HiSparkles className="w-3 h-3 text-cyan-400" />}
          <span>{enhancing ? 'Enhancing...' : 'AI Enhance Prompt'}</span>
        </button>
      </div>

      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value.slice(0, 5000))}
        placeholder={placeholderText}
        rows={8}
        className="w-full bg-slate-900 border border-slate-800 rounded-xl p-4 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-sans leading-relaxed resize-y transition"
      />

      <div className="flex justify-between items-center mt-2 text-xs text-slate-500 font-mono">
        <span>Detailed descriptions yield higher quality architecture & code generation.</span>
        <span>{description.length} / 5000 characters</span>
      </div>
    </div>
  );
}
