import logging
from typing import Dict, List, Any

from backend.agents.base_agent import BaseAgent
from backend.services.deployment.docker_generator import DockerGenerator
from backend.services.deployment.compose_generator import ComposeGenerator
from backend.services.deployment.render_generator import RenderGenerator
from backend.services.deployment.railway_generator import RailwayGenerator
from backend.services.deployment.vercel_generator import VercelGenerator
from backend.services.deployment.netlify_generator import NetlifyGenerator
from backend.services.deployment.fly_generator import FlyGenerator
from backend.services.deployment.huggingface_generator import HuggingFaceGenerator
from backend.services.deployment.github_actions import GitHubActionsGenerator
from backend.services.deployment.env_detector import EnvDetector
from backend.services.deployment.validator import DeploymentValidator
from backend.services.deployment.bundle_exporter import BundleExporter

_logger = logging.getLogger("aiforge.performance")

class DeploymentAgent(BaseAgent):
    """
    Analyzes generated projects, auto-detects frameworks/databases,
    creates Docker and platform configurations, runs validation diagnostics,
    and packages deployment bundles.
    """

    def __init__(self) -> None:
        super().__init__(
            system_prompt="""
You are an expert DevOps Engineer and Cloud Architect.
Your task is to analyze generated codebases and output the correct, production-ready
Dockerfile, docker-compose, and cloud configuration files.
            """,
            task_name="deployment"
        )
        self.docker_gen = DockerGenerator()
        self.compose_gen = ComposeGenerator()
        self.render_gen = RenderGenerator()
        self.railway_gen = RailwayGenerator()
        self.vercel_gen = VercelGenerator()
        self.netlify_gen = NetlifyGenerator()
        self.fly_gen = FlyGenerator()
        self.hf_gen = HuggingFaceGenerator()
        self.gh_actions = GitHubActionsGenerator()
        self.env_detector = EnvDetector()
        self.validator = DeploymentValidator()
        self.exporter = BundleExporter()

    def detect_stack(self, state: Dict[str, Any]) -> tuple[Dict[str, str], List[str]]:
        """
        Auto-detects backend/frontend frameworks and database options based on state code.
        """
        frontend_code = state.get("frontend", "")
        backend_code = state.get("backend", "")
        database_code = state.get("database", "")

        frameworks = {"frontend": "react", "backend": "fastapi"}
        databases: List[str] = []

        # 1. Frontend Detections
        if "next" in frontend_code.lower() or "next/router" in frontend_code.lower():
            frameworks["frontend"] = "next.js"
        elif "vue" in frontend_code.lower():
            frameworks["frontend"] = "vue"
        elif "angular" in frontend_code.lower():
            frameworks["frontend"] = "angular"

        # 2. Backend Detections
        if "django" in backend_code.lower():
            frameworks["backend"] = "django"
        elif "flask" in backend_code.lower():
            frameworks["backend"] = "flask"
        elif "express" in backend_code.lower():
            frameworks["backend"] = "express"
        elif "spring" in backend_code.lower():
            frameworks["backend"] = "spring boot"

        # 3. Database Detections
        db_check_str = f"{backend_code.lower()} {database_code.lower()}"
        if "postgres" in db_check_str or "postgresql" in db_check_str:
            databases.append("postgres")
        if "mongo" in db_check_str or "mongodb" in db_check_str:
            databases.append("mongodb")
        if "mysql" in db_check_str:
            databases.append("mysql")
        if "redis" in db_check_str:
            databases.append("redis")
        if "sqlite" in db_check_str:
            databases.append("sqlite")

        if not databases:
            databases.append("sqlite")  # default fallback

        return frameworks, databases

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes deployment asset generation and validation.
        """
        _logger.info("Executing DeploymentAgent generation pipeline...")
        project_name = state.get("prompt") or state.get("user_prompt", "aiforge-project")
        
        # 1. Stack detection
        frameworks, databases = self.detect_stack(state)
        
        # 2. Ports mapping setup
        frontend_port = 80
        backend_port = 8000
        if frameworks["frontend"] == "next.js":
            frontend_port = 3000

        # 3. Generate deployment files
        deployment_files: Dict[str, str] = {}

        # Dockerfile structures
        deployment_files["frontend/Dockerfile"] = self.docker_gen.generate_frontend_dockerfile(
            framework=frameworks["frontend"], port=frontend_port
        )
        deployment_files["backend/Dockerfile"] = self.docker_gen.generate_backend_dockerfile(
            framework=frameworks["backend"], port=backend_port
        )
        deployment_files["docker-compose.yml"] = self.compose_gen.generate_compose(
            databases=databases,
            frontend_framework=frameworks["frontend"],
            backend_framework=frameworks["backend"],
            frontend_port=frontend_port,
            backend_port=backend_port
        )
        deployment_files[".dockerignore"] = self.docker_gen.generate_dockerignore()

        # Cloud configs
        deployment_files["render.yaml"] = self.render_gen.generate_config(
            app_name=project_name,
            databases=databases,
            backend_framework=frameworks["backend"],
            backend_port=backend_port
        )
        deployment_files["railway.toml"] = self.railway_gen.generate_config(
            framework=frameworks["backend"], port=backend_port
        )
        deployment_files["vercel.json"] = self.vercel_gen.generate_config(
            app_name=project_name, has_backend=bool(frameworks["backend"])
        )
        deployment_files["netlify.toml"] = self.netlify_gen.generate_config(
            framework=frameworks["frontend"]
        )
        deployment_files["fly.toml"] = self.fly_gen.generate_config(
            app_name=project_name, port=backend_port
        )
        deployment_files["huggingface.yml"] = self.hf_gen.generate_config(
            app_name=project_name, port=backend_port
        )

        # Environmental scanner
        combined_code = f"{state.get('frontend', '')}\n{state.get('backend', '')}\n{state.get('database', '')}"
        env_vars = self.env_detector.detect_variables(combined_code)
        deployment_files[".env.example"] = self.env_detector.generate_env_example(env_vars)

        # CI/CD Workflows
        workflows = self.gh_actions.generate_workflows(
            app_name=project_name,
            frontend_framework=frameworks["frontend"],
            backend_framework=frameworks["backend"]
        )
        deployment_files.update(workflows)

        # 4. Validation Readiness Diagnostic
        report = self.validator.validate(
            project_name=project_name,
            state=state,
            deployment_files=deployment_files,
            env_vars=env_vars,
            frameworks=frameworks,
            databases=databases
        )

        # 5. Generate guide
        guide_content = self.exporter.generate_deployment_guide(
            app_name=project_name,
            platform=report.suggested_platform,
            reasoning=report.reasoning,
            port=backend_port
        )

        # Save to state
        state["deployment_files"] = deployment_files
        state["deployment_report"] = report.to_dict()
        state["deployment_platform"] = report.suggested_platform
        state["deployment_guide"] = guide_content

        # Append deployment guide to documentation state
        docs_prefix = f"# Deployment Specifications\nRefer to `docs/DEPLOYMENT.md` for continuous cloud setups.\n\n"
        state["documentation"] = state.get("documentation", "") + "\n\n" + docs_prefix + guide_content

        _logger.info("DeploymentAgent successfully executed and compiled reports")
        return state

    async def run_async(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asynchronous wrapper around synchronous DevOps generators (no external awaits needed).
        """
        return self.run(state)
