import logging

_logger = logging.getLogger("aiforge.performance")


class GitIgnoreGenerator:
    """
    Programmatically generates a comprehensive .gitignore file for full-stack projects,
    covering Python, Node.js, Vite, FastAPI, IDE settings, and OS caches.
    """

    def __init__(self) -> None:
        pass

    def generate_gitignore(self) -> str:
        """
        Compiles the .gitignore file layout content.
        """
        _logger.info("Generating .gitignore template...")
        content = """# ==============================================================================
# AIForge Generated .gitignore Configuration
# ==============================================================================

# Python Caches & Compiled files
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Python Virtual Environments
.venv/
venv/
ENV/
env/
ENV/local/
ENV/bin/

# Node.js/Vite/Frontend builds
node_modules/
jspm_packages/
web_drivers/
.npm
.eslintcache
.stylelintcache
.rpt2_cache/
.rts2_cache_defs/
.rts2_cache_src/
.tsbuildinfo
dist/
dist-ssr/
*.local
.vite/

# Caches and Diagnostic reports
.pytest_cache/
.tox/
.nox/
.coverage
.coverage.*
.cache
htmlcov/
nosetests.xml
coverage.xml
*.cover
*.log
.hypothesis/
.dmypy.json
dmypy.json

# Environment Secrets
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
*.env

# IDE / Editor configurations
.vscode/
!.vscode/extensions.json
.idea/
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?

# OS / File System metadata
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
"""
        _logger.info(".gitignore generated successfully")
        return content
