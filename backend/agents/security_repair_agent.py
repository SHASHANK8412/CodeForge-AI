"""
AIForge Autonomous Engineering Platform — SecurityRepairAgent
================================================================
Performs targeted, deterministic repairs for security vulnerabilities:
- Hardcoded Secret Remediation (Extract to .env and .env.example, add to .gitignore)
- Permissive CORS wildcard fix (allow_origins=["*"] -> explicit origin list)
- Debug mode remediation (debug=True -> debug=False)
- Subprocess shell=True remediation
- Missing .gitignore generation
"""

import re
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from backend.security.security_scanners import SecurityFinding

_logger = logging.getLogger("aiforge.agents.security_repair")


class SecurityFixResult(BaseModel):
    status: str = "repaired"  # "repaired", "partially_repaired", "no_fixes_applied"
    repaired_findings: List[str] = Field(default_factory=list)
    modified_files: List[str] = Field(default_factory=list)
    env_example_created: bool = False
    gitignore_updated: bool = False


class SecurityRepairAgent:
    """
    Dedicated Security Repair Agent for targeted vulnerability remediation.
    """

    def fix_security_issues(
        self,
        findings: List[SecurityFinding],
        files_manifest: Dict[str, str]
    ) -> SecurityFixResult:
        repaired_ids: List[str] = []
        modified: set[str] = set()
        env_vars_extracted: Dict[str, str] = {}

        for f in findings:
            if not f.auto_fixable:
                continue

            rel_path = f.file
            content = files_manifest.get(rel_path, "")

            # 1. Hardcoded Secret Remediation
            if f.category == "hardcoded_secret":
                match = re.search(r"(api_key|secret_key|jwt_secret)\s*[:=]\s*['\"]([^'\"]+)['\"]", content, re.IGNORECASE)
                if match:
                    var_name = match.group(1).upper()
                    secret_val = match.group(2)
                    env_vars_extracted[var_name] = secret_val

                    # Replace in content with os.getenv
                    new_content = content.replace(
                        match.group(0),
                        f'{match.group(1)} = os.getenv("{var_name}", "{secret_val[:3]}****")'
                    )

                    # Ensure import os is present
                    if "import os" not in new_content and rel_path.endswith(".py"):
                        new_content = f"import os\n{new_content}"

                    files_manifest[rel_path] = new_content
                    modified.add(rel_path)
                    repaired_ids.append(f.id)

            # 2. Permissive CORS Remediation
            elif "allow_origins=['*']" in content or 'allow_origins=["*"]' in content:
                new_content = content.replace(
                    "allow_origins=['*']",
                    "allow_origins=['http://localhost:5173', 'http://localhost:3000']"
                ).replace(
                    'allow_origins=["*"]',
                    'allow_origins=["http://localhost:5173", "http://localhost:3000"]'
                )
                files_manifest[rel_path] = new_content
                modified.add(rel_path)
                repaired_ids.append(f.id)

            # 3. Debug Mode Remediation
            elif "debug=True" in content:
                new_content = content.replace("debug=True", "debug=False")
                files_manifest[rel_path] = new_content
                modified.add(rel_path)
                repaired_ids.append(f.id)

            # 4. Unsafe Subprocess Shell=True Remediation
            elif "shell=True" in content:
                new_content = content.replace("shell=True", "shell=False")
                files_manifest[rel_path] = new_content
                modified.add(rel_path)
                repaired_ids.append(f.id)

        # 5. Generate / Update .env.example
        env_created = False
        if env_vars_extracted or ".env.example" not in files_manifest:
            example_lines = [f"{var}=your_{var.lower()}_here" for var in env_vars_extracted.keys()]
            if not example_lines:
                example_lines = ["PORT=8000", "API_KEY=your_api_key_here"]
            files_manifest[".env.example"] = "\n".join(example_lines) + "\n"
            modified.add(".env.example")
            env_created = True

        # 6. Ensure .gitignore has .env
        gitignore_updated = False
        git_content = files_manifest.get(".gitignore", "")
        if ".env" not in git_content:
            new_git = git_content + "\n.env\n.env.*\n*.pem\n*.key\nnode_modules/\n__pycache__/\n"
            files_manifest[".gitignore"] = new_git.strip() + "\n"
            modified.add(".gitignore")
            gitignore_updated = True

        status = "repaired" if repaired_ids else ("partially_repaired" if env_created or gitignore_updated else "no_fixes_applied")

        return SecurityFixResult(
            status=status,
            repaired_findings=repaired_ids,
            modified_files=list(modified),
            env_example_created=env_created,
            gitignore_updated=gitignore_updated
        )


global_security_repair_agent = SecurityRepairAgent()
