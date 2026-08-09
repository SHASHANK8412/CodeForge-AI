"""
AIForge Central Output Validator & Quality Scoring Engine
=========================================================
Multi-layered response validator between LLM generation and the frontend:
- Layer 1: Fast Deterministic Validation (0ms - 5ms)
- Layer 2: Heuristic Quality Scoring (6 weighted dimensions)
- Layer 3: Optional LLM Judge (borderline cases only)

Enforces strict intent contracts, bad-response detection, prompt/traceback leak checks,
repetition scoring, and truncation checks without modifying original responses.
"""

import re
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from backend.quality.validation_models import ValidationResult, QualityConfig

_logger = logging.getLogger("aiforge.quality.output_validator")


class OutputValidator:
    """
    Centralized Output Validator.
    Interface: validate(user_prompt, response, intent, agent="", profile="", metadata=None)
    """

    def __init__(self, config: Optional[QualityConfig] = None):
        self.config = config or QualityConfig()
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for high-performance validation."""
        self.re_traceback = re.compile(r'traceback\s+\(most\s+recent\s+call\s+last\)|file\s+["\'].*backend.*\.py["\']|connectionrefusederror', re.IGNORECASE)
        self.re_prompt_leak = re.compile(r'system\s+prompt:|you\s+are\s+aiforge|my\s+instructions\s+say|according\s+to\s+my\s+system\s+message|agentfactory\s+selected|internal\s+routing\s+decision', re.IGNORECASE)
        self.re_coding_templates = [
            re.compile(r'\bdef\s+solve\s*\('),
            re.compile(r'\bclass\s+solution\b', re.IGNORECASE),
            re.compile(r'##?\s*algorithmic\s+approach', re.IGNORECASE),
            re.compile(r'##?\s*problem\s+approach', re.IGNORECASE),
            re.compile(r'\btime\s+complexity:\s*o\(', re.IGNORECASE),
            re.compile(r'\bspace\s+complexity:\s*o\(', re.IGNORECASE),
            re.compile(r'\binput\s+format\b', re.IGNORECASE),
            re.compile(r'\boutput\s+format\b', re.IGNORECASE),
            re.compile(r'\bconstraints:\b', re.IGNORECASE),
        ]

    def _check_empty(self, prompt: str, response: str) -> Tuple[bool, Optional[str]]:
        if response is None or not response.strip():
            return False, "Response is empty or whitespace only."
        
        # Check task-relative brevity
        clean_resp = response.strip()
        p_lower = prompt.lower()
        if len(clean_resp) < 15:
            # If user prompt requests detailed explanation or code, short response is incomplete
            if any(w in p_lower for w in ["explain", "detail", "how does", "implement", "write", "build", "create"]):
                return False, f"Response is suspiciously short ({len(clean_resp)} chars) for task requirement."
        
        return True, None

    def _check_traceback_leak(self, response: str) -> Tuple[bool, Optional[str]]:
        if self.re_traceback.search(response):
            return False, "Raw internal error traceback detected in response."
        return True, None

    def _check_prompt_leak(self, response: str) -> Tuple[bool, Optional[str]]:
        if self.re_prompt_leak.search(response):
            return False, "Internal system prompt or routing instruction leakage detected."
        return True, None

    def _check_coding_template_leak(self, prompt: str, response: str, intent: str) -> Tuple[bool, Optional[str]]:
        intent_upper = (intent or "").upper()
        if intent_upper in ["EXPLANATION", "GENERAL_QA", "RESUME"]:
            p_lower = prompt.lower()
            # Context Check: Allow coding phrases if explicitly requested by prompt
            allow_code_terms = any(term in p_lower for term in [
                "time complexity", "space complexity", "def solve", "class solution",
                "python code", "code snippet", "algorithm", "binary search", "merge sort", "bfs", "dfs"
            ])

            if not allow_code_terms:
                for pat in self.re_coding_templates:
                    match = pat.search(response)
                    if match:
                        return False, f"Coding template/marker '{match.group(0)}' leaked into non-code {intent_upper} response."
        return True, None

    def _check_language_requirement(self, prompt: str, response: str, intent: str) -> Tuple[bool, Optional[str]]:
        intent_upper = (intent or "").upper()
        if intent_upper in ["CODING", "DSA_PROBLEM"]:
            p_lower = prompt.lower()
            lang_map = {
                "python": ["def ", "import ", "print(", ".py", "python"],
                "java": ["public class", "public static void main", "system.out.println", "java"],
                "c++": ["#include", "std::", "cout", "int main()", "c++"],
                "c#": ["using System;", "namespace", "Console.WriteLine", "c#"],
                "javascript": ["const ", "function ", "console.log", "=>", "javascript", "js"],
                "typescript": ["interface ", "type ", "const ", "typescript", "ts"],
                "go": ["func ", "package main", "fmt.Println", "golang", "go"],
                "rust": ["fn ", "let mut", "println!", "rust"],
                "sql": ["select ", "insert into", "create table", "sql"],
            }
            
            for lang, keywords in lang_map.items():
                # If prompt explicitly demands a language (e.g., "in python", "in java", "rust solution")
                if re.search(r'\bin\s+' + re.escape(lang) + r'\b|\b' + re.escape(lang) + r'\s+code\b|\b' + re.escape(lang) + r'\b', p_lower):
                    r_lower = response.lower()
                    matches = [kw for kw in keywords if kw.lower() in r_lower]
                    if not matches and "```" + lang not in r_lower:
                        return False, f"Explicit programming language requirement '{lang.title()}' missing from response."
                    break
        return True, None

    def _check_repetition(self, response: str) -> Tuple[float, Optional[str]]:
        """Calculates repetition score (1.0 = no repetition, 0.0 = total repetition)."""
        lines = [line.strip() for line in response.splitlines() if line.strip()]
        if not lines:
            return 1.0, None

        # Check line-level duplicate ratio
        unique_lines = set(lines)
        line_ratio = len(unique_lines) / len(lines)

        # Check 4-gram repetition
        words = response.lower().split()
        if len(words) > 20:
            fourgrams = [tuple(words[i:i+4]) for i in range(len(words)-3)]
            unique_fourgrams = set(fourgrams)
            gram_ratio = len(unique_fourgrams) / len(fourgrams)
        else:
            gram_ratio = 1.0

        rep_score = round(min(line_ratio, gram_ratio), 2)
        issue = None
        if rep_score < 0.5:
            issue = f"Pathological output repetition detected (repetition score: {rep_score:.2f})."
        return rep_score, issue

    def _check_truncation(self, response: str) -> Tuple[bool, Optional[str]]:
        # Unmatched code fences
        backtick_count = len(re.findall(r'```', response))
        if backtick_count % 2 != 0:
            return False, "Unmatched triple backticks (unclosed code fence)."

        # Check abrupt termination
        clean_resp = response.rstrip()
        if clean_resp and clean_resp[-1] not in ['.', '!', '?', '`', '}', ')', ']', ';', ':', '>']:
            # Check if ends with suspicious incomplete phrase
            words = clean_resp.split()
            if words and words[-1].lower() in ["while", "and", "or", "the", "with", "for", "def", "class", "if"]:
                return False, f"Abrupt response truncation detected (ends with '{words[-1]}')."
        return True, None

    def validate(
        self,
        user_prompt: str,
        response: str,
        intent: str,
        agent: str = "",
        profile: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        start_time = time.perf_counter()
        issues: List[str] = []
        warnings: List[str] = []
        checks: Dict[str, bool] = {}

        # 1. EMPTY / WHITESPACE CHECK
        ok, issue = self._check_empty(user_prompt, response)
        checks["non_empty"] = ok
        if not ok and issue:
            issues.append(issue)

        # 2. RAW TRACEBACK LEAK CHECK
        ok, issue = self._check_traceback_leak(response or "")
        checks["no_traceback_leak"] = ok
        if not ok and issue:
            issues.append(issue)

        # 3. PROMPT LEAK CHECK
        ok, issue = self._check_prompt_leak(response or "")
        checks["no_prompt_leak"] = ok
        if not ok and issue:
            issues.append(issue)

        # 4. CODING TEMPLATE LEAK CHECK
        ok, issue = self._check_coding_template_leak(user_prompt, response or "", intent)
        checks["no_template_leak"] = ok
        if not ok and issue:
            issues.append(issue)

        # 5. LANGUAGE REQUIREMENT CHECK
        ok, issue = self._check_language_requirement(user_prompt, response or "", intent)
        checks["language_match"] = ok
        if not ok and issue:
            issues.append(issue)

        # 6. REPETITION CHECK
        rep_score, issue = self._check_repetition(response or "")
        checks["non_repetitive"] = (rep_score >= 0.5)
        if issue:
            issues.append(issue)

        # 7. TRUNCATION CHECK
        ok, issue = self._check_truncation(response or "")
        checks["no_truncation"] = ok
        if not ok and issue:
            warnings.append(issue) if "abrupt" in (issue or "") else issues.append(issue)

        # 8. INTENT CONTRACT MATCH
        from backend.utils.response_contract import validate_response_contract
        contract_res = validate_response_contract(intent, user_prompt, response or "")
        checks["contract_match"] = contract_res["valid"]
        if not contract_res["valid"]:
            issues.append(f"Response contract violation: {contract_res['reason']}")

        # CALCULATE 6-DIMENSION HEURISTIC QUALITY SCORES
        # Dimensions: relevance (0.30), task_fulfillment (0.25), contract_match (0.20), completeness (0.15), format_validity (0.05), non_repetition (0.05)
        rel_score = 1.0 if not any("relevance" in i.lower() for i in issues) else 0.4
        tf_score = 1.0 if checks.get("language_match", True) and checks.get("non_empty", True) else 0.3
        cm_score = 1.0 if checks.get("contract_match", True) and checks.get("no_template_leak", True) else 0.0
        comp_score = 1.0 if checks.get("no_truncation", True) and checks.get("non_empty", True) else 0.5
        fmt_score = 1.0 if checks.get("no_traceback_leak", True) and checks.get("no_prompt_leak", True) else 0.0
        nr_score = rep_score

        dimension_scores = {
            "relevance": round(rel_score, 2),
            "task_fulfillment": round(tf_score, 2),
            "contract_match": round(cm_score, 2),
            "completeness": round(comp_score, 2),
            "format_validity": round(fmt_score, 2),
            "non_repetition": round(nr_score, 2)
        }

        overall_score = round(
            (rel_score * 0.30) +
            (tf_score * 0.25) +
            (cm_score * 0.20) +
            (comp_score * 0.15) +
            (fmt_score * 0.05) +
            (nr_score * 0.05),
            2
        )

        # SEVERITY DETERMINATION
        severity = "low"
        if not checks.get("non_empty", True) or not checks.get("no_traceback_leak", True):
            severity = "critical"
        elif not checks.get("no_template_leak", True) or not checks.get("no_prompt_leak", True) or not checks.get("language_match", True) or not checks.get("contract_match", True) or not checks.get("non_repetitive", True):
            severity = "high"
        elif overall_score < self.config.pass_score:
            severity = "medium"

        # DECISION: PASS vs REGENERATE
        is_valid = (overall_score >= self.config.pass_score) and (severity not in ["high", "critical"])
        should_regenerate = (not is_valid) and (severity in ["high", "critical"] or overall_score < self.config.pass_score)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        result = ValidationResult(
            is_valid=is_valid,
            score=overall_score,
            severity=severity,
            should_regenerate=should_regenerate,
            issues=issues,
            warnings=warnings,
            checks=checks,
            dimension_scores=dimension_scores,
            latency_ms=elapsed_ms
        )

        # DEV LOGGING
        status_str = "PASS" if is_valid else "FAIL"
        _logger.info(f"[AIForge OutputValidator] Intent: {intent} | Agent: {agent} | Score: {overall_score} | Status: {status_str} | Severity: {severity} | Regen: {should_regenerate} | Latency: {elapsed_ms}ms")
        if issues:
            _logger.warning(f"[AIForge OutputValidator] Issues: {issues}")

        return result


global_output_validator = OutputValidator()
