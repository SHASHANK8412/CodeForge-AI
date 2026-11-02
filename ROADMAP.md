# 🗺️ AIForge Product Roadmap

Status markers: **[x]** done and verified by tests · **[~]** implemented, partly verified · **[ ]** not done.

## Done
- [x] LangGraph generation pipeline: planner → architect → parallel frontend / backend / database agents → assembly →
      compatibility → review → quality gates → tests → Execution Guardian → approval → export, with human checkpoints
- [x] Execution Guardian: verifies generated projects by running them in isolation (Docker sandbox), classifies
      failures, routes bounded repairs to the responsible agent
- [x] Integration & Compatibility Engine: versioned shared API/data contract, compatibility analysis, generated
      contract tests, drift detection
- [x] Security lockdown: sign-in required by default, project ownership checks, path-traversal protection
- [x] A failed model call fails its pipeline step (no placeholder code is shipped)
- [~] Continuous learning memory (SQLite project memory, knowledge base) — stores data; analytics report only
      recorded values
- [~] AI pair programmer and unified-diff patching (the patch engine is verified through Autopilot and Swarm)
- [~] Plugin marketplace and CI pipeline for generated projects (stages use real exit codes)

## Next
- [ ] Requirement-fidelity check: verify that generated code implements the request
- [ ] Roles / admin scoping for global operations routes; token revocation; login rate limiting
- [ ] Frontend unit tests
- [ ] Real Kubernetes / Terraform integration (today: manifests and plans are generated; nothing is applied)

## Later
- [ ] Real-time WebSocket collaborative canvas
- [ ] VS Code / Cursor extension
- [ ] Helm chart generation
- [ ] Distributed multi-node agent execution (the current Swarm runs on one host)
