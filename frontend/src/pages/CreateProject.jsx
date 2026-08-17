import React, { useState } from 'react';
import { FaArrowLeft, FaPlus, FaCheck, FaCog, FaChevronDown, FaChevronUp, FaSpinner } from 'react-icons/fa';
import { submitProjectGeneration } from '../services/api';

export default function CreateProject({ setView, onGenerateSuccess }) {
  const [projectName, setProjectName] = useState('TaskForge AI');
  const [description, setDescription] = useState(() => {
    const pending = sessionStorage.getItem("aiforge_pending_prompt");
    if (pending) {
      sessionStorage.removeItem("aiforge_pending_prompt");
      return pending;
    }
    return 'Build a modern real-time task manager SaaS. Users can register, log in, create boards and lists, drag and drop tasks, invite team members, assign work, track status, and view basic velocity charts. Backed by a secure database.';
  });

  const [stack, setStack] = useState({
    frontend: 'React',
    backend: 'FastAPI',
    database: 'PostgreSQL',
    styling: 'Tailwind CSS'
  });

  const [options, setOptions] = useState({
    authentication: true,
    testing: true,
    documentation: true,
    docker: true,
    readme_generation: true,
    security_review: true,
    local_llm: true,
    model: 'qwen2.5-coder',
    rag: true,
    code_review: true,
    auto_repair: true
  });

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [nameError, setNameError] = useState(false);

  const handleBack = () => {
    if (setView) setView('dashboard');
    else window.location.href = '/';
  };

  const handleSuggestion = (promptText, defaultName) => {
    setDescription(promptText);
    setProjectName(defaultName);
  };

  const handleSubmit = async () => {
    setErrorMessage('');
    setNameError(false);

    if (!projectName || projectName.trim().length === 0) {
      setNameError(true);
      setErrorMessage('Project Name cannot be empty.');
      return;
    }

    if (!description || description.trim().length === 0) {
      setErrorMessage('Please describe what software project you want AIForge to build.');
      return;
    }

    setSubmitting(true);

    const payload = {
      project_name: projectName.trim(),
      description: description.trim(),
      frontend: stack.frontend,
      backend: stack.backend,
      database: stack.database,
      styling: stack.styling,
      authentication: options.authentication,
      testing: options.testing,
      documentation: options.documentation,
      docker: options.docker,
      security_review: options.security_review,
      local_llm: options.local_llm,
      model: options.model,
      rag: options.rag,
      code_review: options.code_review,
      auto_repair: options.auto_repair
    };

    try {
      const res = await submitProjectGeneration(payload);
      setSubmitting(false);

      if (res.success) {
        const generationId = res.generation_id || `aiforge-${Date.now()}`;
        if (onGenerateSuccess) {
          onGenerateSuccess(generationId, projectName);
        } else if (setView) {
          setView('build');
        } else {
          window.location.href = `/projects/${generationId}/build`;
        }
      } else {
        setErrorMessage(res.error || 'AIForge could not start the project generation.');
      }
    } catch (err) {
      setSubmitting(false);
      setErrorMessage('API request failed. Ensure the backend server is running.');
    }
  };

  const suggestions = [
    {
      label: "🛒 E-Commerce App",
      name: "ShopAI SaaS",
      text: "Build an e-commerce platform with stripe payment gateway integration. Include user registration, shopping carts, checkout forms, order details pages, product catalog searching, and merchant admin panel dashboards."
    },
    {
      label: "📄 Resume Analyzer",
      name: "CVForge AI",
      text: "Build an AI resume analyzer SaaS. Users upload PDF resumes, parsing extracts metadata, and custom models rate skills alignment against job descriptions, recommending corrections and optimizations."
    },
    {
      label: "💬 Real-Time Chat",
      name: "TalkRoom",
      text: "Build a real-time collaborative chat application utilizing websockets. Users can create private rooms, invite guests, send text/markdown, view presence status indicators, and browse past messages."
    }
  ];

  return (
    <div className="min-h-screen bg-[#08090D] text-[#F5F7FA] font-sans p-6">
      {/* Context Top Header */}
      <div className="flex items-center gap-3 border-b border-[#242833] pb-4 mb-6">
        <button
          onClick={handleBack}
          className="text-[#9AA1B2] hover:text-[#F5F7FA] p-1.5 rounded-md hover:bg-[#151821] transition"
        >
          <FaArrowLeft size={12} />
        </button>
        <div className="text-xs text-[#9AA1B2]">
          <span className="hover:underline cursor-pointer" onClick={handleBack}>AIForge</span> / <span className="text-[#F5F7FA] font-bold">New Project</span>
        </div>
      </div>

      <div className="max-w-3xl mx-auto py-4 space-y-6">
        {/* Title */}
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight text-[#F5F7FA]">Build something amazing.</h1>
          <p className="text-xs text-[#9AA1B2]">Tell AIForge what software application you want. Multiple specialized agents will coordinate, plan, build, review, and deploy it.</p>
        </div>

        {/* Prompt Card */}
        <div className="bg-[#0F1117] border border-[#242833] rounded-xl p-5 space-y-4">
          <div className="space-y-2">
            <label className="block text-xs font-bold uppercase tracking-wider text-[#9AA1B2]">Application Requirements</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe your application here..."
              rows={6}
              className="w-full bg-[#08090D] border border-[#242833] rounded-lg p-3 text-xs text-[#F5F7FA] placeholder-[#9AA1B2]/40 focus:border-[#8D5CF6] focus:ring-1 focus:ring-[#8D5CF6] outline-none font-mono resize-none leading-relaxed transition"
            />
          </div>

          {/* Quick Suggestions */}
          <div className="space-y-1.5">
            <span className="block text-[10px] uppercase font-bold text-[#9AA1B2]/60">Quick Examples</span>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSuggestion(item.text, item.name)}
                  className="bg-[#151821] hover:bg-[#1f2330] border border-[#242833] text-xs py-1.5 px-3 rounded-md text-[#9AA1B2] hover:text-[#F5F7FA] transition cursor-pointer"
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div className="space-y-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-[#9AA1B2]">Project Name</label>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="e.g. food delivery saas"
                className={`w-full bg-[#08090D] border rounded-lg px-3 py-2 text-xs text-[#F5F7FA] placeholder-[#9AA1B2]/40 outline-none focus:border-[#8D5CF6] transition ${
                  nameError ? "border-red-500" : "border-[#242833]"
                }`}
              />
            </div>
            <div className="space-y-2 flex flex-col justify-end">
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="w-full flex items-center justify-center gap-2 bg-[#8D5CF6] hover:bg-[#7c4ee4] disabled:bg-[#8D5CF6]/50 text-white rounded-lg py-2.5 px-4 text-xs font-bold transition shadow-lg shadow-violet-500/25 active:scale-95"
              >
                {submitting ? (
                  <>
                    <FaSpinner className="animate-spin" />
                    <span>Analyzing requirements...</span>
                  </>
                ) : (
                  <>
                    <span>Generate Project</span>
                    <span>→</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Error Dialog */}
        {errorMessage && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-xs rounded-lg p-4 flex items-center justify-between">
            <span>{errorMessage}</span>
            <button onClick={handleSubmit} className="underline hover:text-white font-bold ml-4">Retry</button>
          </div>
        )}

        {/* Advanced Settings Accordion */}
        <div className="bg-[#0F1117] border border-[#242833] rounded-xl overflow-hidden">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="w-full p-4 flex items-center justify-between text-xs font-bold text-[#F5F7FA] hover:bg-[#151821]/40 transition border-b border-transparent"
          >
            <div className="flex items-center gap-2.5">
              <FaCog size={13} className="text-[#8D5CF6]" />
              <span>Advanced Engineering Configuration</span>
            </div>
            {showAdvanced ? <FaChevronUp size={11} /> : <FaChevronDown size={11} />}
          </button>

          {showAdvanced && (
            <div className="p-5 border-t border-[#242833] space-y-6 animate-fade-in">
              {/* Tech Stack Selectors */}
              <div className="space-y-3">
                <span className="block text-xs font-bold uppercase tracking-wider text-[#9AA1B2]">Target Tech Stack</span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="space-y-1">
                    <span className="block text-[10px] text-[#9AA1B2] font-mono">FRONTEND</span>
                    <select
                      value={stack.frontend}
                      onChange={(e) => setStack({ ...stack, frontend: e.target.value })}
                      className="w-full bg-[#08090D] border border-[#242833] rounded-md px-2 py-1.5 text-xs text-[#F5F7FA] outline-none focus:border-[#8D5CF6]"
                    >
                      <option value="React">React (Vite)</option>
                      <option value="Next.js">Next.js</option>
                      <option value="Vue">Vue</option>
                      <option value="HTML/JS">Vanilla JS</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <span className="block text-[10px] text-[#9AA1B2] font-mono">BACKEND</span>
                    <select
                      value={stack.backend}
                      onChange={(e) => setStack({ ...stack, backend: e.target.value })}
                      className="w-full bg-[#08090D] border border-[#242833] rounded-md px-2 py-1.5 text-xs text-[#F5F7FA] outline-none focus:border-[#8D5CF6]"
                    >
                      <option value="FastAPI">FastAPI (Python)</option>
                      <option value="Express">Express (Node)</option>
                      <option value="Django">Django (Python)</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <span className="block text-[10px] text-[#9AA1B2] font-mono">DATABASE</span>
                    <select
                      value={stack.database}
                      onChange={(e) => setStack({ ...stack, database: e.target.value })}
                      className="w-full bg-[#08090D] border border-[#242833] rounded-md px-2 py-1.5 text-xs text-[#F5F7FA] outline-none focus:border-[#8D5CF6]"
                    >
                      <option value="PostgreSQL">PostgreSQL</option>
                      <option value="SQLite">SQLite</option>
                      <option value="MongoDB">MongoDB</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <span className="block text-[10px] text-[#9AA1B2] font-mono">STYLING</span>
                    <select
                      value={stack.styling}
                      onChange={(e) => setStack({ ...stack, styling: e.target.value })}
                      className="w-full bg-[#08090D] border border-[#242833] rounded-md px-2 py-1.5 text-xs text-[#F5F7FA] outline-none focus:border-[#8D5CF6]"
                    >
                      <option value="Tailwind CSS">Tailwind CSS</option>
                      <option value="Vanilla CSS">Vanilla CSS</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Engine Toggles */}
              <div className="space-y-3">
                <span className="block text-xs font-bold uppercase tracking-wider text-[#9AA1B2]">Engine Checkpoints & Gates</span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="flex items-start justify-between bg-[#08090D] border border-[#242833] p-3 rounded-lg">
                    <div>
                      <span className="block text-xs font-bold text-[#F5F7FA]">User Authentication</span>
                      <span className="block text-[10px] text-[#9AA1B2] mt-0.5">Generate routes, JWT authorization models.</span>
                    </div>
                    <button
                      onClick={() => setOptions({ ...options, authentication: !options.authentication })}
                      className={`px-3 py-1 text-[10px] font-bold rounded-md border transition ${
                        options.authentication 
                          ? "bg-[#8D5CF6]/10 text-[#8D5CF6] border-[#8D5CF6]/30" 
                          : "bg-transparent text-[#9AA1B2] border-[#242833]"
                      }`}
                    >
                      {options.authentication ? "Enabled" : "Disabled"}
                    </button>
                  </div>

                  <div className="flex items-start justify-between bg-[#08090D] border border-[#242833] p-3 rounded-lg">
                    <div>
                      <span className="block text-xs font-bold text-[#F5F7FA]">Test Pipeline Generators</span>
                      <span className="block text-[10px] text-[#9AA1B2] mt-0.5">Draft pytest and unit testing frameworks.</span>
                    </div>
                    <button
                      onClick={() => setOptions({ ...options, testing: !options.testing })}
                      className={`px-3 py-1 text-[10px] font-bold rounded-md border transition ${
                        options.testing 
                          ? "bg-[#8D5CF6]/10 text-[#8D5CF6] border-[#8D5CF6]/30" 
                          : "bg-transparent text-[#9AA1B2] border-[#242833]"
                      }`}
                    >
                      {options.testing ? "Enabled" : "Disabled"}
                    </button>
                  </div>

                  <div className="flex items-start justify-between bg-[#08090D] border border-[#242833] p-3 rounded-lg">
                    <div>
                      <span className="block text-xs font-bold text-[#F5F7FA]">DevSecOps Review</span>
                      <span className="block text-[10px] text-[#9AA1B2] mt-0.5">Scans credentials and checks for path traversals.</span>
                    </div>
                    <button
                      onClick={() => setOptions({ ...options, security_review: !options.security_review })}
                      className={`px-3 py-1 text-[10px] font-bold rounded-md border transition ${
                        options.security_review 
                          ? "bg-[#8D5CF6]/10 text-[#8D5CF6] border-[#8D5CF6]/30" 
                          : "bg-transparent text-[#9AA1B2] border-[#242833]"
                      }`}
                    >
                      {options.security_review ? "Enabled" : "Disabled"}
                    </button>
                  </div>

                  <div className="flex items-start justify-between bg-[#08090D] border border-[#242833] p-3 rounded-lg">
                    <div>
                      <span className="block text-xs font-bold text-[#F5F7FA]">Autonomous Repair Loops</span>
                      <span className="block text-[10px] text-[#9AA1B2] mt-0.5">Heals building failures up to 3 repair sessions.</span>
                    </div>
                    <button
                      onClick={() => setOptions({ ...options, auto_repair: !options.auto_repair })}
                      className={`px-3 py-1 text-[10px] font-bold rounded-md border transition ${
                        options.auto_repair 
                          ? "bg-[#8D5CF6]/10 text-[#8D5CF6] border-[#8D5CF6]/30" 
                          : "bg-transparent text-[#9AA1B2] border-[#242833]"
                      }`}
                    >
                      {options.auto_repair ? "Enabled" : "Disabled"}
                    </button>
                  </div>
                </div>
              </div>

              {/* LLM Engine Selection */}
              <div className="space-y-3 pt-2">
                <span className="block text-xs font-bold uppercase tracking-wider text-[#9AA1B2]">LLM Model Spec</span>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="block text-[10px] text-[#9AA1B2] font-mono">SELECTED MODEL</span>
                    <select
                      value={options.model}
                      onChange={(e) => setOptions({ ...options, model: e.target.value })}
                      className="w-full bg-[#08090D] border border-[#242833] rounded-md px-2 py-1.5 text-xs text-[#F5F7FA] outline-none focus:border-[#8D5CF6] mt-1"
                    >
                      <option value="qwen2.5-coder">Qwen 2.5 Coder (Ollama)</option>
                      <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                      <option value="gpt-4o-mini">GPT-4o Mini</option>
                    </select>
                  </div>
                  <div>
                    <span className="block text-[10px] text-[#9AA1B2] font-mono">AGENT KNOWLEDGE GRAPH (RAG)</span>
                    <div className="flex items-center gap-2 mt-2">
                      <input
                        type="checkbox"
                        checked={options.rag}
                        onChange={(e) => setOptions({ ...options, rag: e.target.checked })}
                        className="rounded bg-[#08090D] border-[#242833] text-[#8D5CF6] focus:ring-[#8D5CF6]"
                      />
                      <span className="text-xs text-[#9AA1B2]">Enable codebase context vectors</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
