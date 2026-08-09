import React from 'react';
import { FaDesktop, FaServer, FaDatabase, FaPaintBrush } from 'react-icons/fa';

export default function TechnologySelector({ stack, setStack }) {
  const handleChange = (key, value) => {
    setStack({ ...stack, [key]: value });
  };

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl backdrop-blur-md font-sans">
      <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 border-b border-slate-800 pb-2">
        Technology Stack
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-sans">
        {/* Frontend */}
        <div>
          <label className="text-slate-300 font-semibold mb-1.5 flex items-center gap-1.5">
            <FaDesktop className="text-cyan-400" /> Frontend Framework
          </label>
          <select
            value={stack.frontend}
            onChange={(e) => handleChange('frontend', e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2.5 text-slate-200 focus:outline-none focus:border-cyan-500 font-medium"
          >
            <option value="React">React</option>
            <option value="Next.js">Next.js</option>
            <option value="Vue">Vue</option>
            <option value="Angular">Angular</option>
          </select>
        </div>

        {/* Backend */}
        <div>
          <label className="text-slate-300 font-semibold mb-1.5 flex items-center gap-1.5">
            <FaServer className="text-indigo-400" /> Backend Engine
          </label>
          <select
            value={stack.backend}
            onChange={(e) => handleChange('backend', e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2.5 text-slate-200 focus:outline-none focus:border-indigo-500 font-medium"
          >
            <option value="FastAPI">FastAPI</option>
            <option value="Node.js + Express">Node.js + Express</option>
            <option value="Django">Django</option>
            <option value="Spring Boot">Spring Boot</option>
          </select>
        </div>

        {/* Database */}
        <div>
          <label className="text-slate-300 font-semibold mb-1.5 flex items-center gap-1.5">
            <FaDatabase className="text-purple-400" /> Database Persistence
          </label>
          <select
            value={stack.database}
            onChange={(e) => handleChange('database', e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2.5 text-slate-200 focus:outline-none focus:border-purple-500 font-medium"
          >
            <option value="PostgreSQL">PostgreSQL</option>
            <option value="MongoDB">MongoDB</option>
            <option value="MySQL">MySQL</option>
            <option value="SQLite">SQLite</option>
          </select>
        </div>

        {/* Styling */}
        <div>
          <label className="text-slate-300 font-semibold mb-1.5 flex items-center gap-1.5">
            <FaPaintBrush className="text-teal-400" /> Styling System
          </label>
          <select
            value={stack.styling}
            onChange={(e) => handleChange('styling', e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2.5 text-slate-200 focus:outline-none focus:border-teal-500 font-medium"
          >
            <option value="Tailwind CSS">Tailwind CSS</option>
            <option value="CSS">CSS</option>
            <option value="Material UI">Material UI</option>
            <option value="Bootstrap">Bootstrap</option>
          </select>
        </div>
      </div>
    </div>
  );
}
