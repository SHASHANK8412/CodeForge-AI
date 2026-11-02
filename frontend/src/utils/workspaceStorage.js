// Utility to manage saved AI outputs, activity log, and recommendations
const SAVED_OUTPUTS_KEY = "aiforge_saved_outputs";
const ACTIVITY_LOG_KEY = "aiforge_activity_log";

// Saved outputs start empty. Earlier versions seeded four sample snippets into localStorage;
// those ids are dropped on read so they don't pose as the user's own saved work.
const INITIAL_SAVED_OUTPUTS = [];
const SAMPLE_OUTPUT_IDS = new Set(["out-1", "out-2", "out-3", "out-4"]);

// Starts empty: the log should only ever contain things that actually happened.
const INITIAL_ACTIVITIES = [];

export function getSavedOutputs() {
  try {
    const raw = localStorage.getItem(SAVED_OUTPUTS_KEY);
    if (!raw) {
      localStorage.setItem(SAVED_OUTPUTS_KEY, JSON.stringify(INITIAL_SAVED_OUTPUTS));
      return INITIAL_SAVED_OUTPUTS;
    }
    const items = JSON.parse(raw);
    const own = Array.isArray(items) ? items.filter((item) => !SAMPLE_OUTPUT_IDS.has(item?.id)) : [];
    if (own.length !== (items?.length ?? 0)) localStorage.setItem(SAVED_OUTPUTS_KEY, JSON.stringify(own));
    return own;
  } catch (err) {
    console.error("Error reading saved outputs from localStorage:", err);
    return INITIAL_SAVED_OUTPUTS;
  }
}

export function saveOutputItem(item) {
  try {
    const current = getSavedOutputs();
    const newItem = {
      id: `out-${Date.now()}`,
      created_at: "Just now",
      ...item
    };
    const updated = [newItem, ...current];
    localStorage.setItem(SAVED_OUTPUTS_KEY, JSON.stringify(updated));
    window.dispatchEvent(new CustomEvent("aiforge:saved-outputs-updated", { detail: { outputs: updated } }));
    return newItem;
  } catch (err) {
    console.error("Error saving output item:", err);
    return null;
  }
}

export function deleteSavedOutputItem(id) {
  try {
    const current = getSavedOutputs();
    const updated = current.filter(item => item.id !== id);
    localStorage.setItem(SAVED_OUTPUTS_KEY, JSON.stringify(updated));
    window.dispatchEvent(new CustomEvent("aiforge:saved-outputs-updated", { detail: { outputs: updated } }));
    return true;
  } catch (err) {
    console.error("Error deleting saved output:", err);
    return false;
  }
}

export function getActivityLog() {
  try {
    const raw = localStorage.getItem(ACTIVITY_LOG_KEY);
    if (!raw) {
      localStorage.setItem(ACTIVITY_LOG_KEY, JSON.stringify(INITIAL_ACTIVITIES));
      return INITIAL_ACTIVITIES;
    }
    return JSON.parse(raw);
  } catch (err) {
    console.error("Error reading activity log:", err);
    return INITIAL_ACTIVITIES;
  }
}

export function logActivity(activity) {
  try {
    const current = getActivityLog();
    const newAct = {
      id: `act-${Date.now()}`,
      timestamp: "Just now",
      status: "success",
      ...activity
    };
    const updated = [newAct, ...current.slice(0, 49)];
    localStorage.setItem(ACTIVITY_LOG_KEY, JSON.stringify(updated));
    window.dispatchEvent(new CustomEvent("aiforge:activity-logged", { detail: { activity: newAct } }));
    return newAct;
  } catch (err) {
    console.error("Error logging activity:", err);
    return null;
  }
}
