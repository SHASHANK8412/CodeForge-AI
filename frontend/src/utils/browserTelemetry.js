/**
 * frontend/src/utils/browserTelemetry.js
 * ========================================
 * Safe, privacy-preserving browser telemetry tracker for React frontend:
 * - Collects page navigation metrics via window.performance
 * - Measures API call latencies
 * - Automatically redacts authorization headers, JWTs, and sensitive query parameters
 */

const SENSITIVE_QUERY_PATTERNS = [
  /(token=)[^&]+/gi,
  /(key=)[^&]+/gi,
  /(password=)[^&]+/gi,
  /(auth=)[^&]+/gi
];

export function sanitizeBrowserUrl(url) {
  if (!url) return '';
  let sanitized = url;
  for (const pat of SENSITIVE_QUERY_PATTERNS) {
    sanitized = sanitized.replace(pat, '$1[REDACTED]');
  }
  return sanitized;
}

export function getBrowserPerformanceMetrics() {
  if (typeof window === 'undefined' || !window.performance) {
    return { status: 'NOT_AVAILABLE' };
  }

  const navEntries = performance.getEntriesByType('navigation');
  if (navEntries.length === 0) {
    return { status: 'AVAILABLE', loadTimeMs: 0 };
  }

  const nav = navEntries[0];
  return {
    status: 'PASS',
    dnsTimeMs: Math.round(nav.domainLookupEnd - nav.domainLookupStart),
    connectTimeMs: Math.round(nav.connectEnd - nav.connectStart),
    ttfbMs: Math.round(nav.responseStart - nav.requestStart),
    domInteractiveMs: Math.round(nav.domInteractive),
    loadTimeMs: Math.round(nav.loadEventEnd - nav.startTime),
    redirectCount: nav.redirectCount
  };
}

export function recordBrowserSpan(name, durationMs, attributes = {}) {
  const safeAttrs = {};
  for (const [k, v] of Object.entries(attributes)) {
    if (/auth|token|password|key|cookie/i.test(k)) {
      safeAttrs[k] = '[REDACTED_HEADER]';
    } else if (typeof v === 'string') {
      safeAttrs[k] = sanitizeBrowserUrl(v);
    } else {
      safeAttrs[k] = v;
    }
  }

  return {
    name,
    kind: 'BROWSER_CLIENT',
    durationMs: Math.round(durationMs),
    timestamp: new Date().toISOString(),
    attributes: safeAttrs
  };
}
