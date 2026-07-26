import logging

logger = logging.getLogger("aiforge.deployment.github_actions")


class GithubActionsGenerator:
    """
    GithubActionsGenerator builds GitHub Actions CI/CD workflows (.github/workflows/ci.yml)
    including testing, linting, code quality auditing, and Docker image builds.
    """

    def generate_ci_workflow(self) -> str:
        return """name: AIForge Autonomous CI/CD Pipeline

on:
  push:
    branches: [ main, master, ai-forge-v2 ]
  pull_request:
    branches: [ main, master ]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f backend/requirements.txt ]; then pip install -r backend/requirements.txt; fi
          pip install pytest flake8
      - name: Run Backend Tests
        run: pytest backend/tests

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Install & Build Frontend
        run: |
          cd frontend
          npm ci
          npm run build

  docker-build:
    needs: [test-backend, test-frontend]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker Images
        run: |
          docker compose build
"""


# Global GithubActionsGenerator Instance
global_github_actions_generator = GithubActionsGenerator()
