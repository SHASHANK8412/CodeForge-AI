"""
Scanner adapters and non-Python rules.

  bandit        Python SAST (already installed with AIForge; reused via the quality gate)
  secrets       AIForge's secret scanner plus private-key/env-file checks; values are always redacted
  pip-audit     known vulnerabilities in Python requirements (PyPI/OSV advisory data; network)
  npm audit     known vulnerabilities in a package-lock.json (npm registry advisory data; network)
  js rules      Express / React / Node patterns (regex; reported with lower confidence than ast rules)
  config rules  Dockerfile / docker-compose / requirements / lock files
Every adapter reports how it ran (ran / partial / unavailable / error / skipped) - an unavailable scanner is never "clean".
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.evolution.autopilot.models import now_iso
from backend.evolution.autopilot.redact import redact
from backend.guardian.models import ToolRun

Raw = Dict[str, Any]
_BANDIT_MAP = {   # bandit test id -> (category, our rule id it duplicates, if any)
    "B608": ("injection", "PY-SQLI"), "B602": ("injection", "PY-CMDI"), "B605": ("injection", "PY-CMDI"),
    "B307": ("injection", "PY-EVAL"), "B102": ("injection", "PY-EVAL"), "B301": ("injection", "PY-DESERIALIZE"),
    "B506": ("injection", "PY-DESERIALIZE"), "B324": ("crypto", "PY-WEAK-HASH"), "B303": ("crypto", "PY-WEAK-HASH"),
    "B311": ("crypto", "PY-PREDICTABLE-TOKEN"), "B105": ("secrets", None), "B106": ("secrets", None),
    "B107": ("secrets", None), "B201": ("configuration", "PY-DEBUG"), "B104": ("configuration", None),
    "B501": ("web", None), "B310": ("injection", "PY-SSRF"), "B113": ("web", None),
}


def bandit(project: Path) -> Tuple[List[Raw], ToolRun]:
    from backend.validation.quality_gate import _bandit_findings
    found = _bandit_findings(project)
    if found is None:
        return [], ToolRun(tool="bandit", status="unavailable", detail="Bandit could not run")
    version = _version([sys.executable, "-m", "bandit", "--version"])
    out = []
    for b in found:
        cat, dup = _BANDIT_MAP.get(b.get("code"), ("configuration", None))
        out.append({"rule_id": f"BANDIT-{b.get('code')}", "category": cat, "dup_of": dup,
                    "title": f"{b.get('code')}: {b.get('message', '')[:100]}", "severity": {"HIGH": "high", "MEDIUM": "medium"}.get(b.get("severity"), "low"),
                    "confidence": {"HIGH": "high", "MEDIUM": "medium"}.get(b.get("confidence"), "low"),
                    "file": b.get("file"), "line": b.get("line"), "evidence_text": b.get("message", ""),
                    "description": b.get("message", ""), "remediation": "See the Bandit documentation for this test id.",
                    "references": [f"bandit:{b.get('code')}"], "state": "detected" if b.get("confidence") == "HIGH" else "requires_review",
                    "source": "bandit"})
    return out, ToolRun(tool="bandit", status="ran", detail=f"{len(found)} result(s)", version=version)


def secrets(project: Path, files: Dict[str, str]) -> Tuple[List[Raw], ToolRun]:
    from backend.deployment.secret_scanner import global_secret_scanner
    out = []
    scan = global_secret_scanner.scan_files(files)
    for s in scan.findings:
        out.append({"rule_id": "SECRET-HARDCODED", "category": "secrets", "title": f"Possible committed secret: {s.secret_type}",
                    "severity": "critical", "confidence": "medium", "file": s.file_path, "line": s.line_number,
                    "evidence_text": f"{s.secret_type}: {s.masked_value}",
                    "description": "A credential appears in the source; anyone with the code (or an exported archive) can use it.",
                    "remediation": "Remove it, rotate it, and read it from the environment.", "references": ["CWE-798"],
                    "state": "detected", "source": "secret-scanner"})
    for rel, src in files.items():
        if "-----BEGIN" in src and "PRIVATE KEY-----" in src:
            line = src[: src.index("-----BEGIN")].count("\n") + 1
            out.append({"rule_id": "SECRET-PRIVATE-KEY", "category": "secrets", "title": "Private key in the project",
                        "severity": "critical", "confidence": "high", "file": rel, "line": line,
                        "evidence_text": "-----BEGIN ... PRIVATE KEY----- [REDACTED]",
                        "description": "A private key is part of the project files and of any archive made from them.",
                        "remediation": "Delete it from the project, revoke it, and load keys from a secret store.",
                        "references": ["CWE-321"], "state": "detected", "source": "guardian"})
        name = Path(rel).name
        if name == ".env" or (name.startswith(".env.") and not name.endswith((".example", ".sample", ".template"))):
            out.append({"rule_id": "SECRET-ENV-FILE", "category": "secrets", "title": f"Environment file {rel} in the project",
                        "severity": "high", "confidence": "high", "file": rel, "line": None,
                        "evidence_text": f"{rel} ({len(src.splitlines())} lines, values redacted)",
                        "description": "Environment files usually hold real credentials.",
                        "remediation": "Remove it, add it to .gitignore, and commit a .env.example without values instead.",
                        "references": ["CWE-538"], "state": "detected", "source": "guardian"})
    return out, ToolRun(tool="secret scanner", status="ran", detail=f"{len(out)} result(s)")


_PIN = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]*\])?\s*==\s*([A-Za-z0-9][A-Za-z0-9.+!_-]*)\s*(?:;.*)?$")


def pinned_requirements(text: str) -> Tuple[List[str], List[str]]:
    """(exact 'name==version' pins, other requirement lines). Options, index URLs, paths and VCS links are
    never passed on: only package names and versions leave the machine."""
    pins, other = [], []
    for raw in text.splitlines():
        line = raw.split(" #", 1)[0].strip()
        if not line or line.startswith("#"):
            continue
        m = _PIN.match(line)
        if m:
            pins.append(f"{m.group(1)}=={m.group(3)}")
        else:
            other.append(line.split()[0][:60] if not line.startswith("-") else line.split()[0])
    return sorted(set(pins)), other


def pip_audit(project: Path) -> Tuple[List[Raw], ToolRun]:
    """
    Advisory lookup only: pip-audit in --disable-pip --no-deps mode with a temporary file holding the exact
    pins. Nothing is installed or built (no package code runs) and only names and versions are sent.
    Unpinned requirements cannot be looked up and are reported as NOT checked.
    """
    from backend.execution.project_env import requirements_file
    req = requirements_file(project)
    if req is None:
        return [], ToolRun(tool="pip-audit", status="skipped", detail="no requirements file")
    rel = req.relative_to(project).as_posix()
    pins, other = pinned_requirements(req.read_text(encoding="utf-8", errors="replace"))
    unchecked = redact(f"{len(other)} unpinned or non-index requirement(s) NOT checked ({', '.join(other[:8])})") if other else ""
    if not pins:
        return [], ToolRun(tool="pip-audit", status="unavailable",
                           detail=f"no exactly pinned requirements in {rel}; " + (unchecked or "nothing to look up"))
    version = _version([sys.executable, "-m", "pip_audit", "--version"])
    started = now_iso()
    with tempfile.TemporaryDirectory(prefix="aiforge_audit_") as tmp:
        pinned = Path(tmp) / "requirements.txt"
        pinned.write_text("\n".join(pins) + "\n", encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, "-m", "pip_audit", "-r", str(pinned), "--disable-pip", "--no-deps",
                                   "--format", "json", "--progress-spinner", "off", "--desc", "off"],
                                  capture_output=True, text=True, timeout=300, cwd=tmp)
            data = json.loads(proc.stdout or "{}")
        except subprocess.TimeoutExpired:
            return [], ToolRun(tool="pip-audit", status="error", detail="timed out after 300s: advisory data NOT checked",
                               version=version)
        except (OSError, ValueError) as e:
            return [], ToolRun(tool="pip-audit", status="unavailable",
                               detail=f"advisory data could not be retrieved ({type(e).__name__}); dependencies NOT checked",
                               version=version)
    deps = data.get("dependencies", []) if isinstance(data, dict) else data
    if not deps:
        return [], ToolRun(tool="pip-audit", status="error", version=version,
                           detail="advisory lookup failed: dependencies NOT checked. " + redact((proc.stderr or "")[-300:]))
    out = []
    for d in deps:
        seen = set()
        for v in d.get("vulns") or []:
            if v.get("id") in seen:
                continue
            seen.add(v.get("id"))
            aliases = [v.get("id")] + list(v.get("aliases") or [])
            out.append({"rule_id": "DEP-VULNERABLE", "category": "dependencies",
                        "title": f"{d.get('name')} {d.get('version')} has a known vulnerability ({v.get('id')})",
                        "severity": "high", "confidence": "high", "file": rel, "line": None,
                        "evidence_text": f"{d.get('name')}=={d.get('version')}: {', '.join(a for a in aliases if a)}; "
                                         f"fixed in {', '.join(v.get('fix_versions') or []) or 'no release yet'}",
                        "description": "A published advisory affects the pinned version. Severity is not taken from a "
                                       "CVSS score; check the advisory for the real impact.",
                        "remediation": f"Upgrade {d.get('name')} to {', '.join(v.get('fix_versions') or []) or 'a fixed version when available'} "
                                       "(check the changelog for breaking changes).",
                        "references": [a for a in aliases if a], "dependencies": [d.get("name")], "state": "detected",
                        "source": "pip-audit"})
    detail = f"{len(deps)} pinned dependencies checked against PyPI/OSV advisories; {len(out)} vulnerability(ies)"
    return out, ToolRun(tool="pip-audit", status="partial" if other else "ran", version=version, retrieved_at=started,
                        detail=detail + (f"; {unchecked}" if unchecked else ""))


def npm_audit(project: Path) -> Tuple[List[Raw], ToolRun]:
    pkg = next((p for p in [project / "package.json", project / "frontend" / "package.json", project / "backend" / "package.json"]
                if p.is_file()), None)
    if pkg is None:
        return [], ToolRun(tool="npm audit", status="skipped", detail="no package.json")
    lock = pkg.parent / "package-lock.json"
    rel = pkg.relative_to(project).as_posix()
    if not lock.is_file():
        return ([{"rule_id": "DEP-NO-LOCKFILE", "category": "dependencies", "title": f"No package-lock.json next to {rel}",
                  "severity": "low", "confidence": "high", "file": rel, "line": None,
                  "evidence_text": f"{rel} without package-lock.json", "description": "Without a lock file, installs can pick up "
                  "different (possibly compromised or vulnerable) versions, and npm audit cannot check them.",
                  "remediation": "Commit the package-lock.json produced by npm install.", "references": [],
                  "state": "detected", "source": "guardian"}],
                ToolRun(tool="npm audit", status="unavailable", detail=f"{rel} has no lock file: npm dependencies NOT checked"))
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm:
        return [], ToolRun(tool="npm audit", status="unavailable", detail="npm is not installed: npm dependencies NOT checked")
    started = now_iso()
    with tempfile.TemporaryDirectory() as tmp:          # only the manifests: no project code, no install scripts
        shutil.copy(pkg, Path(tmp) / "package.json")
        shutil.copy(lock, Path(tmp) / "package-lock.json")
        try:
            proc = subprocess.run([npm, "audit", "--json", "--package-lock-only"], cwd=tmp, capture_output=True, text=True, timeout=180)
            data = json.loads(proc.stdout or "{}")
        except (subprocess.TimeoutExpired, OSError, ValueError) as e:
            return [], ToolRun(tool="npm audit", status="error", detail=f"advisory lookup failed ({type(e).__name__}): NOT checked")
    if "error" in data and not data.get("vulnerabilities"):
        return [], ToolRun(tool="npm audit", status="error", detail="advisory lookup failed: " + redact(str(data["error"])[:200]))
    out = []
    for name, v in (data.get("vulnerabilities") or {}).items():
        sev = {"critical": "critical", "high": "high", "moderate": "medium"}.get(v.get("severity"), "low")
        via = [x.get("url") or x.get("title") for x in v.get("via", []) if isinstance(x, dict)]
        out.append({"rule_id": "DEP-VULNERABLE", "category": "dependencies", "title": f"npm package {name} is vulnerable ({v.get('severity')})",
                    "severity": sev, "confidence": "high", "file": rel, "line": None,
                    "evidence_text": f"{name} {v.get('range', '')}: {'; '.join(str(x) for x in via[:3])}",
                    "description": "A published npm advisory affects the locked version.",
                    "remediation": "npm audit fix (or upgrade the package) and re-run the tests.",
                    "references": [str(x) for x in via[:5]], "dependencies": [name], "state": "detected", "source": "npm-audit"})
    return out, ToolRun(tool="npm audit", status="ran", retrieved_at=started, version=_version([npm, "--version"]),
                        detail=f"npm registry advisories; {len(out)} vulnerable package(s)")


_JS_RULES = [
    ("JS-EVAL", "injection", r"\b(eval|new Function)\s*\(\s*(?!['\"`][^'\"`]*['\"`]\s*\))", "eval/new Function on dynamic input",
     "high", "medium", "Use JSON.parse or explicit logic instead of evaluating strings.", ["CWE-95"]),
    ("JS-CMDI", "injection", r"\b(exec|execSync)\s*\(\s*(`[^`]*\$\{|[^)'\"`]*\+)", "child_process exec with a built command",
     "critical", "medium", "Use execFile/spawn with an argument array and validate inputs.", ["CWE-78"]),
    ("JS-SQLI", "injection", r"\.(query|raw|execute)\s*\(\s*(`[^`]*\$\{[^}]*req\.|['\"][^'\"]*['\"]\s*\+\s*req\.)",
     "SQL built from request data", "high", "high", "Use parameterized queries ($1 / ? placeholders).", ["CWE-89"]),
    ("JS-XSS", "web", r"res\.send\(\s*`[^`]*<[^`]*\$\{[^}]*req\.", "HTML built from request data (reflected XSS)",
     "high", "medium", "Escape output or render with a template engine that escapes by default.", ["CWE-79"]),
    ("JS-DANGEROUS-HTML", "web", r"dangerouslySetInnerHTML", "dangerouslySetInnerHTML in React",
     "medium", "low", "Avoid it, or sanitize with DOMPurify first.", ["CWE-79"]),
    ("JS-OPEN-REDIRECT", "web", r"res\.redirect\(\s*req\.(query|body|params)", "Redirect to a URL from the request",
     "medium", "high", "Redirect only to relative paths or an allow-list.", ["CWE-601"]),
    ("JS-CORS-ANY", "web", r"cors\(\s*\{[^}]*origin\s*:\s*['\"]\*['\"][^}]*credentials\s*:\s*true", "CORS: any origin with credentials",
     "high", "high", "List allowed origins explicitly.", ["CWE-942"]),
    ("JS-JWT-DECODE", "auth", r"jwt\.decode\(", "jwt.decode does not verify signatures", "medium", "low",
     "Use jwt.verify(token, secret) for authentication decisions.", ["CWE-347"]),
]


def js_rules(files: Dict[str, str]) -> Tuple[List[Raw], ToolRun]:
    out = []
    uses_express = any(re.search(r"require\(['\"]express['\"]\)|from ['\"]express['\"]", s) for s in files.values())
    for rel, src in files.items():
        if not rel.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")) or "node_modules/" in rel:
            continue
        for rid, cat, pattern, title, sev, conf, fix, refs in _JS_RULES:
            for m in re.finditer(pattern, src):
                line = src.count("\n", 0, m.start()) + 1
                out.append({"rule_id": rid, "category": cat, "title": title, "severity": sev, "confidence": conf,
                            "file": rel, "line": line, "evidence_text": src.splitlines()[line - 1].strip()[:200],
                            "description": title + " (pattern match; data flow not proven).", "remediation": fix,
                            "references": refs, "state": "detected" if conf == "high" else "requires_review", "source": "guardian-js"})
    if uses_express and not any("helmet" in s for s in files.values()):
        server = next((r for r, s in files.items() if re.search(r"express\(\)", s)), None)
        out.append({"rule_id": "JS-NO-SECURITY-HEADERS", "category": "web", "title": "Express app without security headers (helmet)",
                    "severity": "low", "confidence": "medium", "file": server, "line": None,
                    "evidence_text": "express() used; helmet not found", "description": "Missing headers such as "
                    "Content-Security-Policy, X-Content-Type-Options and frame protection.",
                    "remediation": "app.use(helmet()) (and configure a CSP).", "references": ["OWASP A05:2021"],
                    "state": "detected", "source": "guardian-js"})
    return out, ToolRun(tool="JavaScript rules", status="ran", detail=f"{len(out)} result(s) (pattern-based)")


def config_rules(files: Dict[str, str]) -> Tuple[List[Raw], ToolRun]:
    out = []
    for rel, src in files.items():
        name = Path(rel).name
        if name == "Dockerfile":
            users = re.findall(r"^\s*USER\s+(\S+)", src, re.M)
            if not users or users[-1] in ("root", "0"):
                out.append(_cfg("CFG-DOCKER-ROOT", "Container runs as root", "medium", rel, None,
                                "no USER instruction" if not users else f"USER {users[-1]}",
                                "A compromise of the app gives root inside the container.",
                                "Add a non-root user (USER app) after installing dependencies.", ["CWE-250"]))
        if name.startswith("docker-compose") and name.endswith((".yml", ".yaml")):
            for m in re.finditer(r"^\s*(privileged:\s*true|network_mode:\s*['\"]?host)", src, re.M):
                line = src.count("\n", 0, m.start()) + 1
                out.append(_cfg("CFG-COMPOSE-PRIVILEGE", f"Compose service uses {m.group(1).split(':')[0]}", "high", rel, line,
                                m.group(1), "The container gets host-level privileges or networking.",
                                "Remove it; grant only the specific capability needed.", ["CWE-250"]))
        if name == "requirements.txt":
            unpinned = [ln.strip() for ln in src.splitlines() if ln.strip() and not ln.strip().startswith(("#", "-"))
                        and "==" not in ln]
            if unpinned:
                out.append({"rule_id": "DEP-UNPINNED", "category": "dependencies",
                            "title": f"{len(unpinned)} unpinned Python requirement(s)", "severity": "low", "confidence": "high",
                            "file": rel, "line": None, "evidence_text": ", ".join(unpinned[:10]),
                            "description": "Unpinned requirements install whatever version is current, which can bring "
                            "vulnerable or breaking releases, and advisory checks only cover the version resolved today.",
                            "remediation": "Pin versions (pip freeze / pip-compile).", "references": [], "state": "detected",
                            "dependencies": unpinned[:10], "source": "guardian"})
    return out, ToolRun(tool="configuration rules", status="ran", detail=f"{len(out)} result(s)")


def _cfg(rid, title, sev, rel, line, evidence, desc, fix, refs) -> Raw:
    return {"rule_id": rid, "category": "configuration", "title": title, "severity": sev, "confidence": "high", "file": rel,
            "line": line, "evidence_text": evidence, "description": desc, "remediation": fix, "references": refs,
            "state": "detected", "source": "guardian"}


def _version(cmd: List[str]) -> Optional[str]:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout.strip()
        m = re.search(r"\d+\.\d+(\.\d+)?", out)
        return m.group(0) if m else None
    except (OSError, subprocess.SubprocessError):
        return None
