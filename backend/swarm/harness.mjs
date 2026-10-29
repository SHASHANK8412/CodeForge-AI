// AIForge Swarm Intelligence contract harness (runs inside a node container on the mission's internal network).
// It never decides anything: it sends the planned requests, calls the generated client's exported functions and
// records exactly what went over the wire. Validation happens in AIForge (backend/swarm/runtime.py).
import fs from "node:fs";
import { pathToFileURL } from "node:url";

const plan = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const base = plan.base.replace(/\/$/, "");
const MAX = 20000;
const realFetch = globalThis.fetch;
const log = [];
const out = { harness: "aiforge-swarm-contract/1", node: process.version, direct: [], client: [], egress: [] };

const abs = (u) => (/^https?:\/\//i.test(u) ? u : base + (u.startsWith("/") ? u : "/" + u));
const rel = (u) => (u.startsWith(base) ? u.slice(base.length) || "/" : u);
const timeoutName = (e) => (e && (e.name === "TimeoutError" || e.name === "AbortError") ? "timeout" : String(e).slice(0, 300));

function headers(h) {
  const o = {};
  try {
    for (const [k, v] of new Headers(h || {})) o[k] = k === "authorization" ? String(v).split(" ")[0] + " <redacted>" : String(v).slice(0, 200);
  } catch (e) { o["<unreadable>"] = String(e).slice(0, 100); }
  return o;
}

async function recordingFetch(input, init = {}) {
  const url = typeof input === "string" || input instanceof URL ? String(input) : input.url;
  const target = abs(url);
  const [path, query] = rel(target).split("?");
  const rec = { method: String(init.method || (input && input.method) || "GET").toUpperCase(), path, query: query || "",
                headers: headers(init.headers), body: typeof init.body === "string" ? init.body.slice(0, MAX) : init.body == null ? null : "[non-text body]" };
  const t0 = Date.now();
  try {
    const res = await realFetch(target, { ...init, signal: AbortSignal.timeout(plan.request_timeout_ms) });
    const text = await res.clone().text();
    Object.assign(rec, { status: res.status, content_type: res.headers.get("content-type"), response: text.slice(0, MAX), ms: Date.now() - t0 });
    log.push(rec);
    return res;
  } catch (e) {
    Object.assign(rec, { error: timeoutName(e), ms: Date.now() - t0 });
    log.push(rec);
    throw e;
  }
}

// 1. the app's own OpenAPI description (declared behaviour)
try {
  const r = await realFetch(base + "/openapi.json", { signal: AbortSignal.timeout(plan.request_timeout_ms) });
  out.openapi = r.ok ? (await r.text()).slice(0, 400000) : null;
} catch (e) { out.openapi_error = timeoutName(e); }

// 2. contract tests sent directly (requests built from the contract)
const saved = {};
for (const s of plan.direct) {
  let path = s.path;
  for (const [p, ref] of Object.entries(s.bind || {})) {
    const v = saved[ref[0]] && saved[ref[0]][ref[1]];
    path = path.replace("{" + p + "}", encodeURIComponent(v !== undefined && v !== null ? v : s.defaults[p]));
  }
  for (const [p, v] of Object.entries(s.defaults || {})) path = path.replace("{" + p + "}", encodeURIComponent(v));
  const qs = s.query && Object.keys(s.query).length ? "?" + new URLSearchParams(s.query) : "";
  const t0 = Date.now();
  try {
    const res = await realFetch(abs(path) + qs, { method: s.method, headers: s.headers || {}, body: s.body_text == null ? undefined : s.body_text,
                                                  signal: AbortSignal.timeout(plan.request_timeout_ms) });
    const text = await res.text();
    try { const j = JSON.parse(text); if (j && typeof j === "object") saved[s.id] = j; } catch (e) { /* not JSON */ }
    out.direct.push({ id: s.id, path, query: qs, status: res.status, content_type: res.headers.get("content-type"), body: text.slice(0, MAX), ms: Date.now() - t0 });
  } catch (e) {
    out.direct.push({ id: s.id, path, query: qs, error: timeoutName(e), ms: Date.now() - t0 });
  }
}

// 3. the generated client, imported and called like the UI would
globalThis.__AIFORGE_ENV__ = { VITE_API_URL: base, REACT_APP_API_URL: base, API_URL: base, MODE: "test", DEV: false, PROD: true };
for (const k of ["VITE_API_URL", "REACT_APP_API_URL", "API_URL"]) process.env[k] = base;
const storage = (init) => { const m = new Map(Object.entries(init || {})); return { getItem: (k) => (m.has(k) ? m.get(k) : null),
  setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k), clear: () => m.clear() }; };
globalThis.localStorage = storage(plan.storage);
globalThis.sessionStorage = storage(plan.storage);
globalThis.window = globalThis;
globalThis.location = { origin: base, href: base + "/", protocol: "http:", host: base.replace(/^https?:\/\//, "") };
globalThis.fetch = recordingFetch;
const modules = {};
for (const m of [...new Set(plan.client.map((c) => c.module))]) {
  try { modules[m] = await import(pathToFileURL(plan.root + "/" + m).href); } catch (e) { modules[m] = { __error: String(e).slice(0, 500) }; }
}
const returned = {};
for (const st of plan.client) {
  const mod = modules[st.module] || {};
  const rec = { export: st.export, module: st.module };
  const fn = mod[st.export];
  if (mod.__error) { rec.error = "import failed: " + mod.__error; out.client.push(rec); continue; }
  if (typeof fn !== "function") { rec.error = "not exported"; out.client.push(rec); continue; }
  const args = st.args.map((a) => ("from" in a ? (returned[a.from] && returned[a.from][a.field] != null ? returned[a.from][a.field] : a.default)
                                                 : "undefined" in a ? undefined : a.value));
  rec.args = args;
  const before = log.length;
  let timer;
  try {
    const ret = await Promise.race([Promise.resolve().then(() => fn(...args)),
      new Promise((_, rej) => { timer = setTimeout(() => rej(new Error("timeout")), plan.call_timeout_ms); })]);
    returned[st.export] = ret;
    try { rec.returned = JSON.parse(JSON.stringify(ret === undefined ? null : ret)); } catch (e) { rec.returned = String(ret).slice(0, 500); }
  } catch (e) {
    rec.error = String(e && e.message === "timeout" ? "timeout" : e).slice(0, 500);
  } finally { clearTimeout(timer); }
  rec.requests = log.slice(before);
  out.client.push(rec);
}

// 4. the network policy: nothing outside the mission network must be reachable
for (const target of plan.egress || []) {
  const t0 = Date.now();
  try {
    const r = await realFetch(target, { signal: AbortSignal.timeout(3000) });
    out.egress.push({ target, reachable: true, status: r.status, ms: Date.now() - t0 });
  } catch (e) { out.egress.push({ target, reachable: false, error: timeoutName(e), ms: Date.now() - t0 }); }
}

process.stdout.write("AIFORGE_RESULT " + JSON.stringify(out) + "\n");
process.exit(0);
