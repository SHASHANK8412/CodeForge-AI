import React from 'react';
import { FaTerminal, FaCheckCircle, FaSpinner, FaCircle, FaPlay, FaCode, FaFolder, FaShieldAlt } from 'react-icons/fa';

export default function ProductPreview() {
  return (
    <section className="py-16 bg-[#090d16] font-sans border-t border-slate-800/60 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-10">
          <h2 className="text-xs uppercase tracking-widest font-mono text-cyan-400 font-bold mb-2">
            Developer IDE Experience
          </h2>
          <p className="text-2xl sm:text-3xl font-extrabold text-white">
            AIForge Project Generation Environment
          </p>
        </div>

        {/* IDE Mockup Window */}
        <div className="max-w-5xl mx-auto bg-slate-950 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden backdrop-blur-md">
          {/* Top Window Bar */}
          <div className="bg-slate-900 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-rose-500/80 inline-block" />
              <span className="w-3 h-3 rounded-full bg-amber-500/80 inline-block" />
              <span className="w-3 h-3 rounded-full bg-emerald-500/80 inline-block" />
              <span className="ml-3 text-xs font-mono text-slate-400">aiforge-ide // ecommerce-platform</span>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded text-[11px] font-mono">
                <FaCircle className="w-2 h-2 animate-pulse" /> Live Generation
              </div>
              <span className="text-xs font-mono text-cyan-400 font-bold">Progress: 45%</span>
            </div>
          </div>

          {/* IDE Content Layout */}
          <div className="grid grid-cols-1 md:grid-cols-12 min-h-[420px]">
            {/* Sidebar: File Explorer & Agent Status */}
            <div className="md:col-span-4 bg-slate-900/60 border-r border-slate-800 p-4 flex flex-col justify-between">
              <div>
                <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
                  <FaFolder className="text-indigo-400" /> Active Agents (E-Commerce Platform)
                </div>

                {/* Agent Status List */}
                <div className="space-y-2 text-xs">
                  {/* Planner Agent */}
                  <div className="flex items-center justify-between p-2 rounded bg-slate-900/90 border border-slate-800">
                    <span className="font-semibold text-slate-200">Planner Agent</span>
                    <span className="text-emerald-400 flex items-center gap-1 font-mono text-[11px]">
                      <FaCheckCircle className="w-3 h-3" /> Completed
                    </span>
                  </div>

                  {/* Architect Agent */}
                  <div className="flex items-center justify-between p-2 rounded bg-slate-900/90 border border-slate-800">
                    <span className="font-semibold text-slate-200">Architect Agent</span>
                    <span className="text-emerald-400 flex items-center gap-1 font-mono text-[11px]">
                      <FaCheckCircle className="w-3 h-3" /> Completed
                    </span>
                  </div>

                  {/* Frontend Agent */}
                  <div className="flex items-center justify-between p-2 rounded bg-indigo-950/50 border border-indigo-500/30">
                    <span className="font-bold text-cyan-300">Frontend Agent</span>
                    <span className="text-cyan-400 flex items-center gap-1 font-mono text-[11px]">
                      <FaSpinner className="w-3 h-3 animate-spin" /> Generating...
                    </span>
                  </div>

                  {/* Backend Agent */}
                  <div className="flex items-center justify-between p-2 rounded bg-slate-950 opacity-60">
                    <span className="text-slate-400">Backend Agent</span>
                    <span className="text-slate-500 font-mono text-[11px]">Waiting</span>
                  </div>

                  {/* Database Agent */}
                  <div className="flex items-center justify-between p-2 rounded bg-slate-950 opacity-60">
                    <span className="text-slate-400">Database Agent</span>
                    <span className="text-slate-500 font-mono text-[11px]">Waiting</span>
                  </div>

                  {/* Reviewer Agent */}
                  <div className="flex items-center justify-between p-2 rounded bg-slate-950 opacity-60">
                    <span className="text-slate-400">Reviewer Agent</span>
                    <span className="text-slate-500 font-mono text-[11px]">Waiting</span>
                  </div>

                  {/* Testing Agent */}
                  <div className="flex items-center justify-between p-2 rounded bg-slate-950 opacity-60">
                    <span className="text-slate-400">Testing Agent</span>
                    <span className="text-slate-500 font-mono text-[11px]">Waiting</span>
                  </div>
                </div>
              </div>

              {/* Progress Bar Container */}
              <div className="mt-4 pt-3 border-t border-slate-800">
                <div className="flex justify-between text-xs text-slate-400 mb-1">
                  <span>Overall Pipeline</span>
                  <span className="font-mono text-cyan-400">45%</span>
                </div>
                <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                  <div className="bg-gradient-to-r from-cyan-500 to-indigo-500 h-full w-[45%] transition-all duration-500" />
                </div>
              </div>
            </div>

            {/* Code Editor & Live Stream Window */}
            <div className="md:col-span-8 bg-slate-950 p-4 font-mono text-xs text-slate-300 flex flex-col justify-between">
              {/* Code Tab Bar */}
              <div>
                <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                  <span className="px-3 py-1 bg-slate-900 text-cyan-400 border border-cyan-500/30 rounded-t text-[11px] font-bold flex items-center gap-1.5">
                    <FaCode className="w-3 h-3" /> src/components/ProductCatalog.jsx
                  </span>
                  <span className="px-3 py-1 text-slate-500 hover:text-slate-300 text-[11px]">
                    backend/main.py
                  </span>
                  <span className="px-3 py-1 text-slate-500 hover:text-slate-300 text-[11px]">
                    database/schema.sql
                  </span>
                </div>

                {/* Code Snippet */}
                <pre className="text-slate-300 leading-relaxed overflow-x-auto p-2 bg-slate-900/40 rounded border border-slate-800/60">
                  <code>{`import React, { useState, useEffect } from 'react';
import { ShoppingCart, Star } from 'lucide-react';

export default function ProductCatalog({ category = 'all' }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch products from FastAPI REST API endpoint
    fetch('/api/products?category=' + category)
      .then(res => res.json())
      .then(data => {
        setProducts(data.items);
        setLoading(false);
      });
  }, [category]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-6">
      {products.map(item => (
        <ProductCard key={item.id} product={item} />
      ))}
    </div>
  );
}`}</code>
                </pre>
              </div>

              {/* Real-time Agent Log Footer */}
              <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                <span className="flex items-center gap-2">
                  <FaTerminal className="text-cyan-400" />
                  <span className="text-slate-300">[FrontendAgent]</span> Generating responsive ProductCatalog component...
                </span>
                <span className="text-slate-500">Ollama // Qwen 2.5 Coder</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
