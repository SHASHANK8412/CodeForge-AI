"""
AIForge GitHub Actions Workflow Generator
=========================================
Generates project-tailored .github/workflows/aiforge-ci.yml workflows
covering checkout, dependency installation, build, test, lint, and security.
"""

import logging
from typing import Dict, Any, Optional

from backend.execution.project_detector import DetectedProjectConfig, ProjectDetector

_logger = logging.getLogger("aiforge.ci.github_actions")


class GitHubActionsGenerator:
    """
    Generates native GitHub Actions YAML workflows based on project technology stack.
    """

    def __init__(self):
        self.detector = ProjectDetector()

    def generate_workflow(
        self,
        files_manifest: Dict[str, str],
        project_name: str = "AIForge Project",
        detected_cfg: Optional[DetectedProjectConfig] = None
    ) -> str:
        cfg = detected_cfg or self.detector.detect(files_manifest)
        lang = cfg.language.lower()

        if lang == "python":
            return self._generate_python_workflow(project_name, cfg)
        elif lang in ["javascript", "typescript"]:
            return self._generate_node_workflow(project_name, cfg)
        return self._generate_generic_workflow(project_name, cfg)

    def _generate_python_workflow(self, project_name: str, cfg: DetectedProjectConfig) -> str:
        return f"""name: AIForge CI - {project_name}

on:
  push:
    branches: [ main, master, dev ]
  pull_request:
    branches: [ main, master ]

jobs:
  validate:
    name: Build, Test & Security Audit
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python ${{{{ matrix.python-version }}}}
        uses: actions/setup-python@v5
        with:
          python-version: ${{{{ matrix.python-version }}}}
          cache: "pip"

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          pip install pytest ruff bandit

      - name: Build / Syntax Compile
        run: |
          {cfg.build_command}

      - name: Run Test Suite
        run: |
          {cfg.test_command}

      - name: Run Code Lint & Style Checks
        run: |
          ruff check .

      - name: Security & Vulnerability Scan
        run: |
          bandit -r . -x ./tests -ll
"""

    def _generate_node_workflow(self, project_name: str, cfg: DetectedProjectConfig) -> str:
        framework_title = cfg.framework.capitalize()
        return f"""name: AIForge CI - {project_name} ({framework_title})

on:
  push:
    branches: [ main, master, dev ]
  pull_request:
    branches: [ main, master ]

jobs:
  validate:
    name: Build, Test & Lint ({framework_title})
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Node.js 20.x
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: "npm"

      - name: Install Dependencies
        run: |
          npm ci || npm install --no-audit

      - name: Run Build
        run: |
          {cfg.build_command}

      - name: Run Test Suite
        run: |
          {cfg.test_command}

      - name: Run Linting
        run: |
          if npm run | grep -q "lint"; then npm run lint; else echo "No lint script declared"; fi

      - name: Security Audit
        run: |
          npm audit --audit-level=high || true
"""

    def _generate_generic_workflow(self, project_name: str, cfg: DetectedProjectConfig) -> str:
        return f"""name: AIForge CI - {project_name}

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Run Build
        run: |
          {cfg.build_command}

      - name: Run Tests
        run: |
          {cfg.test_command}
"""


global_github_actions_generator = GitHubActionsGenerator()
GitHubActionsWorkflowGenerator = GitHubActionsGenerator
