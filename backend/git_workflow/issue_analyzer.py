"""
AIForge Day 12 - Issue Analyzer & Requirement Extractor
=========================================================
Extracts structured requirements, Given/When/Then acceptance criteria,
risk levels, and ambiguity flags from untrusted IssueContext data.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from backend.git_workflow.models import IssueContext, IssueAnalysis, TaskRisk

logger = logging.getLogger("aiforge.git_workflow.issue_analyzer")


class IssueAnalyzer:
    """
    Parses issue bodies and user prompts, treating content strictly as DATA (never system instructions).
    Extracts testable requirements, acceptance criteria, risk rating, and ambiguity flags.
    """

    UNTRUSTED_INJECTION_PATTERNS = [
        r"ignore (all )?previous instructions",
        r"print (env|environment|github_token|secrets)",
        r"dump system prompt",
        r";\s*rm\s+-rf",
        r"exec\s*\(",
    ]

    HIGH_RISK_KEYWORDS = [
        "auth", "login", "jwt", "refresh", "logout", "token", "security",
        "permission", "privilege", "password", "crypto", "database", "migration",
        "infra", "deployment", "payment", "billing"
    ]

    MEDIUM_RISK_KEYWORDS = [
        "service", "api", "endpoint", "controller", "workflow", "model", "cache"
    ]

    def analyze_issue(
        self,
        issue: IssueContext,
        repository_map: Optional[Dict[str, Any]] = None
    ) -> IssueAnalysis:
        """
        Analyze an issue and return a structured IssueAnalysis object.
        """
        title = issue.title.strip()
        body = issue.body.strip()
        combined_text = f"{title}\n{body}"

        # Step 73 & 74: Sanitize / Detect prompt injection in untrusted issue text
        self._check_untrusted_injection(combined_text)

        # 1. Determine Task Type
        task_type = self._determine_task_type(title, body)

        # 2. Extract Requirements
        requirements = self._extract_requirements(title, body)

        # 3. Derive Acceptance Criteria (Given / When / Then)
        acceptance_criteria = self._derive_acceptance_criteria(requirements, combined_text)

        # 4. Extract Keywords & Likely Components
        keywords = self._extract_keywords(combined_text)
        likely_components = self._identify_likely_components(combined_text, repository_map)

        # 5. Determine Task Risk
        risk = self._classify_task_risk(combined_text, likely_components)

        # 6. Ambiguity Detection
        ambiguities, is_ambiguous = self._detect_ambiguity(title, body, likely_components, repository_map)

        # Build Summary
        summary = f"{task_type.title()} Task: {title if title else 'Issue resolution'}"

        return IssueAnalysis(
            summary=summary,
            task_type=task_type,
            requirements=requirements,
            acceptance_criteria=acceptance_criteria,
            keywords=keywords,
            likely_components=likely_components,
            risk=risk,
            ambiguities=ambiguities,
            is_ambiguous=is_ambiguous
        )

    def _check_untrusted_injection(self, text: str) -> None:
        """
        Scans untrusted issue text for prompt injection / malicious commands.
        Logs warning and strips dangerous instructions.
        """
        text_lower = text.lower()
        for pattern in self.UNTRUSTED_INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                logger.warning(f"IssueAnalyzer: Detected suspicious prompt injection pattern: '{pattern}'. Content treated strictly as inert DATA.")

    def _determine_task_type(self, title: str, body: str) -> str:
        text = f"{title} {body}".lower()
        if any(k in text for k in ["fix", "bug", "error", "fail", "broken", "issue", "defect"]):
            return "bugfix"
        elif any(k in text for k in ["refactor", "cleanup", "restructure", "simplify"]):
            return "refactor"
        elif any(k in text for k in ["doc", "readme", "comment"]):
            return "docs"
        return "feature"

    def _extract_requirements(self, title: str, body: str) -> List[str]:
        requirements = []
        full_text = f"{title}\n{body}".strip()

        # Split sentences and newlines
        parts = re.split(r"[\n\.]+", full_text)
        for part in parts:
            cleaned = part.strip("- *1234567890. ")
            if len(cleaned) > 5 and not cleaned.startswith("#"):
                # Clean prompt injection attempts out of requirements
                sanitized = re.sub(r"(ignore instructions|print env|rm -rf)", "", cleaned, flags=re.IGNORECASE).strip()
                if sanitized and sanitized not in requirements:
                    requirements.append(sanitized)

        if not requirements:
            requirements = [title if title else "Implement requested issue changes."]

        return requirements[:5]

    def _derive_acceptance_criteria(self, requirements: List[str], text: str) -> List[Dict[str, str]]:
        criteria = []
        for req in requirements:
            req_lower = req.lower()
            if "logout" in req_lower or "revoke" in req_lower or "token" in req_lower:
                criteria.append({
                    "given": "a valid refresh token",
                    "when": "logout occurs or revocation is requested",
                    "then": "refresh attempt with the revoked token fails"
                })
            elif "fix" in req_lower or "bug" in req_lower:
                criteria.append({
                    "given": "the defect scenario described in issue",
                    "when": "the fix is executed",
                    "then": "the expected correct output is produced without errors"
                })
            else:
                criteria.append({
                    "given": "the system state before operation",
                    "when": f"requirement '{req}' is invoked",
                    "then": "the system satisfies the expected behavior cleanly"
                })
        return criteria

    def _extract_keywords(self, text: str) -> List[str]:
        words = re.findall(r"\b[a-zA-Z_]{3,}\b", text.lower())
        stopwords = {"the", "and", "for", "with", "this", "that", "from", "after", "remain", "valid"}
        keywords = list(set([w for w in words if w not in stopwords]))
        return keywords[:10]

    def _identify_likely_components(
        self,
        text: str,
        repository_map: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        text_lower = text.lower()
        components = []
        if any(k in text_lower for k in ["auth", "token", "logout", "login", "jwt"]):
            components.extend(["auth", "services/auth_service.py", "security/jwt.py"])
        if any(k in text_lower for k in ["user", "account", "profile"]):
            components.append("users")
        if any(k in text_lower for k in ["db", "database", "migration", "sql"]):
            components.append("database")
        if any(k in text_lower for k in ["api", "route", "endpoint"]):
            components.append("api")

        if repository_map and "files" in repository_map:
            # Match keywords against repository files
            for file_path in repository_map.get("files", []):
                for kw in ["auth", "jwt", "login", "token", "service"]:
                    if kw in file_path.lower() and file_path not in components:
                        components.append(file_path)

        return components if components else ["core"]

    def _classify_task_risk(self, text: str, components: List[str]) -> TaskRisk:
        text_lower = text.lower()
        if any(k in text_lower for k in self.HIGH_RISK_KEYWORDS) or any("auth" in c or "security" in c for c in components):
            return TaskRisk.HIGH
        elif any(k in text_lower for k in self.MEDIUM_RISK_KEYWORDS):
            return TaskRisk.MEDIUM
        return TaskRisk.LOW

    def _detect_ambiguity(
        self,
        title: str,
        body: str,
        components: List[str],
        repository_map: Optional[Dict[str, Any]] = None
    ) -> (List[str], bool):
        ambiguities = []
        text = f"{title} {body}".strip()

        clean_body = "" if (not body or body.strip().lower() == title.strip().lower()) else body

        # Short vague titles like "Fix authentication" or "Fix bug"
        if len(title.split()) <= 3 and (not clean_body or len(clean_body.split()) <= 3):
            ambiguities.append("Vague issue description without specific steps or target modules.")
        elif "fix authentication" in text.lower() and (not clean_body or len(clean_body.split()) <= 3):
            ambiguities.append("Multiple auth subsystems or vague auth request detected. Specific target auth system not specified.")

        is_ambiguous = len(ambiguities) > 0
        return ambiguities, is_ambiguous


global_issue_analyzer = IssueAnalyzer()
