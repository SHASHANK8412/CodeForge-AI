import React, { useState, useEffect, useMemo } from "react";
import { 
  FaHistory, FaSearch, FaFilter, FaDownload, FaCode, 
  FaShieldAlt, FaComments, FaRocket, FaArrowRight, FaCheckCircle 
} from "react-icons/fa";
import { getActivityLog } from "../utils/workspaceStorage";

export default function ActivityHistoryPage({ setView }) {
  const [activities, setActivities] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState("all");

  const refreshActivities = () => {
    setActivities(getActivityLog());
  };

  useEffect(() => {
    refreshActivities();
    const handleLog = () => refreshActivities();
    window.addEventListener("aiforge:activity-logged", handleLog);
    return () => window.removeEventListener("aiforge:activity-logged", handleLog);
  }, []);

  const handleExportLog = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(activities, null, 2));
    const a = document.createElement("a");
    a.setAttribute("href", dataStr);
    a.setAttribute("download", `aiforge_activity_log_${Date.now()}.json`);
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  const filteredActivities = useMemo(() => {
    return activities.filter(act => {
      const matchesType = selectedType === "all" || act.type === selectedType;
      const q = searchQuery.trim().toLowerCase();
      const matchesQuery = !q || 
        act.title.toLowerCase().includes(q) || 
        act.description.toLowerCase().includes(q) ||
        act.type.toLowerCase().includes(q);
      return matchesType && matchesQuery;
    });
  }, [activities, selectedType, searchQuery]);

  const getIcon = (type) => {
    switch (type) {
      case "project":
        return <FaCode className="text-violet-400" size={12} />;
      case "security":
        return <FaShieldAlt className="text-cyan-400" size={12} />;
      case "debate":
        return <FaComments className="text-indigo-400" size={12} />;
      case "autopilot":
        return <FaRocket className="text-emerald-400" size={12} />;
      default:
        return <FaHistory className="text-[#9AA1B2]" size={12} />;
    }
  };

  return (
    <div className="min-h-full p-6 md:p-8 space-y-6 text-[#F5F7FA] font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#242833]">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400">
              <FaHistory size={14} />
            </span>
            <h1 className="text-xl md:text-2xl font-extrabold text-white tracking-tight">
              Activity History & Audit Log
            </h1>
          </div>
          <p className="text-xs text-[#9AA1B2] mt-1">
            Complete chronological record of all agentic code generations, security audits, and automated runs
          </p>
        </div>

        <button
          onClick={handleExportLog}
          className="flex items-center gap-2 px-4 py-2 bg-[#151821] hover:bg-[#1E2330] border border-[#242833] text-white rounded-xl text-xs font-semibold transition cursor-pointer self-start md:self-auto"
        >
          <FaDownload size={11} className="text-[#8D5CF6]" />
          <span>Export Audit Log</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64748B]" size={12} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search activity events, audits, or agents..."
            className="w-full bg-[#0F1117] border border-[#242833] focus:border-[#8D5CF6] rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-[#64748B] outline-none"
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="bg-[#0F1117] border border-[#242833] rounded-xl px-3 py-2 text-xs text-[#9AA1B2] outline-none cursor-pointer"
          >
            <option value="all">All Event Types</option>
            <option value="project">Project Builds</option>
            <option value="security">Security Audits</option>
            <option value="debate">Debate Arena</option>
            <option value="autopilot">Autopilot Runs</option>
          </select>
        </div>
      </div>

      {/* Timeline List */}
      <div className="bg-[#0F1117]/80 border border-[#242833] rounded-3xl p-6 sm:p-8 space-y-6 shadow-xl">
        {filteredActivities.length === 0 ? (
          <div className="text-center py-12 space-y-2 text-[#64748B]">
            <FaHistory className="mx-auto text-[#242833]" size={28} />
            <p>No activity events match your query.</p>
          </div>
        ) : (
          <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-[#242833]">
            {filteredActivities.map((act) => (
              <div key={act.id} className="relative group">
                {/* Timeline Node */}
                <div className="absolute -left-6 sm:-left-8 top-1 w-6 h-6 rounded-full bg-[#151821] border border-[#242833] group-hover:border-[#8D5CF6] flex items-center justify-center transition-colors shadow">
                  {getIcon(act.type)}
                </div>

                {/* Event Card */}
                <div className="bg-[#151821]/40 hover:bg-[#151821] border border-[#242833] rounded-2xl p-4 transition-all">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-white group-hover:text-violet-300 transition-colors">
                          {act.title}
                        </span>
                        <span className="px-2 py-0.5 rounded-full bg-[#08090D] border border-[#242833] text-[9px] font-mono text-[#9AA1B2] uppercase">
                          {act.type}
                        </span>
                      </div>
                      <p className="text-xs text-[#9AA1B2] leading-relaxed">
                        {act.description}
                      </p>
                    </div>

                    <div className="flex items-center gap-3 shrink-0 pt-2 sm:pt-0">
                      <span className="text-xs font-mono text-[#64748B]">
                        {act.timestamp}
                      </span>
                      {act.actionLink && setView && (
                        <button
                          onClick={() => setView(act.actionLink)}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-[#8D5CF6]/15 hover:bg-[#8D5CF6] text-[#8D5CF6] hover:text-white border border-[#8D5CF6]/30 rounded-xl text-xs font-semibold transition cursor-pointer"
                        >
                          <span>{act.actionLabel || "Inspect"}</span>
                          <FaArrowRight size={8} />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
