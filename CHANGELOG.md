# 📜 AIForge Changelog

All notable changes to the AIForge platform are documented in this file.

## [Unreleased]

### Added
- **Execution Guardian**: stack-aware verification of generated projects in isolated containers, classified failures,
  agent-routed bounded repair, verified repairs delivered as an approval-gated Autopilot plan.
- **Integration & Compatibility Engine**: versioned shared contracts derived from the architecture, deterministic
  frontend/backend/database compatibility analysis, contract tests generated and executed in isolation, contract
  drift detection, bounded repairs routed to the responsible agent.
- **CI**: GitHub Actions workflow (backend lint + deterministic test suites, frontend lint + build).

### Security
- Sign-in required by default (`AIFORGE_AUTH_MODE=local-dev` for single-user local development); project ownership
  enforced on project routes; path-traversal and archive/symlink escapes closed; unauthenticated execution endpoints
  retired.

### Fixed — reported results now come only from what actually ran
- A failed or timed-out model call fails its pipeline step; canned placeholder code is no longer shipped as output.
- Quality Center and the production-readiness (CTO) gate are computed from recorded checks (Execution Guardian,
  Integration Engine, project files); anything not evaluated is shown as such. A readiness override is a recorded
  decision and no longer raises scores.
- The reviewer is no longer shown a concrete example to copy; unreadable reviews are "not reviewed"; findings about
  files that do not exist are marked unverified; the review score is computed from verified findings.
- Kubernetes and Terraform: generated manifests and plans are real, but applying them is not implemented, and the
  API now says so instead of reporting LIVE / HEALTHY / applied (no false audit events).
- Verifiable records are described as what they are: a local hash-chained log with HMAC signatures (key no longer in
  the source), not a blockchain.
- Removed invented values from dashboards and analytics (fallback scores, pre-loaded cluster nodes, learning
  accuracy, fixed metric constants) and deleted unused pages that displayed them.

### Corrected
- The v1.0.0 entry below listed "Cyclomatic Complexity 18 → 7" and a "95.6% Overall AI Score". Those figures were
  hardcoded in the UI, not measured, and have been withdrawn.

## [v1.0.0] - 2026-07-24

### Added
- **Multi-Agent Workflow**: specialized agents (Planner, Architect, Frontend, Backend, Database, API, DevOps,
  Testing, Reviewer, Security, Learning, Refactor).
- **Self-Learning Engine**: SQLite long-term project memory, semantic vector similarity search, lessons-learned
  extraction.
- **AI Pair Programmer**: file locator, dependency graph builder, safe backup system, unified diff patch generator.
- **Autonomous Refactoring**: AST code smell detection, print-to-logger replacement, security anti-pattern fixes.
- **Reflection & Quality Scoring**: six-category weighted evaluation.
- **Enterprise Features**: JWT authentication, API keys, plugin marketplace, CI/CD pipelines for generated projects.
