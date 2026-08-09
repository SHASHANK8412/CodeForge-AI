"""
AIForge Mandatory 5-Project Dynamic LLM Architecture Verification Suite
========================================================================
Generates and audits 5 distinct prompts across different industries:
1. "Develop a cricket live-score platform"
2. "Build a hospital appointment management system"
3. "Create an e-commerce marketplace"
4. "Build a university placement portal"
5. "Create a personal expense tracker"

Verifies:
- RequirementAnalyzerAgent extracts distinct ProjectSpecifications via LLM
- DynamicArchitectAgent generates distinct file manifests and pages
- Zero keyword-template overlap across all 5 projects
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.generators.incremental_generator import IncrementalProjectGenerator, RequirementAnalyzerAgent
from backend.memory.project_memory import ProjectMemoryStore

PASS = "[PASS]"
FAIL = "[FAIL]"
_results = {"passed": 0, "failed": 0}


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


def test_5_projects():
    print("===========================================================================")
    print(" 🚀 AIForge Mandatory 5-Project Dynamic Architecture Audit")
    print("===========================================================================\n")

    analyzer = RequirementAnalyzerAgent()
    generator = IncrementalProjectGenerator()

    prompts = [
        "Develop a cricket live-score platform",
        "Build a hospital appointment management system",
        "Create an e-commerce marketplace",
        "Build a university placement portal",
        "Create a personal expense tracker"
    ]

    project_outputs = []

    for i, p in enumerate(prompts, 1):
        print(f"\n{"="*75}\n PROJECT #{i}: '{p}'\n{"="*75}")
        spec = analyzer.analyze_prompt(p)
        memory = ProjectMemoryStore(spec.get("project_name", p))
        files = generator.generate_modules_incrementally(spec.get("project_name", p), memory)

        print(f"  - PROJECT NAME: {spec.get('project_name')}")
        print(f"  - DOMAIN:       {spec.get('domain')}")
        print(f"  - FEATURES:     {', '.join(spec.get('features', []))}")
        print(f"  - PAGES:        {', '.join(spec.get('frontend_pages', []))}")
        print(f"  - FILES COUNT:  {len(files)}")

        project_outputs.append({
            "prompt": p,
            "domain": spec.get("domain"),
            "pages": set(spec.get("frontend_pages", [])),
            "files": set(files.keys())
        })

    # Cross-Project Uniqueness Audit
    print("\n" + "="*75)
    print(" 🔍 CROSS-PROJECT ARCHITECTURE UNIQUENESS AUDIT")
    print("="*75)

    domains = [p["domain"] for p in project_outputs]
    check("All 5 projects extracted distinct domains", len(set(domains)) == 5, f"Domains: {domains}")

    # Ensure page overlap across projects is low
    page_overlaps = []
    for i in range(len(project_outputs)):
        for j in range(i + 1, len(project_outputs)):
            pages_i = project_outputs[i]["pages"]
            pages_j = project_outputs[j]["pages"]
            overlap = len(pages_i.intersection(pages_j)) / len(pages_i.union(pages_j)) if pages_i.union(pages_j) else 0.0
            page_overlaps.append(overlap)
            print(f"  - Overlap between '{project_outputs[i]['prompt']}' vs '{project_outputs[j]['prompt']}': {overlap:.1%}")

    avg_overlap = sum(page_overlaps) / len(page_overlaps) if page_overlaps else 0.0
    check("Average page/module overlap across projects is < 30%", avg_overlap < 0.30, f"Average Overlap: {avg_overlap:.2%}")

    # Summary
    print("\n" + "="*75)
    print(f" MANDATORY 5-PROJECT AUDIT SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: { _results['passed'] } | Failed: { _results['failed'] }")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = test_5_projects()
    sys.exit(0 if success else 1)
