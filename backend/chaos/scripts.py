"""
Programs that run inside the experiment's own containers (python:3.13-slim, standard library only).
They are AIForge's code, not the project's: a controllable stub dependency and a probe that sends
requests to the app from inside the isolated network.
"""

# A disposable HTTP dependency. Its behaviour is switched through a control endpoint that is only
# reachable inside the experiment network:  POST /__chaos {"mode": "ok"|"error"|"slow"|"malformed", "delay_ms": n}
STUB_DEPENDENCY = r'''
import json, os, sys, time, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
ROUTES = json.loads(os.environ.get("STUB_ROUTES", "{}"))      # {"/path": json body}
STATE = {"mode": "ok", "delay_ms": 0, "requests": 0}
LOCK = threading.Lock()

class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def do_POST(self):
        if self.path == "/__chaos":
            n = int(self.headers.get("Content-Length") or 0)
            cfg = json.loads(self.rfile.read(n) or b"{}")
            with LOCK:
                STATE["mode"] = cfg.get("mode", "ok")
                STATE["delay_ms"] = int(cfg.get("delay_ms", 0))
            return self._send(200, dict(STATE))
        return self.do_GET()
    def do_GET(self):
        if self.path == "/__chaos":
            return self._send(200, dict(STATE))
        with LOCK:
            STATE["requests"] += 1
            mode, delay = STATE["mode"], STATE["delay_ms"]
        if mode == "slow":
            time.sleep(delay / 1000)
        if mode == "error":
            return self._send(500, {"error": "injected dependency failure"})
        if mode == "malformed":
            return self._send(200, b"{this is not json", "application/json")
        path = self.path.split("?")[0]
        if path in ROUTES:
            return self._send(200, ROUTES[path])
        return self._send(404, {"error": "unknown path"})

ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("STUB_PORT", "8080"))), H).serve_forever()
'''

# Sends requests from inside the network; prints one JSON document with every result.
#   argv: base_url, json list of [method, path], count per endpoint, concurrency, timeout seconds
PROBE = r'''
import json, sys, time, urllib.request, urllib.error, concurrent.futures as cf
base, eps, count, conc, timeout = sys.argv[1], json.loads(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5])
def one(ep):
    method, path = ep
    req = urllib.request.Request(base + path, method=method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(2000).decode("utf-8", "replace")
            return {"ep": method + " " + path, "status": r.status, "ms": round((time.perf_counter() - t0) * 1000, 2), "body": body[:600]}
    except urllib.error.HTTPError as e:
        body = e.read(2000).decode("utf-8", "replace")
        return {"ep": method + " " + path, "status": e.code, "ms": round((time.perf_counter() - t0) * 1000, 2), "body": body[:600]}
    except Exception as e:
        return {"ep": method + " " + path, "status": None, "ms": round((time.perf_counter() - t0) * 1000, 2), "error": type(e).__name__ + ": " + str(e)[:200]}
jobs = [ep for ep in eps for _ in range(count)]
started = time.time()
with cf.ThreadPoolExecutor(max_workers=conc) as pool:
    results = list(pool.map(one, jobs))
print(json.dumps({"started": started, "results": results}))
'''

# Changes the stub dependency's behaviour from inside the network.
CONTROL = r'''
import json, sys, urllib.request
req = urllib.request.Request(sys.argv[1] + "/__chaos", data=sys.argv[2].encode(), method="POST",
                             headers={"Content-Type": "application/json"})
print(urllib.request.urlopen(req, timeout=5).read().decode())
'''
