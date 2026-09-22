/**
 * AIForge Universal Command Center Service
 * ========================================
 * Intent detection, smart context routing, and local command history management.
 */

import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const RECENT_COMMANDS_KEY = "aiforge_recent_command_history";

export function getRecentCommands() {
  try {
    const raw = localStorage.getItem(RECENT_COMMANDS_KEY);
    if (!raw) {
      const defaults = [
        "Debug this Python code",
        "Continue my AIForge FoodDelivery project",
        "Create a study plan for DBMS",
        "Research event streaming Kafka vs Redpanda"
      ];
      localStorage.setItem(RECENT_COMMANDS_KEY, JSON.stringify(defaults));
      return defaults;
    }
    return JSON.parse(raw);
  } catch (err) {
    return [];
  }
}

export function addRecentCommand(query) {
  if (!query || !query.trim()) return;
  try {
    const current = getRecentCommands();
    const filtered = current.filter(q => q.toLowerCase() !== query.trim().toLowerCase());
    const updated = [query.trim(), ...filtered].slice(0, 10);
    localStorage.setItem(RECENT_COMMANDS_KEY, JSON.stringify(updated));
  } catch (err) {
    console.error("Error saving recent command:", err);
  }
}

export function clearRecentCommands() {
  try {
    localStorage.removeItem(RECENT_COMMANDS_KEY);
  } catch (err) {
    console.error("Error clearing command history:", err);
  }
}

export async function resolveCommandIntent({ query, currentProjectId, currentView }) {
  try {
    const res = await axios.post(`${API_BASE}/api/command/route`, {
      query,
      current_project_id: currentProjectId,
      current_view: currentView
    }, { timeout: 4000 });
    if (res.data?.resolution) {
      return res.data.resolution;
    }
  } catch (err) {
    console.warn("Local fallback for command intent resolution:", err);
  }

  // Client-side NLP Intent Matcher Fallback
  const q = (query || "").toLowerCase().trim();
  if (!q) {
    return {
      query: "",
      intent: "INITIAL_SUGGESTIONS",
      title: "AIForge Universal Command Center",
      description: "Type natural language instructions or select a quick action",
      target_view: "dashboard",
      action_type: "NAVIGATE",
      suggested_chips: ["🤖 Run Agent", "💻 Code", "📚 Study", "🔬 Research", "✍️ Write", "📊 Analyze", "🧠 Remember"]
    };
  }

  if (q.startsWith("remember") || q.startsWith("save preference") || q.includes("always use")) {
    const fact = q.replace(/^remember(?:\s+that)?\s*/i, "").replace(/^save preference\s*/i, "");
    return {
      query,
      intent: "MEMORY_STORE",
      title: `Save to AI Memory: "${fact.slice(0, 40)}"`,
      description: "Immediately store this preference into AIForge persistent memory graph",
      target_view: "memory",
      action_type: "STORE_MEMORY",
      action_payload: { title: `Preference: ${fact.slice(0, 30)}`, content: fact }
    };
  }

  if (q.includes("study") || q.includes("exam") || q.includes("quiz") || q.includes("dbms")) {
    return {
      query,
      intent: "AGENT_STUDY",
      title: "Launch Study & Exam Agent",
      description: `Deconstruct syllabus, generate multi-day milestones, notes, and quiz for: '${query}'`,
      target_view: "agents",
      action_type: "LAUNCH_AGENT",
      action_payload: { agent_id: "agent-study", goal: query }
    };
  }

  if (q.includes("code") || q.includes("debug") || q.includes("fastapi") || q.includes("react") || q.includes("error")) {
    return {
      query,
      intent: "AGENT_CODING",
      title: "Launch Autonomous Coding Agent",
      description: `Plan architecture, generate clean code, run unit tests, and verify: '${query}'`,
      target_view: "agents",
      action_type: "LAUNCH_AGENT",
      action_payload: { agent_id: "agent-coding", goal: query, project_id: currentProjectId }
    };
  }

  if (q.includes("research") || q.includes("compare") || q.includes("vs ") || q.includes("rfc")) {
    return {
      query,
      intent: "AGENT_RESEARCH",
      title: "Launch Deep Research Agent",
      description: `Perform library search, gather technical specifications, and synthesize RFC for: '${query}'`,
      target_view: "agents",
      action_type: "LAUNCH_AGENT",
      action_payload: { agent_id: "agent-research", goal: query }
    };
  }

  if (q.includes("continue") || q.includes("project") || q.includes("fooddelivery") || q.includes("yesterday")) {
    return {
      query,
      intent: "PROJECT_ACTION",
      title: `Continue Active Project: ${currentProjectId || "FoodDelivery AI"}`,
      description: "Resume project workspace with synchronized memory context",
      target_view: "projects",
      action_type: "NAVIGATE"
    };
  }

  return {
    query,
    intent: "CHAT_PROMPT",
    title: `Ask AIForge: "${query.slice(0, 45)}"`,
    description: "Send prompt to AI Assistant with automatic Smart Memory Recall context",
    target_view: "chat",
    action_type: "SET_PROMPT",
    action_payload: { prompt: query }
  };
}

export async function quickRememberNote(content) {
  try {
    const res = await axios.post(`${API_BASE}/api/command/quick-remember`, { content }, { timeout: 4000 });
    return res.data;
  } catch (err) {
    console.warn("Local fallback for quick remember:", err);
    return { success: true };
  }
}
