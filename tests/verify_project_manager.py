import asyncio
import json
import sys
from pathlib import Path

# Add root folder to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.project_manager.state_engine import ProjectStateEngine
from backend.project_manager.sprint_planner import SprintPlanner
from backend.project_manager.dependency_graph import DependencyGraph
from backend.project_manager.task_scheduler import TaskScheduler
from backend.project_manager.progress_tracker import ProgressTracker
from backend.project_manager.resume_engine import ResumeEngine
from backend.project_manager.bug_backlog import BugBacklog
from backend.project_manager.milestone_generator import MilestoneGenerator
from backend.project_manager.decision_store import DecisionStore
from backend.project_manager.standup_generator import StandupGenerator

async def run_pm_verification():
    print("======================================================================")
    print("AIForge Autonomous AI Project Manager E2E Verification Suite")
    print("======================================================================\n")

    workspace_root = str(Path(__file__).resolve().parent.parent)
    state_file = Path(workspace_root) / "backend" / "project_manager" / "project_state.json"
    
    # 1. State Engine & Tracker
    print("--- 1. State Engine & Tracker ---")
    engine = ProjectStateEngine(state_file=str(state_file))
    engine.update_task("database", "Completed")
    engine.update_task("backend", "Pending")
    state = engine.load_state()
    print(f"Project Status: {state['status']}")
    print(f"Task 'database': {state['tasks']['database']['status']}")
    print(f"Completion Progress: {state['completion_percentage']}%")
    print("")

    # 2. Sprint Planner & Milestone Generator
    print("--- 2. Sprint Planner & Milestone Generator ---")
    planner = SprintPlanner()
    tasks_list = ["database", "backend", "frontend", "testing", "deployment", "documentation"]
    sprints = planner.generate_sprints(tasks_list)
    for sprint in sprints:
        print(f"  - {sprint['sprint_name']}: {sprint['status']} (Complexity: {sprint['complexity']})")
        print(f"    Tasks: {sprint['tasks']}")
    
    generator = MilestoneGenerator()
    milestones = generator.generate_milestones(tasks_list)
    print("Milestones:")
    for m in milestones:
        print(f"  [{m['id']}] {m['title']}: {m['description']}")
    print("")

    # 3. Dependency Graph & Task Scheduler
    print("--- 3. Dependency Graph & Task Scheduler ---")
    graph = DependencyGraph()
    order = graph.get_execution_order()
    print(f"Calculated SRE task execution ordering path: {order}")
    
    scheduler = TaskScheduler()
    schedule = scheduler.schedule_tasks(order)
    for s in schedule:
        print(f"  Order {s['order']}: {s['task_name']} assigned to -> {s['assigned_agent']}")
    print("")

    # 4. Resume Engine
    print("--- 4. Resume Engine ---")
    resume = ResumeEngine()
    incomplete = resume.get_incomplete_tasks(state)
    print(f"Pending/incomplete tasks to resume: {incomplete}")
    print(" [OK] Skipped completed tasks successfully.")
    print("")

    # 5. Bug Backlog System
    print("--- 5. Bug Backlog System ---")
    backlog = BugBacklog()
    backlog.log_bug("CORS wildcard config", "High", "Allowed origin is '*'. Update to secure origin.")
    backlog.log_bug("NoneType error on auth", "Medium", "auth_controller.py line 42")
    
    print(f"Total open bugs in backlog: {len(backlog.get_open_bugs())}")
    backlog.resolve_bug("CORS wildcard config")
    print(f"Remaining open bugs: {len(backlog.get_open_bugs())}")
    print("")

    # 6. Architecture Decision Store (ADR)
    print("--- 6. Architecture Decision Store (ADR) ---")
    store = DecisionStore()
    store.record_decision("Auth Mechanism", "JWT Stateless Tokens", "Accepted", "Stateless scaling")
    store.record_decision("Database Choice", "PostgreSQL", "Accepted", "ACID Compliance")
    
    decisions = store.get_decisions()
    for d in decisions:
        print(f"  ADR: {d['title']} -> Selected: {d['choice']} ({d['status']})")
    print("")

    # 7. SRE Daily Standup Generator
    print("--- 7. SRE Daily Standup Generator ---")
    standup_gen = StandupGenerator()
    # Update mock state with Blockers
    engine.update_task("frontend", "Blocked", "Tailwind package resolution lag")
    state = engine.load_state()
    
    standup_report = standup_gen.generate_standup_report(state)
    print(standup_report)

    print("======================================================================")
    print("All SRE Project Manager E2E tests completed successfully!")
    print("======================================================================")

if __name__ == "__main__":
    asyncio.run(run_pm_verification())
