"""
AIForge Day 17 — AI Browser Test Generator
==========================================
Generates structured end-to-end browser scenarios (Auth, E-Commerce, Task Management,
AIForge Website Self-Test, Responsive Layout) linked to project requirements and Engineering DNA.
"""

import logging
from typing import List, Dict, Any

from backend.browser_testing.models import BrowserScenario, BrowserStep, ViewportPreset

_logger = logging.getLogger("aiforge.browser_testing.generator")


class AIBrowserTestGenerator:
    """
    Generates structured browser scenarios from project requirements and DNA.
    """

    def generate_auth_user_journey(self, project_id: str) -> BrowserScenario:
        return BrowserScenario(
            scenario_id="scen_auth_01",
            name="User Authentication & Session Lifecycle",
            description="Verify login, dashboard access, and logout flow.",
            requirement_id="req_1",
            viewport=ViewportPreset.DESKTOP,
            steps=[
                BrowserStep(action="navigate", url="/login"),
                BrowserStep(action="fill", selector="input[name='email'], [data-testid='email-input'], #email", value="test@example.com"),
                BrowserStep(action="fill", selector="input[name='password'], [data-testid='password-input'], #password", value="test-password"),
                BrowserStep(action="click", selector="button[type='submit'], [data-testid='login-btn']"),
                BrowserStep(action="assert_url", value="/dashboard"),
                BrowserStep(action="assert_visible", selector="[data-testid='user-profile'], header"),
                BrowserStep(action="click", selector="[data-testid='logout-btn'], button:has-text('Logout')"),
                BrowserStep(action="assert_url", value="/login")
            ]
        )

    def generate_task_management_journey(self, project_id: str) -> BrowserScenario:
        return BrowserScenario(
            scenario_id="scen_task_01",
            name="Create, Edit and Delete Task",
            description="Verify user can create, update priority, and delete a task.",
            requirement_id="req_2",
            viewport=ViewportPreset.DESKTOP,
            steps=[
                BrowserStep(action="navigate", url="/dashboard/tasks"),
                BrowserStep(action="click", selector="[data-testid='new-task-btn'], button:has-text('New Task')"),
                BrowserStep(action="fill", selector="input[name='task_name'], [data-testid='task-input']", value="E2E Synthetic Test Task"),
                BrowserStep(action="click", selector="button[type='submit'], [data-testid='save-task-btn']"),
                BrowserStep(action="assert_text", selector="[data-testid='task-list']", value="E2E Synthetic Test Task"),
                BrowserStep(action="click", selector="[data-testid='delete-task-btn']:first-child")
            ]
        )

    def generate_ecommerce_journey(self, project_id: str) -> BrowserScenario:
        return BrowserScenario(
            scenario_id="scen_ecom_01",
            name="Product Catalog & Cart Checkout",
            description="Browse products, add item to cart, and verify order confirmation.",
            requirement_id="req_3",
            viewport=ViewportPreset.DESKTOP,
            steps=[
                BrowserStep(action="navigate", url="/products"),
                BrowserStep(action="fill", selector="input[type='search'], [data-testid='search-input']", value="laptop"),
                BrowserStep(action="click", selector="[data-testid='add-to-cart-btn']:first-child"),
                BrowserStep(action="navigate", url="/cart"),
                BrowserStep(action="click", selector="[data-testid='checkout-btn'], button:has-text('Checkout')"),
                BrowserStep(action="assert_url", value="/order-confirmation")
            ]
        )

    def generate_aiforge_selftest_journey(self) -> BrowserScenario:
        return BrowserScenario(
            scenario_id="scen_aiforge_self",
            name="AIForge IDE & Engineering Dashboard Self-Test",
            description="Navigates AIForge Landing, Code Workspace, DNA Graph, Security Center, Autopilot, and Flight Recorder.",
            requirement_id="req_aiforge",
            viewport=ViewportPreset.DESKTOP,
            steps=[
                BrowserStep(action="navigate", url="/dashboard"),
                BrowserStep(action="navigate", url="/projects/aiforge-demo/dna"),
                BrowserStep(action="assert_visible", selector="header"),
                BrowserStep(action="navigate", url="/security"),
                BrowserStep(action="assert_visible", selector="header"),
                BrowserStep(action="navigate", url="/autopilot"),
                BrowserStep(action="assert_visible", selector="header"),
                BrowserStep(action="navigate", url="/projects/aiforge-demo/debate"),
                BrowserStep(action="assert_visible", selector="header")
            ]
        )

    def generate_responsive_workspace_journey(self, viewport: ViewportPreset = ViewportPreset.LAPTOP) -> BrowserScenario:
        return BrowserScenario(
            scenario_id=f"scen_responsive_{viewport.value}",
            name=f"Code Workspace Viewport Fit ({viewport.value})",
            description=f"Verify no vertical or horizontal page overflow at {viewport.value}.",
            requirement_id="req_responsive",
            viewport=viewport,
            steps=[
                BrowserStep(action="navigate", url="/projects/aiforge-demo/workspace"),
                BrowserStep(action="assert_visible", selector=".main-layout, body")
            ]
        )

    def generate_all_project_scenarios(self, project_id: str) -> List[BrowserScenario]:
        return [
            self.generate_auth_user_journey(project_id),
            self.generate_task_management_journey(project_id),
            self.generate_ecommerce_journey(project_id),
            self.generate_aiforge_selftest_journey(),
            self.generate_responsive_workspace_journey(ViewportPreset.LAPTOP),
            self.generate_responsive_workspace_journey(ViewportPreset.MOBILE)
        ]


global_test_generator = AIBrowserTestGenerator()
