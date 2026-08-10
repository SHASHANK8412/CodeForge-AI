"""
AIForge Day 30 — GitHub Integration & Autonomous PR Engineering Test Suite
=============================================================================
Comprehensive unit and integration tests covering:
1. Repository Connection & Project Isolation
2. Branch Creation & Default Branch Protection (main/master protection)
3. Pre-Commit Secret Scanning & Commit Blocking
4. Pull Request Body Generation & GitHub Submission
5. GitHub Actions CI Status Detection & 3-Attempt Repair Loop Limit
6. AI PR Reviewer Decision Audit (APPROVE, REQUEST_CHANGES, COMMENT)
7. Copilot GitHub Commands & ADR PR Generation
8. Security Policy & Permission Enforcement
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.github.repositories import RepositoryAnalyzer
from backend.github.branches import BranchManager, PROTECTED_BRANCH_NAMES
from backend.github.commits import CommitManager, PreCommitSecretScanner, SecurityError
from backend.github.pull_requests import PullRequestGenerator
from backend.github.actions import ActionsCIDetector, CIStatusEnum, MAX_AUTONOMOUS_CI_REPAIR_ATTEMPTS
from backend.github.service import GitHubService, ReviewDecisionEnum
from backend.github.models import RepositoryConnection


@pytest.fixture
def client():
    return TestClient(app)


class TestGitHubPRSuite:

    def test_repository_connection_and_project_isolation(self):
        analyzer = RepositoryAnalyzer()
        conn = analyzer.connect_repository("https://github.com/SHASHANK8412/CodeForge-AI", project_id="proj_alpha")

        assert conn.repo_name == "CodeForge-AI"
        assert conn.owner == "SHASHANK8412"
        assert conn.project_id == "proj_alpha"
        assert conn.token_scrubbed == "[REDACTED_SECRET]"

    def test_branch_creation_and_default_branch_protection(self):
        bm = BranchManager()

        # Creating dedicated feature branch succeeds
        binfo = bm.create_feature_branch("SHASHANK8412/CodeForge-AI", "fix-checkout-api", base_branch="main")
        assert binfo.name == "aiforge/fix-checkout-api"
        assert binfo.is_protected is False

        # Direct modification of default branch raises PermissionError
        with pytest.raises(PermissionError, match="strictly prohibited"):
            bm.create_feature_branch("SHASHANK8412/CodeForge-AI", "main", base_branch="main")

    def test_pre_commit_secret_scanner_blocks_credentials(self):
        cm = CommitManager()

        # Clean commit succeeds
        clean_files = {"backend/api.py": "def checkout(): return True"}
        commit = cm.create_commit("aiforge/feat-checkout", "feat: Update checkout API", clean_files)
        assert commit.sha is not None

        # Secret commit is BLOCKED by Pre-Commit Secret Scanner
        dirty_files = {"backend/config.py": "GITHUB_TOKEN = 'ghp_1234567890abcdef1234567890abcdef1234'"}
        with pytest.raises(SecurityError, match="Commit blocked by Pre-Commit Secret Scanner"):
            cm.create_commit("aiforge/feat-checkout", "feat: Add github token", dirty_files)

    def test_pull_request_creation_and_evidence_template(self):
        pr_gen = PullRequestGenerator()
        pr = pr_gen.create_pull_request(
            full_repo_name="SHASHANK8412/CodeForge-AI",
            title="Fix checkout transaction pool timeout",
            head_branch="aiforge/fix-checkout-timeout",
            problem="Database pool timeout under load",
            root_cause="Missing pool overflow configuration",
            changes=["Updated pool size to 20", "Added timeout retry logic"],
            project_id="proj_alpha"
        )

        assert pr.number == 42
        assert pr.project_id == "proj_alpha"
        assert "52/52 PASS" in pr.body
        assert "Security Gate" in pr.body
        assert "Performance Benchmark" in pr.body

    def test_ci_failure_repair_loop_3_attempt_cap(self):
        detector = ActionsCIDetector()

        # Attempts 1, 2, 3 succeed/repair
        status, notes = detector.execute_ci_failure_repair_loop("SHASHANK8412/CodeForge-AI", pr_number=42, attempt=1)
        assert status == CIStatusEnum.SUCCESS

        # Attempt 4 exceeds max attempts and escalates!
        status_escalated, notes_escalated = detector.execute_ci_failure_repair_loop(
            "SHASHANK8412/CodeForge-AI", pr_number=42, attempt=MAX_AUTONOMOUS_CI_REPAIR_ATTEMPTS + 1
        )
        assert status_escalated == CIStatusEnum.FAILURE
        assert "ESCALATED" in notes_escalated

    def test_ai_pr_reviewer(self):
        service = GitHubService()

        # Safe code diff -> APPROVE
        safe_diff = "+ def calculate_total(items):\n+     return sum(items)"
        review_safe = service.review_pull_request("SHASHANK8412/CodeForge-AI", pr_number=42, diff_text=safe_diff)
        assert review_safe.decision == ReviewDecisionEnum.APPROVE

        # Unsafe code diff (eval injection) -> REQUEST_CHANGES
        unsafe_diff = "+ def execute_raw(cmd):\n+     eval(cmd)"
        review_unsafe = service.review_pull_request("SHASHANK8412/CodeForge-AI", pr_number=42, diff_text=unsafe_diff)
        assert review_unsafe.decision == ReviewDecisionEnum.REQUEST_CHANGES
        assert review_unsafe.security == "FAIL"

    def test_copilot_github_integration_and_adr(self):
        service = GitHubService()

        copilot_res = service.handle_copilot_github_query("proj_alpha", "Why did CI fail?")
        assert "CI failed due to a database connection timeout" in copilot_res["answer"]

        # ADR generation
        adr_res = service.generate_adr_and_pr(
            project_id="proj_alpha",
            adr_number=12,
            title="PostgreSQL + pgvector Vector Storage",
            decision_text="We choose PostgreSQL + pgvector for unified relational and vector storage."
        )
        assert adr_res["adr_filepath"] == "docs/adr/ADR-012.md"
        assert adr_res["pr"]["number"] == 42

    def test_github_overview_api_endpoint(self, client):
        res = client.get("/api/github/overview?project_id=aiforge-demo")
        assert res.status_code == 200
        data = res.json()
        assert data["connected_repository"] == "SHASHANK8412/CodeForge-AI"
        assert data["active_branch"] == "aiforge/fix-checkout-timeout"
        assert len(data["open_prs"]) >= 1
        assert data["ci_overall_status"] == "SUCCESS"
