# 📜 AIForge Changelog

All notable changes to the AIForge platform are documented in this file.

## [Unreleased]

### Added
- **Execution Guardian**: stack-aware verification of generated projects in isolated containers, classified failures,
  agent-routed bounded repair, verified repairs delivered as an approval-gated Autopilot plan.
- **Integration & Compatibility Engine**: versioned shared contracts derived from the architecture, deterministic
  frontend/backend/database compatibility analysis, contract tests generated and executed in isolation, contract
  drift detection, bounded repairs routed to the responsible agent.
- **Qwen 3.5 9B is the default local model** (`AIFORGE_LOCAL_MODEL`, `ollama pull qwen3.5:9b`): when installed it
  answers every task, with the older installed models as fallbacks; with a Groq key, Qwen 3.8 27B on Groq answers
  first. Qwen 3.x thinking is off locally (it multiplies CPU time per answer) and any inline thinking is removed
  before an answer reaches the agents.
- **Local Hugging Face models** (`backend/ml/local_models.py`, CPU, loaded on first use from the local cache):
  - a prompt-injection classifier (`protectai/deberta-v3-base-prompt-injection-v2`) alongside the patterns: in the
    8-document eval (local model) attack success with the guard went from 1/8 to 0/8 and useful answers from 7/8 to
    8/8;
  - a cross-encoder reranker (`cross-encoder/ms-marco-MiniLM-L6-v2`) for document search;
  - sentence embeddings (`BAAI/bge-small-en-v1.5`). Until now no embedding model was ever loaded: both embedding
    classes returned hashed-word vectors, so "semantic" search matched words, not meaning. Vectors are now tagged
    with the model that made them and never compared across models;
  - voice prompts: a mic button on the project forms, transcribed on this machine by faster-whisper
    (`POST /api/speech/transcribe`, signed-in users, audio deleted after transcription).
- **Qwen 3.8 27B on Groq** (`qwen/qwen3.8-27b`) is the default hosted model, and by default every task uses it
  (code generation, planning, review, testing, debugging, docs, chat); its thinking is requested hidden so only
  the answer reaches the agents. The local Ollama models remain the fallback. `AIFORGE_GROQ_MODEL` and
  `AIFORGE_GROQ_TASKS` still choose another model or a subset of tasks.
- **Self-healing that knows when a fix didn't work** (merged from the evaluation branch): each debug-loop patch is
  judged on per-test evidence before and after the re-run (fixed / improved / regressed / no effect); regressions
  and no-ops are rolled back on disk, never re-applied, and described to the model on the next attempt; the loop
  stops after `AIFORGE_REPAIR_STALL_LIMIT` (default 2) non-improving attempts. The generated test suite is now
  written once and re-run during repair instead of being regenerated every cycle.
- **Precise repairs**: model repairs (debug loop, Execution Guardian, project editor, Autopilot) ask for search/replace
  edits; an edit must match exactly one place in the file (tolerating trailing whitespace and a uniform indentation
  offset) or it is refused with the reason and retried once. Replies with whole files are still accepted.
- **Repo-aware repair context**: a repair is shown the files the failure involves - traceback files, the files defining
  the symbols named in the error, files the failing module imports, and the failing tests - full or summarised to
  signatures within a budget, instead of only the failing file.
- **Memory of verified fixes**: a repair is remembered only after the re-run checks or the project's tests pass, per
  user (`backend/data/fix_memory.json`); later repairs of a similar error are shown up to three of that user's fixes.
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

### Fixed — app and data
- Every frontend API client sends the sign-in token (chat history, document grounding and other pages answered 401
  after signing in), and the live build progress stream sends it in a header (the `?token=` URL parameter was refused).
- AI Chat agent modes call the local Ollama models; the canned "Synthesized intelligent reasoning" reply, the invented
  sample documents and the model list of hosted models that were never called are gone.
- Chat conversations, canvases, tasks, agent runs, AI-core memories and uploaded documents belong to the user who
  created them; other users get 404.
- The command line runs the real pipeline (it crashed without a checkpoint thread id), asks at the approval
  checkpoints and reports the real failure category.
- The release report is never `ready` unless the generated tests passed and the Execution Guardian verified the
  project.
- Local generated-project test runs time out after 120 s (configurable with `AIFORGE_LOCAL_TEST_TIMEOUT`) instead of
  15 s, which turned slow genuine failures into errors.
- Canvas autosave saves once per pause in typing (it saved a version per keystroke), and changing a canvas's type is
  stored.
- The benchmark test no longer overwrites `benchmarks/REPORT.md` with mocked 100% results; benchmark output is no
  longer committed.

### Removed
- Simulated features that only displayed built-in demo data (no model call, no real work): Mission Control, Deep
  Research, Workflows and the autonomous workflow engine, Cyber Copilot, Sentinel, Browser Agent, the AI OS command
  center, Knowledge Graph / Graph RAG and the Intelligence overview, with their pages and API routes.
- Seeded demo content (food-delivery canvases, tasks, memories and RFC documents) and the fake "AI" buttons of
  Canvas and Tasks.
- About 200 backend modules that nothing in the app imports, and about 260 test files that only tested them or that
  pytest never collected (`backend/tests/`, `tests/verify_*.py`).

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
