import React, { useState, useMemo } from "react";
import { 
  FaCode, FaPenNib, FaGraduationCap, FaFlask, FaRocket, 
  FaSearch, FaBrain, FaShieldAlt, FaComments, FaHistory, 
  FaChartBar, FaArrowRight, FaServer, FaFileAlt, FaProjectDiagram
} from "react-icons/fa";

export default function AIToolsSection({ setView }) {
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");

  const categories = ["All", "Coding", "Writing", "Study", "Research", "Productivity"];

  const tools = useMemo(() => [
    // Coding Category
    {
      id: "tool-workspace",
      name: "Code Workspace",
      category: "Coding",
      badge: "IDE Engine",
      description: "Full-featured Monaco IDE with real-time multi-agent file tree generation, terminal execution, and diff viewer.",
      icon: <FaCode className="text-violet-400" />,
      action: () => setView("code"),
      tags: ["Monaco", "Terminal", "FastAPI", "React"]
    },
    {
      id: "tool-copilot",
      name: "Codebase Copilot",
      category: "Coding",
      badge: "Context AI",
      description: "Ask questions across your entire repository with RAG semantic indexing and AST symbol tracing.",
      icon: <FaComments className="text-cyan-400" />,
      action: () => setView("talk"),
      tags: ["RAG", "AST", "Context", "Semantic"]
    },
    {
      id: "tool-bug-hunter",
      name: "Bug Hunter & SAST",
      category: "Coding",
      badge: "Security",
      description: "Automated vulnerability scanner, concurrency race detector, and memory leak analysis engine.",
      icon: <FaShieldAlt className="text-rose-400" />,
      action: () => setView("bug-bounty"),
      tags: ["SAST", "CVE", "Fuzzing", "Audit"]
    },
    {
      id: "tool-dna",
      name: "DNA Graph & AST",
      category: "Coding",
      badge: "Topology",
      description: "Interactive visual dependency graph showing module relationships, import trees, and circular references.",
      icon: <FaProjectDiagram className="text-emerald-400" />,
      action: () => setView("dna"),
      tags: ["AST Graph", "Imports", "Metrics"]
    },

    // Writing Category
    {
      id: "tool-srs",
      name: "SRS System Architect",
      category: "Writing",
      badge: "Spec Generator",
      description: "Generate comprehensive IEEE 830 Software Requirements Specifications and technical blueprints.",
      icon: <FaPenNib className="text-pink-400" />,
      action: () => setView("create"),
      tags: ["IEEE 830", "RFC", "Architecture", "PRD"]
    },
    {
      id: "tool-api-docs",
      name: "API Documentation Generator",
      category: "Writing",
      badge: "OpenAPI",
      description: "Auto-generate OpenAPI 3.1 Swagger specifications, Markdown API reference, and Postman collections.",
      icon: <FaFileAlt className="text-amber-400" />,
      action: () => setView("chat"),
      tags: ["OpenAPI", "Swagger", "Postman", "Markdown"]
    },
    {
      id: "tool-release-notes",
      name: "Release Notes & Changelog",
      category: "Writing",
      badge: "Git Flow",
      description: "Synthesize git commits, pull requests, and automated test summaries into clean release notes.",
      icon: <FaPenNib className="text-cyan-400" />,
      action: () => setView("history"),
      tags: ["Changelog", "SemVer", "Commits"]
    },

    // Study Category
    {
      id: "tool-code-explainer",
      name: "Algorithm & Code Explainer",
      category: "Study",
      badge: "Deep Dive",
      description: "Line-by-line interactive breakdown of complex algorithms, regex engines, and concurrency patterns.",
      icon: <FaGraduationCap className="text-blue-400" />,
      action: () => setView("talk"),
      tags: ["Algorithms", "Big-O", "Education"]
    },
    {
      id: "tool-design-patterns",
      name: "Design Pattern Tutor",
      category: "Study",
      badge: "Architecture",
      description: "Learn and refactor Gang-of-Four & Enterprise Architecture patterns tailored to your stack.",
      icon: <FaGraduationCap className="text-violet-400" />,
      action: () => setView("learning"),
      tags: ["GoF", "DDD", "Clean Architecture"]
    },
    {
      id: "tool-memory-graph",
      name: "Memory Graph & Knowledge Base",
      category: "Study",
      badge: "Persistent AI",
      description: "Explore versioned engineering decisions, architectural trade-offs, and learned conventions.",
      icon: <FaBrain className="text-emerald-400" />,
      action: () => setView("project-overview"),
      tags: ["Decisions", "Knowledge", "Graph"]
    },

    // Research Category
    {
      id: "tool-debate",
      name: "Multi-Agent Debate Arena",
      category: "Research",
      badge: "Consensus",
      description: "Dual-agent dialectic debate between Architect Agent and Performance Agent to find optimal designs.",
      icon: <FaFlask className="text-indigo-400" />,
      action: () => setView("debate"),
      tags: ["Debate", "Multi-Agent", "Synthesis"]
    },
    {
      id: "tool-benchmark",
      name: "Tech Stack Evaluator",
      category: "Research",
      badge: "Empirical",
      description: "Compare frameworks, databases, and libraries with empirical latency, memory, and scalability benchmarks.",
      icon: <FaFlask className="text-cyan-400" />,
      action: () => setView("evaluations"),
      tags: ["Benchmarks", "Latency", "Scalability"]
    },
    {
      id: "tool-simulator",
      name: "Execution Simulator",
      category: "Research",
      badge: "Sandbox",
      description: "Simulate multi-user load spikes, network latency jitter, and database failovers before deployment.",
      icon: <FaFlask className="text-pink-400" />,
      action: () => setView("simulator"),
      tags: ["Chaos", "Simulation", "Load Test"]
    },

    // Productivity Category
    {
      id: "tool-autopilot",
      name: "Autopilot Orchestrator",
      category: "Productivity",
      badge: "Autonomous",
      description: "Self-directed agent that runs autonomous coding, test-driven validation, and auto-repair loops.",
      icon: <FaRocket className="text-violet-400" />,
      action: () => setView("autopilot"),
      tags: ["Autonomous", "Self-Healing", "Loops"]
    },
    {
      id: "tool-devops",
      name: "DevOps & Cloud Deployer",
      category: "Productivity",
      badge: "CI / CD",
      description: "1-click deploy to Vercel, Docker, AWS ECS, and Kubernetes with automatic TLS and edge caching.",
      icon: <FaServer className="text-emerald-400" />,
      action: () => setView("deploy"),
      tags: ["Docker", "Kubernetes", "Edge"]
    },
    {
      id: "tool-flight-recorder",
      name: "Flight Recorder Time Machine",
      category: "Productivity",
      badge: "Telemetry",
      description: "Step backward and forward through agent execution steps, prompt histories, and AST diff evolutions.",
      icon: <FaHistory className="text-amber-400" />,
      action: () => setView("flight-recorder"),
      tags: ["Replay", "Audit", "State Machine"]
    },
    {
      id: "tool-observability",
      name: "APM Observability Hub",
      category: "Productivity",
      badge: "Telemetry",
      description: "Live CPU, memory, request tracing, p99 latency heatmaps, and structured agent execution logs.",
      icon: <FaChartBar className="text-cyan-400" />,
      action: () => setView("observability"),
      tags: ["APM", "Logs", "Metrics", "Traces"]
    }
  ], [setView]);

  // Filter tools by category and search
  const filteredTools = useMemo(() => {
    return tools.filter(tool => {
      const matchesCat = selectedCategory === "All" || tool.category === selectedCategory;
      const matchesQuery = !searchQuery.trim() || 
        tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchesCat && matchesQuery;
    });
  }, [tools, selectedCategory, searchQuery]);

  return (
    <div className="space-y-4">
      {/* Header and Category Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded-md bg-cyan-500/20 text-cyan-400">
              <FaBrain size={12} />
            </span>
            <h2 className="text-sm font-bold text-white tracking-tight">
              AI Tools & Specialized Engines
            </h2>
          </div>
          <p className="text-[11px] text-[#64748B] mt-0.5">
            Categorized AI engineering tools for every stage of your development lifecycle
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
          {/* Search bar */}
          <div className="relative w-full sm:w-44">
            <FaSearch className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#64748B]" size={10} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search tools..."
              className="w-full bg-[#151821] border border-[#242833] focus:border-[#8D5CF6] rounded-xl pl-7 pr-2.5 py-1 text-xs text-white placeholder-[#64748B] outline-none"
            />
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 custom-scrollbar">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1 rounded-xl text-xs font-semibold transition-all shrink-0 cursor-pointer ${
                  selectedCategory === cat
                    ? "bg-[#8D5CF6] text-white shadow-md shadow-violet-500/20"
                    : "bg-[#151821] hover:bg-[#1E2330] text-[#9AA1B2] hover:text-white border border-[#242833]"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3.5">
        {filteredTools.map((tool) => (
          <div
            key={tool.id}
            onClick={tool.action}
            className="bg-[#0F1117]/80 hover:bg-[#151821] border border-[#242833] hover:border-[#8D5CF6]/50 rounded-2xl p-4 flex flex-col justify-between transition-all group cursor-pointer relative overflow-hidden"
          >
            <div>
              <div className="flex items-center justify-between gap-2 mb-3">
                <div className="p-2 rounded-xl bg-[#151821] group-hover:bg-violet-600/20 text-lg transition-colors">
                  {tool.icon}
                </div>
                <span className="px-2 py-0.5 rounded-full bg-[#151821] border border-[#242833] text-[#9AA1B2] text-[10px] font-mono font-bold uppercase">
                  {tool.badge}
                </span>
              </div>

              <h3 className="text-xs font-bold text-white group-hover:text-violet-300 transition-colors">
                {tool.name}
              </h3>

              <p className="text-[11px] text-[#9AA1B2] mt-1.5 line-clamp-2 leading-relaxed">
                {tool.description}
              </p>
            </div>

            <div className="pt-3 mt-3 border-t border-[#1C202B] flex items-center justify-between">
              <div className="flex items-center gap-1.5 flex-wrap">
                {tool.tags.slice(0, 2).map((t, idx) => (
                  <span key={idx} className="text-[9px] font-mono text-[#64748B]">
                    #{t}
                  </span>
                ))}
              </div>
              <span className="text-xs font-bold text-[#8D5CF6] group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
                Launch <FaArrowRight size={8} />
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
