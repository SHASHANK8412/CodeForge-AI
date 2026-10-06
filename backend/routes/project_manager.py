import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.project_manager.planner import global_project_planner

logger = logging.getLogger("aiforge.routes.project_manager")

router = APIRouter(tags=["Autonomous Project Management & Sprint Orchestration"])


class CreateProjectPlanRequest(BaseModel):
    prompt: str = Field(min_length=1)


@router.post("/project/create")
@router.post("/api/project/create")
def create_project_plan(req: CreateProjectPlanRequest):
    """Decomposes prompt into Product Manager Analysis, Epics, Stories, Tasks, DAG & Sprints."""
    return global_project_planner.plan_project(req.prompt)


@router.get("/project/{id}")
@router.get("/api/project/{id}")
def get_project_details(id: str):
    """Returns project details for a given project ID."""
    return global_project_planner.plan_project(f"Project {id}")


@router.get("/project/tasks")
@router.get("/api/project/tasks")
def get_project_tasks(prompt: str = "Build Application"):
    """Returns task breakdown for a project."""
    plan = global_project_planner.plan_project(prompt)
    return {"tasks": plan["tasks"]}


@router.get("/project/sprints")
@router.get("/api/project/sprints")
def get_project_sprints(prompt: str = "Build Application"):
    """Returns sprint allocation for a project."""
    plan = global_project_planner.plan_project(prompt)
    return {"sprints": plan["sprints"]}


@router.get("/project/progress")
@router.get("/api/project/progress")
def get_project_progress(prompt: str = "Build Application"):
    """Returns project progress metrics."""
    plan = global_project_planner.plan_project(prompt)
    return plan["progress"]


    return plan["analytics"]


from pathlib import Path
from datetime import datetime
from backend.generators.project_generator import GENERATED_PROJECTS_DIR

# In-memory store for project metadata overrides (renames, duplicates, archives)
PROJECT_METADATA_STORE: dict[str, dict] = {}


def _fmt_time(ts: Optional[float]) -> Optional[str]:
    return datetime.fromtimestamp(ts).strftime("%b %d, %H:%M") if ts else None


def _infer_stack(pdir: Path) -> list:
    """Technologies actually present in the generated files."""
    stack = []
    pkg = pdir / "frontend" / "package.json"
    if pkg.exists():
        text = pkg.read_text(encoding="utf-8", errors="ignore").lower()
        stack += [name for key, name in (('"react"', "React"), ('"vue"', "Vue"), ('"vite"', "Vite"), ("tailwind", "Tailwind CSS")) if key in text]
    elif (pdir / "frontend").is_dir():
        stack.append("Frontend")
    backend_text = " ".join(
        f.read_text(encoding="utf-8", errors="ignore").lower()[:4000]
        for f in list((pdir / "backend").glob("*.py"))[:20] + list((pdir / "backend").glob("requirements*.txt"))
    ) if (pdir / "backend").is_dir() else ""
    for key, name in (("fastapi", "FastAPI"), ("flask", "Flask"), ("django", "Django")):
        if key in backend_text:
            stack.append(name)
    if any(pdir.glob("database/*.sql")) or "sqlalchemy" in backend_text:
        stack.append("SQL")
    return stack


def _project_summary(pdir: Path, generations: list) -> Dict[str, Any]:
    """Everything AIForge actually knows about one generated project; unknown values are None."""
    from backend.quality.version_manager import global_version_manager
    from backend.routes.deployment import DEPLOYMENT_STATE_DB

    gen_id = pdir.name
    meta = PROJECT_METADATA_STORE.get(gen_id, {})
    target = pdir.resolve()
    runs = sorted(
        (r for r in generations if r.get("project_path") and Path(r["project_path"]).resolve() == target),
        key=lambda r: r.get("created_at") or "",
    )
    latest_run = runs[-1] if runs else None
    versions = global_version_manager.get_history(latest_run["project_id"]) if latest_run else []
    latest_ver = versions[-1] if versions else None
    test_result = latest_ver.test_result if latest_ver else {}

    deploy_status = (DEPLOYMENT_STATE_DB.get(gen_id) or {}).get("status")
    if meta.get("status"):
        status = meta["status"]
    elif deploy_status == "LIVE":
        status = "LIVE"
    elif latest_run:
        status = str(latest_run.get("status", "")).upper() or "UNKNOWN"
    else:
        status = "GENERATED"

    return {
        "generation_id": gen_id,
        "project_name": meta.get("name") or pdir.name.replace("_", " "),
        "description": (latest_run or {}).get("prompt") or "",
        "status": status,
        "quality_score": latest_ver.quality_score if latest_ver else None,
        "tests_passed": test_result.get("passed"),
        "tests_total": test_result.get("total"),
        "stack": _infer_stack(pdir),
        "updated_at": _fmt_time(pdir.stat().st_mtime),
        "created_at": (latest_run or {}).get("created_at") or _fmt_time(pdir.stat().st_ctime),
        "is_archived": meta.get("archived", False),
        "_runs": runs,
        "_versions": versions,
    }


