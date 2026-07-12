from __future__ import annotations

import sys
from pathlib import Path


backend_dir = Path(__file__).resolve().parent
repo_root = backend_dir.parent

if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))