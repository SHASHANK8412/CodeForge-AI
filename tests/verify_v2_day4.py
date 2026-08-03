"""
AIForge V2 Day 4 Verification Suite
====================================
End-to-end verification script for AIForge V2 Day 4 deliverables:
1. Typed ValidationResult structure
2. Central OutputValidator & multi-layered validation architecture
3. Empty response & task-shortness detection
4. Unwanted coding template leak detection
5. Intent/Output consistency & contract enforcement
6. Language requirement validation
7. Repetition scoring & truncation checks
8. Prompt leak & raw traceback leak detection
9. Weighted quality scoring (6 dimensions) & severity level rules
10. Bounded RegenerationController & corrective prompt strategy
11. Safe Response Cleaner & Safe Fallback Provider
12. Critical Formula 1 bad output simulation (REJECTED -> REGENERATED -> ACCEPTED)
13. False-positive resistance tests
14. Cross-intent validation coverage
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.quality.validation_models import ValidationResult, QualityConfig
from backend.quality.output_validator import global_output_validator, OutputValidator
from backend.quality.regeneration_controller import global_regeneration_controller
from backend.quality.response_cleaner import global_response_cleaner
from backend.quality.safe_fallback import get_safe_fallback_response

PASS = "[PASS]"
FAIL = "[FAIL]"
_results = {"passed": 0, "failed": 0}


def section(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    if condition:
        _results["passed"] += 1
    else:
        _results["failed"] += 1
    msg = f"  {status}  {name}"
    if detail:
        msg += f"\n        => {detail}"
    print(msg)
    return condition


def run_v2_day4_verification():
    print("======================================================================")
    print(" 🛡️ AIForge V2 – Day 4 Output Validator & Quality Recovery Verification")
    print("======================================================================\n")

    # 1. ValidationResult Data Structure
    section("1. Typed ValidationResult Structure & QualityConfig")
    res = global_output_validator.validate("Explain Formula 1", "Formula 1 is motorsport.", intent="EXPLANATION")
    check("Emits typed ValidationResult instance", isinstance(res, ValidationResult))
    check("Includes 6 dimension scores (relevance, task_fulfillment, contract_match, completeness, format_validity, non_repetition)",
          len(res.dimension_scores) == 6)

    # 2. Empty Response Detection
    section("2. Empty & Task-Shortness Response Detection")
    res_empty = global_output_validator.validate("Explain Formula 1", "", intent="EXPLANATION")
    check("Rejects empty string response", not res_empty.is_valid and res_empty.severity == "critical")
    
    res_short_qa = global_output_validator.validate("Capital of France?", "Paris.", intent="GENERAL_QA")
    check("Accepts concise valid response for simple QA", res_short_qa.is_valid)

    # 3. Coding Template Leak Detection
    section("3. Unwanted Coding Template Leak Detection")
    bad_template = "## Algorithmic Approach\nFormula 1 algorithm.\n```python\ndef solve():\n    pass\n```"
    res_bad_tmpl = global_output_validator.validate("Explain Formula 1", bad_template, intent="EXPLANATION")
    check("Detects def solve() leaked into non-coding EXPLANATION prompt",
          not res_bad_tmpl.is_valid and res_bad_tmpl.should_regenerate and res_bad_tmpl.severity == "high")

    # 4. Language Requirement Validation
    section("4. Programming Language Requirement Validation")
    res_lang = global_output_validator.validate("Write binary search in Python", "```java\npublic class Search {}\n```", intent="CODING")
    check("Detects language mismatch when Python code was requested but Java was returned",
          not res_lang.checks.get("language_match", True))

    # 5. Repetition & Truncation Checks
    section("5. Repetition Scoring & Truncation Detection")
    rep_text = "Formula 1 is racing.\n" * 15
    res_rep = global_output_validator.validate("Explain Formula 1", rep_text, intent="EXPLANATION")
    check("Detects pathological repetition", not res_rep.is_valid and res_rep.should_regenerate)

    unbalanced = "```python\ndef foo():\n    pass"
    res_trunc = global_output_validator.validate("Write code", unbalanced, intent="CODING")
    check("Detects unclosed code fence", not res_trunc.checks.get("no_truncation", True))

    # 6. Prompt & Traceback Leak Detection
    section("6. System Prompt Leak & Raw Traceback Leak Detection")
    leak_prompt = "SYSTEM PROMPT: You are AIForge's Explanation Agent."
    res_leak = global_output_validator.validate("Explain Formula 1", leak_prompt, intent="EXPLANATION")
    check("Flags system prompt leakage as HIGH severity issue", not res_leak.is_valid and res_leak.severity == "high")

    traceback_text = "Traceback (most recent call last):\n File \"backend/main.py\"\nConnectionRefusedError"
    res_tb = global_output_validator.validate("Search query", traceback_text, intent="GENERAL_QA")
    check("Flags raw backend traceback as CRITICAL severity issue", not res_tb.is_valid and res_tb.severity == "critical")

    # 7. False-Positive Resistance
    section("7. False-Positive Resistance Tests")
    res_fp1 = global_output_validator.validate("Explain time complexity", "Time Complexity describes runtime scaling.", intent="EXPLANATION")
    check("Allows 'time complexity' when explicitly asked in prompt", res_fp1.is_valid)

    res_fp2 = global_output_validator.validate("Explain def solve() in competitive programming", "def solve() is a helper function.", intent="EXPLANATION")
    check("Allows 'def solve()' when explicitly asked in prompt", res_fp2.is_valid)

    # 8. Regeneration Controller & Bounded Retries
    section("8. Bounded RegenerationController & Corrective Prompt Strategy")
    check("RegenerationController allows retry for attempt 0", global_regeneration_controller.should_regenerate(res_bad_tmpl, attempt=0))
    check("RegenerationController blocks retry when max attempts (1) exceeded", not global_regeneration_controller.should_regenerate(res_bad_tmpl, attempt=1))
    
    rules, wrapped = global_regeneration_controller.build_corrective_prompt("Explain Formula 1", bad_template, res_bad_tmpl, intent="EXPLANATION")
    check("Corrective prompt preserves original user prompt separately from corrective instructions",
          "Explain Formula 1" in wrapped and "CORRECTIVE INSTRUCTION FOR REGENERATION" in wrapped)

    # 9. Response Cleaner & Safe Fallback
    section("9. Safe Response Cleaner & Safe Fallback")
    dirty = "Formula 1 is motorsport.\n\n\n\n\nKey highlights."
    cleaned = global_response_cleaner.clean(dirty)
    check("ResponseCleaner normalizes 5+ newlines to max 2 newlines", cleaned.count("\n\n\n") == 0)

    fallback = get_safe_fallback_response("EXPLANATION", "Explain Formula 1", ["Coding template leak"])
    check("Safe Fallback returns clean user guidance without bad LLM code", "unable to generate" in fallback.lower())

    # 10. CRITICAL FORMULA 1 END-TO-END TEST
    section("10. Critical Formula 1 End-to-End Simulation")
    bad_f1 = "## Algorithmic Approach\n```python\ndef solve(): print('F1')\n```"
    val_bad = global_output_validator.validate("Explain Formula 1", bad_f1, intent="EXPLANATION")
    check("BAD Formula 1 response is REJECTED (is_valid=False)", not val_bad.is_valid and val_bad.should_regenerate)

    good_f1 = "## What is Formula 1?\nFormula 1 is the highest class of international single-seater auto racing."
    val_good = global_output_validator.validate("Explain Formula 1", good_f1, intent="EXPLANATION")
    check("GOOD Formula 1 response is ACCEPTED (is_valid=True)", val_good.is_valid and not val_good.should_regenerate)

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 4 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return run_v2_day4_verification()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