def _generated_dirs() -> list:
    if not GENERATED_PROJECTS_DIR.exists():
        return []
    return [p for p in GENERATED_PROJECTS_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")]


def _public(summary: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in summary.items() if not k.startswith("_")}


@router.get("/api/projects")
def list_projects_endpoint(
    page: int = 1,
    page_size: int = 12,
    search: str = "",
    status: str = "all",
    sort: str = "recently_updated"
):
    """
    Lists the projects in generated_projects/ with the status, quality score and test counts
    recorded for them. Values that were never measured are null, not estimated.
    """
    from backend.generation.store import global_generation_store
    generations = global_generation_store.list_all()

    projects_list = []
    for pdir in _generated_dirs():
        proj = _public(_project_summary(pdir, generations))
        if proj["is_archived"] and status.lower() != "archived":
            continue
        if search:
            s_lower = search.lower()
            haystack = [proj["project_name"], proj["description"], proj["status"], *proj["stack"]]
            if not any(s_lower in str(h).lower() for h in haystack):
                continue
        if status != "all":
            if status.lower() == "archived":
                if not proj["is_archived"]:
                    continue
            elif proj["status"].lower() != status.lower():
                continue
        projects_list.append(proj)

    if sort in ("highest_quality", "lowest_quality"):
        scored = [p for p in projects_list if p["quality_score"] is not None]
        unscored = [p for p in projects_list if p["quality_score"] is None]
        scored.sort(key=lambda x: x["quality_score"], reverse=(sort == "highest_quality"))
        projects_list = scored + unscored
    elif sort == "alphabetical":
        projects_list.sort(key=lambda x: x["project_name"].lower())
    else:
        projects_list.sort(key=lambda x: (GENERATED_PROJECTS_DIR / x["generation_id"]).stat().st_mtime, reverse=True)

    total = len(projects_list)
    start_idx = (page - 1) * page_size
    paginated = projects_list[start_idx : start_idx + page_size]

    scores = [p["quality_score"] for p in projects_list if p["quality_score"] is not None]
    tests = [p["tests_passed"] for p in projects_list if p["tests_passed"] is not None]
    deployed_cnt = sum(1 for p in projects_list if p["status"] == "LIVE")
    return {
        "projects": paginated,
        "page": page,
        "page_size": page_size,
        "total": total,
        "stats": {
            "total_projects": total,
            "completed": sum(1 for p in projects_list if p["status"] in ("COMPLETED", "LIVE")),
            "building": sum(1 for p in projects_list if p["status"] in ("QUEUED", "PLANNING", "RUNNING", "WAITING_FOR_APPROVAL")),
            "deployed": deployed_cnt,
            "avg_quality_score": round(sum(scores) / len(scores), 1) if scores else None,
            "total_tests_passed": sum(tests) if tests else None,
            "successful_deployments": deployed_cnt,
        }
    }


@router.get("/api/projects/{generation_id}")
def get_project_details_page(generation_id: str):
    """Project details, its generation activity and recorded versions."""
    from backend.generation.store import global_generation_store
    from backend.routes.project import resolve_generated_project_dir

    pdir = resolve_generated_project_dir(generation_id)
    if not pdir:
        raise HTTPException(status_code=404, detail=f"No generated project found for '{generation_id}'.")
    summary = _project_summary(pdir, global_generation_store.list_all())

    activity = [
        {"timestamp": e.get("timestamp"), "message": e.get("message") or e.get("type")}
        for run in reversed(summary["_runs"]) for e in reversed(run.get("events", []))
    ][:50]
    versions = [
        {
            "version": v.version_id,
            "status": (v.test_result or {}).get("overall_status") or (v.test_result or {}).get("status"),
            "timestamp": _fmt_time(v.created_at),
            "quality_score": v.quality_score,
            "tests": (f"{v.test_result.get('passed')}/{v.test_result.get('total')}"
                      if v.test_result and v.test_result.get("total") else None),
        }
        for v in reversed(summary["_versions"])
    ]
    proj = _public(summary)
    proj["generation_id"] = generation_id
    proj["tests"] = ({"passed": proj["tests_passed"], "total": proj["tests_total"]}
                     if proj["tests_total"] is not None else None)
    proj["activity"] = activity
    proj["versions"] = versions
    return proj


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None


@router.patch("/api/projects/{generation_id}")
def update_project_endpoint(generation_id: str, req: UpdateProjectRequest):
    """Renames or updates project attributes."""
    if generation_id not in PROJECT_METADATA_STORE:
        PROJECT_METADATA_STORE[generation_id] = {}

    if req.name:
        PROJECT_METADATA_STORE[generation_id]["name"] = req.name
    if req.status:
        PROJECT_METADATA_STORE[generation_id]["status"] = req.status

    return {"success": True, "generation_id": generation_id, "updated": PROJECT_METADATA_STORE[generation_id]}


@router.post("/api/projects/{generation_id}/duplicate")
def duplicate_project_endpoint(generation_id: str):
    """Duplicates an existing project into a new project record."""
    new_id = f"{generation_id}-copy"
    old_meta = PROJECT_METADATA_STORE.get(generation_id, {})
    new_name = f"{old_meta.get('name') or 'Project'} v2"

    PROJECT_METADATA_STORE[new_id] = {
        "name": new_name,
        "archived": False
    }

    return {"success": True, "new_generation_id": new_id, "new_name": new_name}


@router.post("/api/projects/{generation_id}/archive")
def archive_project_endpoint(generation_id: str):
    """Archives a project."""
    if generation_id not in PROJECT_METADATA_STORE:
        PROJECT_METADATA_STORE[generation_id] = {}
    PROJECT_METADATA_STORE[generation_id]["archived"] = True
    return {"success": True, "generation_id": generation_id, "archived": True}


@router.delete("/api/projects/{generation_id}")
def delete_project_endpoint(generation_id: str):
    """Permanently deletes a project."""
    if generation_id in PROJECT_METADATA_STORE:
        del PROJECT_METADATA_STORE[generation_id]
    return {"success": True, "generation_id": generation_id, "deleted": True}

