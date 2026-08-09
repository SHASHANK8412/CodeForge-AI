"""
AIForge Requirement Alignment & Intent Fidelity Agent
=====================================================
Evaluates whether a generated project satisfies the original user prompt,
checking intent alignment, domain matching, and feature coverage.
Prevents AIForge from scoring 100/100 or exporting projects that hallucinate
unrelated domains (e.g. F1 / Motorsport when the user asked for a Todo App).
"""

import re
import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.requirement_fidelity")

# Domain keyword taxonomy for accurate intent & domain extraction
DOMAIN_TAXONOMY = {
    "Productivity / Task Management": ["todo", "task", "checklist", "kanban", "productivity", "reminder", "schedule", "notes"],
    "E-Commerce / Shopping": ["ecommerce", "e-commerce", "cart", "product", "checkout", "order", "catalog", "store", "shop"],
    "Blogging / Content Management": ["blog", "article", "post", "comment", "cms", "newsletter", "publication"],
    "Finance / Expense Tracking": ["expense", "budget", "finance", "money", "transaction", "income", "tracker", "accounting"],
    "Authentication & Identity": ["auth", "login", "jwt", "user profile", "identity", "registration", "signup", "oauth"],
    "Sports / Motorsport": ["formula 1", "f1", "grand prix", "racing", "motorsport", "driver", "lap time"],
    "Social & Messaging": ["chat", "social", "message", "feed", "follower", "friend", "network"],
    "Healthcare & Fitness": ["fitness", "health", "workout", "patient", "medical", "doctor", "gym"]
}


class RequirementFidelityAgent:
    """
    Evaluates generated ProjectSpec, ArchitectureSpec, and files against original user prompt.
    Produces RequirementFidelityResult.
    """

    def infer_expected_domain(self, prompt: str) -> str:
        """Determines expected product domain from user prompt text."""
        p_lower = prompt.lower()
        for domain_name, keywords in DOMAIN_TAXONOMY.items():
            if any(kw in p_lower for kw in keywords):
                return domain_name
        return "General Software Application"

    def extract_expected_features(self, prompt: str) -> List[str]:
        """Extracts core feature keywords from prompt."""
        p_lower = prompt.lower()
        words = re.findall(r"\b[a-z0-9_-]{3,}\b", p_lower)
        ignore = {"build", "create", "generate", "develop", "with", "app", "application", "using", "from", "that", "this", "have"}
        return [w for w in set(words) if w not in ignore]

    def evaluate_fidelity(
        self,
        user_prompt: str,
        project_spec: Dict[str, Any],
        architecture_spec: Dict[str, Any],
        files: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Evaluates requirement fidelity.
        Returns Dict with:
        - expected_domain
        - generated_domain
        - domain_matched
        - feature_coverage
        - fidelity_score
        - status (PASS/FAIL)
        - reason
        """
        prompt = user_prompt or project_spec.get("project_name", "")
        expected_domain = self.infer_expected_domain(prompt)
        expected_features = self.extract_expected_features(prompt)

        # Extract generated domain
        gen_domain = project_spec.get("domain") or architecture_spec.get("domain") or ""
        if not gen_domain:
            # Fallback: check project_name and requirements text in spec
            spec_str = str(project_spec) + str(architecture_spec)
            gen_domain = self.infer_expected_domain(spec_str)

        # Check domain match
        p_lower = prompt.lower()
        gen_lower = (gen_domain + " " + str(project_spec.get("requirements", []))).lower()

        # Flag explicit domain hallucinations (e.g. prompt asks for todo/expense, but generated talks about F1/racing)
        is_f1_prompt = any(kw in p_lower for kw in ["formula 1", "f1", "racing", "grand prix"])
        is_f1_generated = any(kw in gen_lower for kw in ["formula 1", "f1", "motorsport", "grand prix"])

        domain_matched = True
        if not is_f1_prompt and is_f1_generated:
            domain_matched = False

        if expected_domain != "General Software Application" and gen_domain != "General Software Application":
            if expected_domain != gen_domain and not (expected_domain in gen_domain or gen_domain in expected_domain):
                domain_matched = False

        # Calculate feature coverage
        all_generated_text = (
            str(project_spec) + " " +
            str(architecture_spec) + " " +
            " ".join(files.keys()) + " " +
            " ".join([c[:200] for c in files.values()])
        ).lower()

        matched_count = 0
        for feat in expected_features:
            if feat in all_generated_text:
                matched_count += 1

        feature_coverage = (matched_count / len(expected_features) * 100.0) if expected_features else 100.0

        # Fidelity score calculation
        if not domain_matched:
            fidelity_score = round(feature_coverage * 0.2, 1)  # Capped at 20 max if domain mismatches
            status = "FAIL"
            reason = f"Requirement Fidelity FAILED: Generated domain '{gen_domain}' does not match expected prompt domain '{expected_domain}'."
        elif feature_coverage < 60.0:
            fidelity_score = round(feature_coverage, 1)
            status = "FAIL"
            reason = f"Requirement Fidelity FAILED: Insufficient feature coverage ({feature_coverage:.1f}% matched)."
        else:
            fidelity_score = round(min(100.0, 50.0 + (feature_coverage * 0.5)), 1)
            status = "PASS"
            reason = f"Requirement Match PASS: Domain '{expected_domain}' matched with {feature_coverage:.1f}% feature coverage."

        return {
            "expected_domain": expected_domain,
            "generated_domain": gen_domain if gen_domain else expected_domain,
            "domain_matched": domain_matched,
            "feature_coverage": round(feature_coverage, 1),
            "fidelity_score": fidelity_score,
            "status": status,
            "reason": reason
        }


global_requirement_fidelity_agent = RequirementFidelityAgent()
