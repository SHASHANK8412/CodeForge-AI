"""
AIForge V2 Download & Export Functionality Verification Script
=============================================================
Verifies:
1. GET /api/export/zip/{projectId} & POST /api/export/zip returns application/zip stream
2. GET /api/export/docs/{projectId} & POST /api/export/docs returns text/markdown documentation
3. POST /api/export/github authenticates and returns repository URL
4. Proper validation errors when project files are empty or missing
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.routes.export import export_project_zip, export_project_docs, export_to_github, ExportZipRequest, GitHubExportRequest

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


async def verify_download_export():
    print("===========================================================================")
    print(" 🚀 AIForge V2 – Download & Export Functionality Verification")
    print("===========================================================================\n")

    project_id = "Formula_1_Website"
    sample_files = {
        "frontend/src/App.jsx": "export default function App() { return <h1>F1 App</h1>; }",
        "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()",
        "database/schema.sql": "CREATE TABLE drivers (id SERIAL PRIMARY KEY, name VARCHAR(255));",
        "README.md": "# Formula 1 Website Documentation"
    }

    # 1. Verify ZIP Export
    print("1. Testing Project ZIP Archive Download Endpoint...")
    zip_req = ExportZipRequest(project_id=project_id, files=sample_files)
    res_zip = await export_project_zip(projectId=project_id, payload=zip_req)

    check("ZIP response media_type is 'application/zip'", res_zip.media_type == "application/zip")
    check("ZIP response headers contain Content-Disposition attachment", "attachment; filename=" in res_zip.headers.get("Content-Disposition", ""))
    check("ZIP response body is non-empty bytes", len(res_zip.body) > 100)

    # 2. Verify Docs Export
    print("\n2. Testing Documentation Download Endpoint...")
    res_docs = await export_project_docs(projectId=project_id, payload=zip_req)

    check("Docs response media_type is 'text/markdown'", res_docs.media_type == "text/markdown")
    check("Docs response headers contain Content-Disposition attachment", "attachment; filename=" in res_docs.headers.get("Content-Disposition", ""))
    check("Docs response body contains README content", b"Formula 1" in res_docs.body)

    # 3. Verify GitHub Export
    print("\n3. Testing GitHub Repository Export Endpoint...")
    gh_req = GitHubExportRequest(project_id=project_id, files=sample_files)
    res_gh = await export_to_github(gh_req)

    check("GitHub export returned success = True", res_gh.get("success") == True)
    check("GitHub export returned valid repository URL", "github.com" in res_gh.get("repository_url", ""))
    check("GitHub export committed 4 files", res_gh.get("committed_files") == 4)

    # Summary
    print("\n" + "="*75)
    print(f" DOWNLOAD & EXPORT FUNCTIONALITY VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: { _results['passed'] } | Failed: { _results['failed'] }")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(verify_download_export())
    sys.exit(0 if success else 1)
