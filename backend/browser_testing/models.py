"""
AIForge Day 17 — Autonomous Browser Testing Pydantic Data Models
==================================================================
Models for Browser Steps, Scenarios, Results, Accessibility Findings,
Visual Regression Diffs, Viewport Dimensions, and Reports.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ViewportPreset(str, Enum):
    DESKTOP = "1920x1080"
    LAPTOP = "1366x768"
    TABLET = "768x1024"
    MOBILE = "390x844"


class ViewportSize(BaseModel):
    width: int = 1920
    height: int = 1080
    preset_name: str = "Desktop"


class BrowserStep(BaseModel):
    action: str  # navigate, fill, click, select, assert_url, assert_text, assert_visible, wait
    url: Optional[str] = None
    selector: Optional[str] = None
    value: Optional[str] = None
    timeout_ms: int = 5000


class BrowserScenario(BaseModel):
    scenario_id: str
    name: str
    description: str
    requirement_id: Optional[str] = None
    steps: List[BrowserStep] = Field(default_factory=list)
    viewport: ViewportPreset = ViewportPreset.DESKTOP


class AccessibilityFinding(BaseModel):
    id: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    rule: str
    description: str
    target_selector: str
    recommendation: str


class VisualRegressionResult(BaseModel):
    page_name: str
    baseline_screenshot: str
    current_screenshot: str
    diff_screenshot: Optional[str] = None
    mismatch_percent: float = 0.0
    passed: bool = True


class BrowserTestResult(BaseModel):
    scenario_id: str
    scenario_name: str
    requirement_id: Optional[str] = None
    status: str  # PASS, FAIL, ERROR, SKIPPED
    duration_seconds: float = 0.0
    failed_step_index: Optional[int] = None
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    trace_path: Optional[str] = None
    current_url: Optional[str] = None
    console_errors: List[str] = Field(default_factory=list)
    network_errors: List[Dict[str, Any]] = Field(default_factory=list)
    affected_file: Optional[str] = None


class BrowserTestReport(BaseModel):
    project_id: str
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    duration_seconds: float = 0.0
    browser_type: str = "Chromium (Headless Docker)"
    scenarios_results: List[BrowserTestResult] = Field(default_factory=list)
    accessibility_findings: List[AccessibilityFinding] = Field(default_factory=list)
    visual_regression_results: List[VisualRegressionResult] = Field(default_factory=list)
    created_at: str = ""
