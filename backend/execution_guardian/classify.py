"""
Failure classification and routing. Deterministic rules read the real output of each failed check; a model is
asked only when no rule matches, its answer must be one of the known categories, and it is labelled as a model
classification. Nothing is invented: excerpts, files and test names come from the output or are left empty.

Routing (responsible agent):
  frontend_build_error, frontend files                       -> frontend (Frontend Agent)
  database_connection_error, models/schema/migration files   -> database (Database Agent)
  dependency_install_error                                   -> dependency_resolver (controlled: requirements only)
  api_contract_mismatch, configuration_error                 -> debug (Debug Agent / integration)
  backend_startup_error, runtime_exception                   -> backend (Backend Agent; Debug Agent strategies first)
  syntax / compilation / failing tests                       -> by the affected implementation file
  infrastructure_error                                       -> none (not repairable: the environment must change)
"""

import hashlib
import re
import uuid
from typing import Callable, List, Optional

from backend.execution_guardian.models import CATEGORIES, Check, Failure

SEVERITY = {"syntax_error": "critical", "compilation_error": "critical", "dependency_install_error": "critical",
            "frontend_build_error": "critical", "backend_startup_error": "critical", "database_connection_error": "high",
            "api_contract_mismatch": "high", "unit_test_failure": "high", "integration_test_failure": "high",
            "configuration_error": "high", "runtime_exception": "high", "infrastructure_error": "medium"}
NEXT = {"syntax_error": "fix the syntax error in the named file",
        "compilation_error": "fix the undefined name / import the static check reported",
        "dependency_install_error": "correct requirements.txt / package.json (missing or uninstallable package)",
        "frontend_build_error": "fix the frontend source the build reported",
        "backend_startup_error": "fix the error the app raised at startup (see the container log)",
        "database_connection_error": "fix the database URL / setup the app uses at startup",
        "api_contract_mismatch": "align the client calls and the API routes",
        "unit_test_failure": "fix the implementation the failing test exercises (tests are not edited)",
        "integration_test_failure": "fix the integration the failing test exercises (tests are not edited)",
        "configuration_error": "provide or correct the configuration the app reads",
        "runtime_exception": "fix the exception raised at runtime",
        "infrastructure_error": "make the isolated environment available (e.g. start Docker) and verify again"}

FILE_RE = re.compile(r'File "([^"]+\.py)", line (\d+)')
PATHLINE_RE = re.compile(r"((?:[\w.\-]+/)*[\w.\-]+\.(?:py|jsx?|tsx?|vue)):(\d+)")
FAILED_TEST_RE = re.compile(r"^(?:FAILED|ERROR) ((?:[\w.\-]+/)*[\w.\-]+\.py::[\w\[\]\-.:]+)", re.M)


def _norm_file(path: str, known: List[str]) -> Optional[str]:
    p = path.replace("\\", "/")
    for k in known:
        if p.endswith(k):
            return k
    for marker in ("/app/", "/work/"):
        if marker in p:
            return p.split(marker, 1)[1]
    return None if p.startswith("/") or ":" in p[:3] else p


def _files(text: str, known: List[str]) -> List[str]:
    out = []
    for m in FILE_RE.finditer(text):
        f = _norm_file(m.group(1), known)
        if f and f not in out and "site-packages" not in m.group(1) and "/deps/" not in m.group(1):
            out.append(f)
    for m in PATHLINE_RE.finditer(text):
        f = _norm_file(m.group(1), known)
        if f and f not in out and (not known or f in known):
            out.append(f)
    return out[:10]


