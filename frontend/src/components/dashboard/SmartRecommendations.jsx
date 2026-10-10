import React, { useState } from "react";
import { FaBolt, FaShieldAlt, FaRocket, FaCode, FaTimes, FaArrowRight } from "react-icons/fa";

export default function SmartRecommendations({ setView }) {
  const [recommendations, setRecommendations] = useState([
    {
      id: "rec-1",
      tag: "Security Audit",
      title: "Scan FoodDelivery AI for OWASP Top 10 API Vulnerabilities",
      desc: "Detected 4 new REST routes added today. Run the automated SAST scanner to verify parameter validations.",
      actionLabel: "Run Security Audit",
      icon: <FaShieldAlt className="text-cyan-400" />,
      action: () => setView("security"),
      badgeColor: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
    },
    {
      id: "rec-2",
      tag: "Autopilot Refactor",
      title: "Optimize Async Database Queries with Connection Pooling",
      desc: "Reviewer Agent noted potential connection exhaustion under concurrent load. Launch Autopilot to patch async pool config.",
      actionLabel: "Launch Autopilot",
      icon: <FaRocket className="text-violet-400" />,
      action: () => setView("autopilot"),
      badgeColor: "bg-violet-500/10 text-violet-400 border-violet-500/20"
    },
    {
      id: "rec-3",
      tag: "Workspace Copilot",
      title: "Complete OpenAPI Swagger Documentation for Order Router",
      desc: "Generate full request/response typing and JSON schema definitions for checkout endpoints.",
      actionLabel: "Open in Workspace",
      icon: <FaCode className="text-emerald-400" />,
      action: () => setView("code"),
      badgeColor: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
    }
  ]);

  const dismissRecommendation = (id) => {
    setRecommendations(prev => prev.filter(r => r.id !== id));
  };

  if (recommendations.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="p-1 rounded-md bg-violet-500/20 text-violet-400">
            <FaBolt size={11} />
          </span>
          <h2 className="text-sm font-bold text-white tracking-tight">
            Smart AI Recommendations
          </h2>
        </div>
        <span className="text-[11px] text-[#64748B]">Tailored to your recent coding activity</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {recommendations.map((rec) => (
          <div
            key={rec.id}
            className="bg-[#0F1117]/80 hover:bg-[#151821] border border-[#242833] hover:border-[#8D5CF6]/40 rounded-2xl p-4 flex flex-col justify-between transition-all group relative overflow-hidden"
          >
            <div>
              <div className="flex items-center justify-between gap-2 mb-2.5">
                <span className={`px-2 py-0.5 rounded-full border text-[10px] font-mono font-bold ${rec.badgeColor}`}>
                  {rec.tag}
                </span>
                <button
                  onClick={() => dismissRecommendation(rec.id)}
                  className="text-[#64748B] hover:text-[#9AA1B2] p-1 transition"
                  title="Dismiss recommendation"
                >
                  <FaTimes size={10} />
                </button>
              </div>

              <h3 className="text-xs font-bold text-white group-hover:text-violet-300 transition-colors leading-snug line-clamp-2">
                {rec.title}
              </h3>

              <p className="text-[11px] text-[#9AA1B2] mt-1.5 leading-relaxed line-clamp-2">
                {rec.desc}
              </p>
            </div>

            <div className="pt-3 mt-3 border-t border-[#1C202B] flex items-center justify-between">
              <button
                onClick={rec.action}
                className="flex items-center gap-1.5 text-xs font-bold text-[#8D5CF6] hover:text-white transition cursor-pointer"
              >
                <span>{rec.actionLabel}</span>
                <FaArrowRight size={9} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
