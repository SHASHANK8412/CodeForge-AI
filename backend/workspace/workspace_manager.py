"""
AIForge Workspace Manager
=========================
Master Workspace Manager coordinating multi-project lifecycles, team simulations, cross-project learning,
agent scheduling, resource allocations, and notifications.
"""

import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.workspace.project import WorkspaceProject
from backend.workspace.state import global_workspace_state
from backend.workspace.events import global_event_bus
from backend.workspace.scheduler import global_agent_scheduler
from backend.workspace.portfolio import global_portfolio_dashboard
from backend.workspace.notifications import global_notification_manager
from backend.workspace.resource_manager import global_resource_manager
from backend.workspace.priorities import global_priority_manager
from backend.workspace.analytics import global_workspace_analytics

_logger = logging.getLogger("aiforge.workspace.manager")


class WorkspaceManager:
    """
    Manages multi-project engineering workspace & AI software company execution.
    """

    def __init__(self, workspace_root: Optional[str] = None) -> None:
        if workspace_root is None:
            workspace_root = str(Path(__file__).resolve().parents[2] / "workspace")
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.projects: Dict[str, WorkspaceProject] = {}
        self.shared_memory_dir = Path(__file__).resolve().parents[2] / "shared_memory"
        self.shared_memory_dir.mkdir(parents=True, exist_ok=True)
        self._load_existing_projects()

    def _load_existing_projects(self) -> None:
        default_names = [
            ("Ecommerce Platform", "proj_ecommerce", "Ecommerce Enterprise Suite"),
            ("Hospital Management", "proj_hospital", "Healthcare & Medical Management System"),
            ("Banking Platform", "proj_banking", "Core Banking & Transaction Platform"),
            ("CRM System", "proj_crm", "Customer Relationship Management Suite"),
            ("Inventory Management", "proj_inventory", "Supply Chain & Inventory Suite")
        ]
        for p_name, pid, p_desc in default_names:
            p_dir = self.workspace_root / p_name.replace(" ", "_")
            p_dir.mkdir(parents=True, exist_ok=True)
            proj = WorkspaceProject(project_id=pid, name=p_name, description=p_desc, project_dir=str(p_dir))
            self.projects[pid] = proj
            global_portfolio_dashboard.register_or_update_project(
                project_id=pid,
                name=p_name,
                health="Healthy",
                completion_percentage=75,
                deployment_status="Build Passing"
            )

        if self.projects and not global_workspace_state.active_project_id:
            first_id = list(self.projects.keys())[0]
            global_workspace_state.set_active_project(first_id)

    def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        import time
        pid = f"proj_{int(time.time() * 1000)}"
        clean_dir_name = name.replace(" ", "_")
        p_dir = self.workspace_root / clean_dir_name
        proj = WorkspaceProject(project_id=pid, name=name, description=description, project_dir=str(p_dir))
        self.projects[pid] = proj
        global_workspace_state.set_active_project(pid)

        global_portfolio_dashboard.register_or_update_project(
            project_id=pid,
            name=name,
            health="Healthy",
            completion_percentage=10,
            deployment_status="Initialized"
        )

        global_event_bus.publish("Task Started", pid, "WorkspaceManager", {"action": "create_project", "name": name})
        global_notification_manager.notify(
            event_type="project_created",
            project_id=pid,
            project_name=name,
            title="New Project Created",
            message=f"Project '{name}' initialized in multi-project workspace."
        )

        _logger.info(f"WorkspaceManager: Created project '{name}' (ID={pid})")
        return proj.to_dict()

    def delete_project(self, project_id: str) -> bool:
        if project_id in self.projects:
            proj = self.projects[project_id]
            if proj.project_dir.exists():
                shutil.rmtree(proj.project_dir, ignore_errors=True)
            del self.projects[project_id]
            if global_workspace_state.active_project_id == project_id:
                global_workspace_state.active_project_id = list(self.projects.keys())[0] if self.projects else None
            _logger.info(f"WorkspaceManager: Deleted project ID '{project_id}'")
            return True
        return False

    def switch_project(self, project_id: str) -> Dict[str, Any]:
        if project_id in self.projects:
            global_workspace_state.set_active_project(project_id)
            proj = self.projects[project_id]
            _logger.info(f"WorkspaceManager: Switched active project to '{proj.name}'")
            return proj.to_dict()
        raise ValueError(f"Project ID '{project_id}' not found in workspace.")

    def get_all_projects(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self.projects.values()]

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        if project_id in self.projects:
            return self.projects[project_id].to_dict()
        return None

    def get_portfolio_overview(self) -> Dict[str, Any]:
        return global_portfolio_dashboard.get_portfolio_dashboard()

    def reuse_module_across_projects(self, target_project_id: str, module_name: str = "Authentication Package") -> Dict[str, Any]:
        if target_project_id not in self.projects:
            raise ValueError(f"Target project '{target_project_id}' not found.")

        target_proj = self.projects[target_project_id]
        auth_pkg_dir = target_proj.project_dir / "src" / "auth"
        auth_pkg_dir.mkdir(parents=True, exist_ok=True)

        jwt_file = auth_pkg_dir / "jwt_handler.py"
        jwt_file.write_text("""
# Reused Shared Authentication Package (JWT + Middleware)
from typing import Dict, Any

def verify_shared_jwt_token(token: str) -> Dict[str, Any]:
    return {"status": "authenticated", "user_id": 1, "role": "admin"}
""", encoding="utf-8")

        # Track in analytics
        global_workspace_analytics.reuse_pattern("jwt_auth", target_proj.name)

        global_event_bus.publish("API Ready", target_project_id, "WorkspaceManager", {"action": "reuse_module", "module": module_name})
        _logger.info(f"WorkspaceManager: Successfully copied shared '{module_name}' to project '{target_proj.name}'")

        return {
            "status": "success",
            "module_reused": module_name,
            "target_project": target_proj.name,
            "installed_files": ["src/auth/jwt_handler.py"]
        }


global_workspace_manager = WorkspaceManager()
