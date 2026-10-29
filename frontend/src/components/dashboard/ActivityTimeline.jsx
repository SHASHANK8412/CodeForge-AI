import React, { useState, useEffect, useMemo } from "react";
import { 
  FaHistory, FaCheckCircle, FaExclamationCircle, FaInfoCircle, 
  FaArrowRight, FaCode, FaShieldAlt, FaComments, FaRocket, FaFilter 
} from "react-icons/fa";
import { getActivityLog } from "../../utils/workspaceStorage";

export default function ActivityTimeline({ setView }) {
  const [activities, setActivities] = useState([]);
  const [selectedFilter, setSelectedFilter] = useState("all");

  const refreshActivities = () => {
    setActivities(getActivityLog());
  };

  useEffect(() => {
    refreshActivities();
    const handleLog = () => refreshActivities();
    window.addEventListener("aiforge:activity-logged", handleLog);
    return () => window.removeEventListener("aiforge:activity-logged", handleLog);
  }, []);

  const filteredActivities = useMemo(() => {
    if (selectedFilter === "all") return activities;
    return activities.filter(act => act.type === selectedFilter);
  }, [activities, selectedFilter]);

  const getIcon = (type) => {
    switch (type) {
      case "project":
        return <FaCode className="text-violet-400" size={11} />;
      case "security":
        return <FaShieldAlt className="text-cyan-400" size={11} />;
      case "debate":
        return <FaComments className="text-indigo-400" size={11} />;
      case "autopilot":
        return <FaRocket className="text-emerald-400" size={11} />;
      default:
        return <FaHistory className="text-[#9AA1B2]" size={11} />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Header and Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded-md bg-emerald-500/20 text-emerald-400">
              <FaHistory size={12} />
            </span>
            <h2 className="text-sm font-bold text-white tracking-tight">
              Recent Activity & Execution Timeline
            </h2>
          </div>
          <p className="text-[11px] text-[#64748B] mt-0.5">
            Audit trail of multi-agent operations, builds, security scans, and code generations
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedFilter}
            onChange={(e) => setSelectedFilter(e.target.value)}
            className="bg-[#151821] border border-[#242833] rounded-xl px-2.5 py-1 text-xs text-[#9AA1B2] outline-none cursor-pointer"
          >
            <option value="all">All Events</option>
            <option value="project">Project Builds</option>
            <option value="security">Security Audits</option>
            <option value="debate">Debate Arena</option>
            <option value="autopilot">Autopilot</option>
          </select>

          {setView && (
            <button
              onClick={() => setView("history")}
              className="text-xs text-[#8D5CF6] hover:text-[#a78bfa] font-semibold transition px-2 py-1 cursor-pointer"
            >
              Full Log →
            </button>
          )}
        </div>
      </div>

      {/* Activity Timeline List */}
      <div className="bg-[#0F1117]/80 border border-[#242833] rounded-2xl p-4 sm:p-5 space-y-4 shadow-xl">
        <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-[#242833]">
          {filteredActivities.map((act) => (
            <div key={act.id} className="relative group">
              {/* Timeline Bullet Dot */}
              <div className="absolute -left-6 sm:-left-8 top-1 w-6 h-6 rounded-full bg-[#151821] border border-[#242833] group-hover:border-[#8D5CF6] flex items-center justify-center transition-colors shadow">
                {getIcon(act.type)}
              </div>

              {/* Event Content */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-white group-hover:text-violet-300 transition-colors">
                      {act.title}
                    </span>
                    <span className="px-1.5 py-0.2 rounded bg-[#151821] text-[9px] font-mono text-[#64748B] uppercase">
                      {act.type}
                    </span>
                  </div>
                  <p className="text-[11px] text-[#9AA1B2] leading-relaxed">
                    {act.description}
                  </p>
                </div>

                <div className="flex items-center gap-3 shrink-0 pt-1 sm:pt-0">
                  <span className="text-[10px] font-mono text-[#64748B]">
                    {act.timestamp}
                  </span>
                  {act.actionLink && setView && (
                    <button
                      onClick={() => setView(act.actionLink)}
                      className="text-xs font-semibold text-[#8D5CF6] hover:text-white flex items-center gap-1 transition cursor-pointer"
                    >
                      <span>{act.actionLabel || "Inspect"}</span>
                      <FaArrowRight size={8} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
