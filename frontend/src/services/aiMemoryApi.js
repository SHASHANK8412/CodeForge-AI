import { BACKEND_URL } from '../config/backend';
/**
 * AIForge AI Memory API Service
 * ==============================
 * Handles personal and project memory persistence, smart recall, and suggestions.
 * Includes seamless local fallback support with localStorage synchronization.
 */

import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || `${BACKEND_URL}`;
const LOCAL_STORAGE_KEY = "aiforge_ai_memory_items";

// The offline cache starts empty. Earlier versions seeded sample memories; those ids are
// dropped on read so they don't pose as things the user told AIForge.
const INITIAL_FALLBACK_MEMORIES = [];
const SAMPLE_MEMORY_IDS = new Set(['mem-pers-1', 'mem-pers-2', 'mem-proj-1', 'mem-proj-2']);

function getLocalMemories() {
  try {
    const raw = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (!raw) {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(INITIAL_FALLBACK_MEMORIES));
      return INITIAL_FALLBACK_MEMORIES;
    }
    const items = JSON.parse(raw);
    return Array.isArray(items) ? items.filter((m) => !SAMPLE_MEMORY_IDS.has(m?.id)) : [];
  } catch (err) {
    console.error("Local storage error:", err);
    return INITIAL_FALLBACK_MEMORIES;
  }
}

function saveLocalMemories(items, { notify = true } = {}) {
  try {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(items));
    // Only real changes notify listeners: the memory page reloads on this event, so announcing
    // the cache refresh done by fetchMemories itself caused an endless fetch loop.
    if (notify) window.dispatchEvent(new CustomEvent("aiforge:memory-updated", { detail: { count: items.length } }));
  } catch (err) {
    console.error("Failed to save memories to localStorage:", err);
  }
}

export async function fetchMemories({ scope, projectId, category, search, sortBy = "recent" } = {}) {
  try {
    const res = await axios.get(`${API_BASE}/api/memory/list`, {
      params: { scope, project_id: projectId, category, search, sort_by: sortBy },
      timeout: 6000
    });
    if (res.data?.memories) {
      saveLocalMemories(res.data.memories, { notify: false });
      return res.data.memories;
    }
    return getLocalMemories();
  } catch (err) {
    console.warn("Falling back to local memories:", err);
    let items = getLocalMemories();
    if (scope) items = items.filter(m => m.scope.toUpperCase() === scope.toUpperCase());
    if (projectId) items = items.filter(m => m.project_id === projectId);
    if (category && category !== "All") items = items.filter(m => m.category.toLowerCase() === category.toLowerCase());
    if (search) {
      const q = search.toLowerCase();
      items = items.filter(m => m.title.toLowerCase().includes(q) || m.content.toLowerCase().includes(q) || m.tags.some(t => t.toLowerCase().includes(q)));
    }
    return items;
  }
}

export async function createMemory(payload) {
  try {
    const res = await axios.post(`${API_BASE}/api/memory`, payload, { timeout: 6000 });
    if (res.data?.memory) {
      const current = getLocalMemories();
      saveLocalMemories([res.data.memory, ...current.filter(m => m.id !== res.data.memory.id)]);
      return res.data.memory;
    }
  } catch (err) {
    console.warn("Local fallback for create memory:", err);
  }

  const localItem = {
    id: `mem-${Date.now()}`,
    user_id: "default_user",
    scope: payload.scope || "PERSONAL",
    project_id: payload.scope === "PROJECT" ? (payload.project_id || "aiforge-fooddelivery-ai") : null,
    category: payload.category || "Preferences",
    title: payload.title,
    content: payload.content,
    importance: payload.importance || "HIGH",
    source: payload.source || "User",
    tags: payload.tags || [],
    pinned: payload.pinned || false,
    created_at: new Date().toISOString().replace("T", " ").slice(0, 19),
    updated_at: new Date().toISOString().replace("T", " ").slice(0, 19),
    last_used_at: "Just now",
    usage_count: 0
  };
  const current = getLocalMemories();
  saveLocalMemories([localItem, ...current]);
  return localItem;
}

export async function updateMemory(memoryId, payload) {
  try {
    const res = await axios.put(`${API_BASE}/api/memory/${memoryId}`, payload, { timeout: 6000 });
    if (res.data?.memory) {
      const current = getLocalMemories();
      saveLocalMemories(current.map(m => m.id === memoryId ? res.data.memory : m));
      return res.data.memory;
    }
  } catch (err) {
    console.warn("Local fallback for update memory:", err);
  }

  const current = getLocalMemories();
  const updated = current.map(m => {
    if (m.id === memoryId) {
      return {
        ...m,
        ...payload,
        updated_at: new Date().toISOString().replace("T", " ").slice(0, 19)
      };
    }
    return m;
  });
  saveLocalMemories(updated);
  return updated.find(m => m.id === memoryId);
}

export async function deleteMemory(memoryId) {
  try {
    await axios.delete(`${API_BASE}/api/memory/${memoryId}`, { timeout: 6000 });
  } catch (err) {
    console.warn("Local fallback for delete memory:", err);
  }
  const current = getLocalMemories();
  const filtered = current.filter(m => m.id !== memoryId);
  saveLocalMemories(filtered);
  return true;
}

export async function clearProjectMemory(projectId) {
  try {
    await axios.delete(`${API_BASE}/api/memory/project/${projectId}`, { timeout: 6000 });
  } catch (err) {
    console.warn("Local fallback for clear project memory:", err);
  }
  const current = getLocalMemories();
  const filtered = current.filter(m => m.project_id !== projectId);
  saveLocalMemories(filtered);
  return true;
}

export async function clearAllMemory() {
  try {
    await axios.delete(`${API_BASE}/api/memory/clear/all`, { timeout: 6000 });
  } catch (err) {
    console.warn("Local fallback for clear all memory:", err);
  }
  saveLocalMemories([]);
  return true;
}

export async function smartRecall({ prompt, projectId, limit = 5 } = {}) {
  try {
    const res = await axios.post(`${API_BASE}/api/memory/recall`, { prompt, project_id: projectId, limit }, { timeout: 6000 });
    return res.data;
  } catch (err) {
    console.warn("Local fallback for smart recall:", err);
    const memories = getLocalMemories();
    const promptLower = (prompt || "").toLowerCase();
    const matches = memories.filter(m => 
      promptLower.includes(m.title.toLowerCase()) || 
      promptLower.includes(m.category.toLowerCase()) ||
      m.tags.some(t => promptLower.includes(t.toLowerCase())) ||
      (projectId && m.project_id === projectId) ||
      m.pinned
    ).slice(0, limit);

    return {
      success: true,
      recalled_memories: matches,
      context_prompt: matches.map(m => `- **[${m.scope}] ${m.title}**: ${m.content}`).join("\n"),
      total_recalled: matches.length,
      memory_active: matches.length > 0
    };
  }
}
