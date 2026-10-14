import { BACKEND_URL } from '../config/backend';
/**
 * AIForge AI Usage & Analytics API Service
 */

import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || `${BACKEND_URL}`;

export async function fetchAnalyticsMetrics() {
  try {
    const res = await axios.get(`${API_BASE}/api/analytics/metrics`, { timeout: 10000 });
    if (res.data?.metrics) return res.data.metrics;
    return { error: "The server returned no metrics" };
  } catch (err) {
    // No sample numbers on failure: the page shows the error instead.
    return { error: err?.response?.data?.detail || err?.message || "Request failed" };
  }
}
