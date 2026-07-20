import logging
from typing import Dict

_logger = logging.getLogger("aiforge.performance")

class GitHubActionsGenerator:
    """
    Generates professional CI/CD pipeline workflows for GitHub Actions (test, lint, deploy)
    along with corresponding status badges for integration into README documents.
    """

    def __init__(self) -> None:
        pass

    def generate_workflows(
        self,
        app_name: str,
        frontend_framework: str = "react",
        backend_framework: str = "fastapi"
    ) -> Dict[str, str]:
        """
        Creates a set of YAML workflow structures for GitHub Actions.
        """
        _logger.info("Generating GitHub Actions workflow pipelines...")

        # 1. Lint Workflow (lint.yml)
        lint_yaml = f"""name: Code Linting

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Install Frontend Dependencies
        run: npm ci

      - name: Lint Frontend
        run: npm run lint --if-present

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Backend Linters
        run: |
          python -m pip install --upgrade pip
          pip install flake8 black

      - name: Lint with black
        run: black --check . --exclude "/(\\.git|\\.venv)/"

      - name: Lint with flake8
        run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
"""

        # 2. Test Workflow (test.yml)
        test_yaml = f"""name: Continuous Integration

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Install Frontend Dependencies
        run: npm ci

      - name: Run Frontend Tests
        run: npm test --if-present

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Backend Dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          pip install pytest

      - name: Run Backend Tests
        run: pytest tests/ --if-present
"""

        # 3. Deploy Workflow (deploy.yml)
        deploy_yaml = f"""name: Continuous Deployment

on:
  push:
    branches: [ main, master ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{GitHub.actor}}
          password: ${{secrets.GITHUB_TOKEN}}

      - name: Build and Push Backend Image
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: ghcr.io/${{GitHub.repository}}/{app_name}-backend:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build and Push Frontend Image
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: ghcr.io/${{GitHub.repository}}/{app_name}-frontend:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
"""

        return {
            ".github/workflows/lint.yml": lint_yaml.strip(),
            ".github/workflows/test.yml": test_yaml.strip(),
            ".github/workflows/deploy.yml": deploy_yaml.strip()
        }

    def generate_badges(self, repo_url: str) -> str:
        """
        Creates markdown status badges for README integration.
        """
        # Strip trailing slashes and normalize repo path
        clean_url = repo_url.rstrip("/")
        if not clean_url:
            clean_url = "https://github.com/aiforge/project"

        return f"""[![CI](https://github.com/aiforge/project/actions/workflows/test.yml/badge.svg)]({clean_url}/actions)
[![Lint](https://github.com/aiforge/project/actions/workflows/lint.yml/badge.svg)]({clean_url}/actions)
[![Deploy](https://github.com/aiforge/project/actions/workflows/deploy.yml/badge.svg)]({clean_url}/actions)"""
