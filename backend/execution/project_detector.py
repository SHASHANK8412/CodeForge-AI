"""
AIForge Autonomous Engineering Platform — ProjectDetector
==========================================================
Inspects generated project file manifests or disk structures to detect:
- Programming language (JavaScript, Python, Java, Go, Rust)
- Framework (React, Vite, Next.js, Express, Node, FastAPI, Flask, Django, Maven, Gradle)
- Package manager (npm, yarn, pnpm, pip, poetry, maven, gradle)
- Build, test, and start commands
"""

import json
import sys
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.execution.detector")


class DetectedProjectConfig(BaseModel):
    language: str = "javascript"
    framework: str = "react"
    package_manager: str = "npm"
    build_command: str = "npm run build"
    test_command: str = "npm test"
    start_command: str = "npm run dev"
    entry_point: str = "src/App.jsx"
    confidence: float = 1.0
    # Full-stack layout (frontend/ + backend/), used by live preview and local deploys.
    is_fullstack: bool = False
    frontend_framework: Optional[str] = None
    backend_framework: Optional[str] = None
    frontend_command: Optional[str] = None
    backend_command: Optional[str] = None
    health_check_url: str = "/health"


class ProjectDetector:
    """
    Automatic project technology stack and command detector.
    """

    def detect(self, files_manifest: Dict[str, str]) -> DetectedProjectConfig:
        return self._annotate_services(self._detect_primary(files_manifest), files_manifest)

    @staticmethod
    def _annotate_services(cfg: DetectedProjectConfig, files: Dict[str, str]) -> DetectedProjectConfig:
        """Describe the frontend and backend services, including how to start each one.
        {PORT} in a command is replaced with the allocated port."""
        fe_pkg = next((p for p in ("frontend/package.json", "package.json") if p in files), None)
        if fe_pkg:
            try:
                pkg = json.loads(files[fe_pkg] or "{}")
            except ValueError:
                pkg = {}
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            scripts = pkg.get("scripts", {})
            cfg.frontend_framework = next((f for f in ("vite", "next", "react", "vue", "svelte") if f in deps), "node")
            if "dev" in scripts:
                cfg.frontend_command = "npm run dev -- --port {PORT}"
            elif "start" in scripts:
                cfg.frontend_command = "npm start"

        be_main = next((p for p in ("backend/main.py", "main.py") if p in files), None)
        if be_main:
            req = files.get(be_main.replace("main.py", "requirements.txt"), "") + files.get(be_main, "")
            lowered = req.lower()
            cfg.backend_framework = "fastapi" if "fastapi" in lowered else "flask" if "flask" in lowered else "python"
            if cfg.backend_framework == "fastapi":
                cfg.backend_command = f'"{sys.executable}" -m uvicorn main:app --host 127.0.0.1 --port {{PORT}}'

        cfg.is_fullstack = bool(cfg.frontend_framework and cfg.backend_framework)
        return cfg

    def _detect_primary(self, files_manifest: Dict[str, str]) -> DetectedProjectConfig:
        paths = set(files_manifest.keys())

        # 1. JavaScript / TypeScript Projects
        if "package.json" in paths or any(p.endswith((".js", ".jsx", ".ts", ".tsx")) for p in paths):
            pkg_json_content = files_manifest.get("package.json", "{}")
            pkg_data = {}
            try:
                pkg_data = json.loads(pkg_json_content) if pkg_json_content.strip() else {}
            except Exception:
                pass

            scripts = pkg_data.get("scripts", {})
            deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}

            # Detect Framework
            framework = "node"
            if "vite" in deps or "vite.config.js" in paths or "vite.config.ts" in paths:
                framework = "vite"
            elif "next" in deps:
                framework = "nextjs"
            elif "react" in deps or any("App.jsx" in p or "App.tsx" in p for p in paths):
                framework = "react"
            elif "express" in deps:
                framework = "express"

            # Detect Commands
            build_cmd = "npm run build" if "build" in scripts else "npm run build"
            test_cmd = "npm test" if "test" in scripts else "npx vitest run"
            start_cmd = "npm run dev" if ("dev" in scripts or framework in ("vite", "react")) else ("npm start" if "start" in scripts else "node index.js")

            entry = "src/App.jsx"
            if "src/main.jsx" in paths:
                entry = "src/main.jsx"
            elif "src/index.js" in paths:
                entry = "src/index.js"
            elif "index.js" in paths:
                entry = "index.js"

            return DetectedProjectConfig(
                language="typescript" if any(p.endswith((".ts", ".tsx")) for p in paths) else "javascript",
                framework=framework,
                package_manager="npm",
                build_command=build_cmd,
                test_command=test_cmd,
                start_command=start_cmd,
                entry_point=entry,
                confidence=0.95
            )

        # 2. Python Projects
        if any(p.endswith(".py") for p in paths) or "requirements.txt" in paths or "pyproject.toml" in paths:
            framework = "python"
            if any("FastAPI" in c or "fastapi" in c for c in files_manifest.values()):
                framework = "fastapi"
            elif any("Flask" in c or "flask" in c for c in files_manifest.values()):
                framework = "flask"
            elif any("django" in c for c in files_manifest.values()) or "manage.py" in paths:
                framework = "django"

            entry = "backend/main.py" if "backend/main.py" in paths else ("main.py" if "main.py" in paths else "app.py")

            return DetectedProjectConfig(
                language="python",
                framework=framework,
                package_manager="pip",
                build_command="python -m py_compile " + entry,
                test_command="python -m pytest",
                start_command=f"python -m uvicorn {entry.replace('/', '.').replace('.py', '')}:app --host 0.0.0.0 --port 8000",
                entry_point=entry,
                confidence=0.95
            )

        # 3. Java Projects
        if "pom.xml" in paths or "build.gradle" in paths or any(p.endswith(".java") for p in paths):
            is_maven = "pom.xml" in paths
            return DetectedProjectConfig(
                language="java",
                framework="spring-boot" if "pom.xml" in paths else "java",
                package_manager="mvn" if is_maven else "gradle",
                build_command="mvn compile" if is_maven else "gradle build",
                test_command="mvn test" if is_maven else "gradle test",
                start_command="mvn spring-boot:run" if is_maven else "gradle bootRun",
                entry_point="src/main/java/Application.java",
                confidence=0.90
            )

        # Generic Fallback
        return DetectedProjectConfig(
            language="generic",
            framework="generic",
            package_manager="generic",
            build_command="echo build",
            test_command="echo test",
            start_command="echo start",
            entry_point="README.md",
            confidence=0.50
        )


global_project_detector = ProjectDetector()