def _is_test(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return "/tests/" in f"/{path}" or name.startswith("test_") or name.endswith(("_test.py", ".test.js", ".test.jsx", ".spec.js"))


def route(category: str, files: List[str]) -> Optional[str]:
    if category == "infrastructure_error":
        return None
    if category == "dependency_install_error":
        return "dependency_resolver"
    if category == "frontend_build_error":
        return "frontend"
    if category == "database_connection_error":
        return "database"
    if category in ("api_contract_mismatch", "configuration_error"):
        return "debug"
    impl = [f for f in files if not _is_test(f)] or files
    for f in impl:
        low = f.lower()
        if low.startswith(("frontend/", "src/")) or low.endswith((".js", ".jsx", ".ts", ".tsx", ".vue")):
            return "frontend"
        if any(k in low for k in ("models", "schema", "migration", "database", "db.py", "/db/")):
            return "database"
    return "backend"


def _signature(category: str, check: str, text: str) -> str:
    norm = re.sub(r"0x[0-9a-f]+|\d+(\.\d+)?|/[\w./\-]+", "#", text.lower())[:400]
    return hashlib.sha1(f"{category}|{check}|{norm}".encode()).hexdigest()[:16]


def _failure(check: Check, category: str, summary: str, excerpt: str, files: List[str], tests: List[str], rule: str,
             attempt: int) -> Failure:
    repairable = category != "infrastructure_error"
    return Failure(id="gf_" + uuid.uuid4().hex[:10], check=check.name, category=category, severity=SEVERITY[category],
                   summary=summary[:400], log_excerpt=excerpt, files=files, failing_tests=tests,
                   responsible_agent=route(category, files), classified_by=rule, next_action=NEXT[category],
                   signature=_signature(category, check.name, summary), repairable=repairable, attempt=attempt)


def _first(text: str, pattern: str) -> Optional[str]:
    m = re.search(pattern, text, re.M)
    return m.group(0).strip() if m else None


def classify_check(check: Check, known_files: List[str], attempt: int = 0,
                   llm: Optional[Callable[[str, str], str]] = None) -> List[Failure]:
    """The failures behind one FAILED or BLOCKED check."""
    text = check.log_excerpt or check.error_summary or check.reason or ""
    files = _files(text, known_files)
    if check.status == "BLOCKED":
        return [_failure(check, "infrastructure_error", f"{check.label} could not run: {check.reason}", "", [], [],
                         "rule:blocked_check", attempt)]
    if check.status != "FAILED":
        return []
    out: List[Failure] = []
    name = check.name
    if name == "python_syntax":
        return [_failure(check, "syntax_error", _first(text, r".*(SyntaxError|IndentationError).*") or check.error_summary or "syntax error",
                         check.log_excerpt, files, [], "rule:python_syntax", attempt)]
    if name == "quality_gate":
        return [_failure(check, "compilation_error", check.error_summary or "blocking static errors", check.log_excerpt, files, [],
                         "rule:quality_gate", attempt)]
    if name == "security_static":
        return []                                 # optional: a warning, not an application failure
    if name in ("python_dependencies", "frontend_dependencies"):
        msg = (_first(text, r".*(No matching distribution found for|Could not find a version|ERESOLVE|404 Not Found|"
                            r"ResolutionImpossible|npm ERR!).*") or check.error_summary)
        f = _failure(check, "dependency_install_error", msg, check.log_excerpt,
                     ["requirements.txt"] if name == "python_dependencies" else ["package.json"], [],
                     f"rule:{name}", attempt)
        return [f]
    if name == "frontend_build":
        return [_failure(check, "frontend_build_error", _first(text, r".*(error|Error|ERROR).*") or "the build failed",
                         check.log_excerpt, files, [], "rule:frontend_build", attempt)]
    if name == "frontend_tests":
        return [_failure(check, "unit_test_failure", _first(text, r".*(FAIL|✕|failed).*") or "frontend tests failed",
                         check.log_excerpt, files, [], "rule:frontend_tests", attempt)]
    if name == "backend_startup":
        if re.search(r"OperationalError|could not connect to server|Connection refused.*(5432|3306|27017)|"
                     r"unable to open database file|sqlalchemy\.exc", text, re.I):
            cat, rule = "database_connection_error", "rule:startup_database"
        elif re.search(r"ModuleNotFoundError|No module named", text):
            cat, rule = "dependency_install_error", "rule:startup_missing_module"
        elif re.search(r"KeyError: '[A-Z_]+'|environment variable|ValidationError.*[Ss]ettings|not set", text):
            cat, rule = "configuration_error", "rule:startup_configuration"
        else:
            cat, rule = "backend_startup_error", "rule:backend_startup"
        msg = _first(text, r"^\w*(Error|Exception)\b.*") or check.error_summary
        return [_failure(check, cat, msg, check.log_excerpt, files, [], rule, attempt)]
    if name == "python_tests":
        if check.timed_out:
            return [_failure(check, "runtime_exception", check.error_summary, check.log_excerpt, files, [], "rule:test_timeout", attempt)]
        tests = FAILED_TEST_RE.findall(text)
        if re.search(r"ModuleNotFoundError: No module named|ImportError while importing", text):
            out.append(_failure(check, "dependency_install_error" if "No module named" in text else "compilation_error",
                                _first(text, r".*(ModuleNotFoundError|ImportError).*") or "import error", check.log_excerpt,
                                files, tests, "rule:test_import_error", attempt))
            return out
        if re.search(r"SyntaxError|IndentationError", text):
            return [_failure(check, "syntax_error", _first(text, r".*(SyntaxError|IndentationError).*"), check.log_excerpt, files, tests,
                             "rule:test_syntax", attempt)]
        if tests:
            integ = [t for t in tests if re.search(r"integration|e2e|end_to_end", t, re.I)]
            unit = [t for t in tests if t not in integ]
            for group, cat in ((unit, "unit_test_failure"), (integ, "integration_test_failure")):
                if group:
                    err = _first(text, r"^E\s+.*") or check.error_summary
                    # an assertion that did not hold is a test failure; any other exception is a runtime exception
                    raised = re.search(r"^E\s+(\w+(?:Error|Exception))\b", text, re.M)
                    kind = ("runtime_exception" if cat == "unit_test_failure" and raised and raised.group(1) != "AssertionError"
                            and not re.search(r"^E\s+assert\b", text, re.M) else cat)
                    out.append(_failure(check, kind, f"{len(group)} failing test(s): {err}", check.log_excerpt, files, group,
                                        f"rule:{kind}", attempt))
            return out
    # no rule matched: ask the model (if any), constrained to the known categories
    if llm is not None:
        try:
            answer = llm("Classify the failure of a software verification check. Answer with exactly one of: "
                         + ", ".join(CATEGORIES) + ".", f"Check: {check.label}\nOutput:\n{text[-2000:]}")
            cat = next((c for c in CATEGORIES if c in (answer or "").lower()), None)
        except Exception:  # noqa: BLE001 - the model is optional; the fallback below is labelled
            cat = None
        if cat:
            return [_failure(check, cat, check.error_summary or f"{check.label} failed", check.log_excerpt, files, [],
                             "model (no rule matched; the category is the model's answer)", attempt)]
    return [_failure(check, "runtime_exception", check.error_summary or f"{check.label} failed", check.log_excerpt, files, [],
                     "fallback (no rule matched and no model classification)", attempt)]


def classify(checks: List[Check], known_files: List[str], attempt: int = 0,
             llm: Optional[Callable[[str, str], str]] = None) -> List[Failure]:
    out: List[Failure] = []
    for c in checks:
        if c.required or c.status == "FAILED":
            out += classify_check(c, known_files, attempt, llm)
    return out
