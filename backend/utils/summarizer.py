def summarize_plan(plan: str) -> str:
    """
    Creates a concise outline of the planner output to keep prompt size minimal.
    """
    if not plan:
        return ""
    lines = plan.splitlines()
    summary = []
    bullet_count = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            summary.append(stripped)
            bullet_count = 0
        elif stripped.startswith(("-", "*", "1.", "2.", "3.", "4.", "5.")):
            if bullet_count < 3:  # limit to top 3 points per section
                summary.append(stripped)
                bullet_count += 1
        elif len(stripped) < 100:  # Include short description lines
            summary.append(stripped)
    return "\n".join(summary)


def summarize_architecture(architecture: str) -> str:
    """
    Summarizes the architecture output.
    """
    if not architecture:
        return "No architecture available."
    lines = architecture.splitlines()
    summary = []
    bullet_count = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            summary.append(stripped)
            bullet_count = 0
        elif stripped.startswith(("-", "*", "1.", "2.", "3.", "4.")):
            if bullet_count < 3:
                summary.append(stripped)
                bullet_count += 1
        elif len(stripped) < 120:
            summary.append(stripped)
    return "\n".join(summary)


def extract_ui_info(plan: str, architecture: str) -> str:
    """
    Extracts only UI/frontend relevant scope from plan and architecture.
    """
    combined = f"{plan}\n{architecture}"
    ui_lines = []
    current_sec = ""
    recording = False
    for line in combined.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            current_sec = stripped.lower()
            recording = any(term in current_sec for term in ["frontend", "ui", "component", "file", "view", "page", "layout", "routing"])
            if recording:
                ui_lines.append(stripped)
        elif recording:
            ui_lines.append(stripped)
        elif any(kw in stripped.lower() for kw in ["react", "jsx", "tailwind", "ui", "css", "html", "view", "page", "route", "frontend"]):
            ui_lines.append(stripped)
    return "\n".join(ui_lines[:100])


def extract_backend_info(plan: str, architecture: str) -> str:
    """
    Extracts only backend/API/database relevant scope from plan and architecture.
    """
    combined = f"{plan}\n{architecture}"
    backend_lines = []
    current_sec = ""
    recording = False
    for line in combined.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            current_sec = stripped.lower()
            recording = any(term in current_sec for term in ["backend", "api", "database", "schema", "route", "server", "model"])
            if recording:
                backend_lines.append(stripped)
        elif recording:
            backend_lines.append(stripped)
        elif any(kw in stripped.lower() for kw in ["fastapi", "python", "sql", "db", "endpoint", "api", "query", "database", "route", "backend"]):
            backend_lines.append(stripped)
    return "\n".join(backend_lines[:100])


def extract_file_list(frontend: str, backend: str, database: str) -> str:
    """
    Parses code blocks to extract generated file paths.
    """
    files = []
    for content in [frontend, backend, database]:
        if not content:
            continue
        for line in content.splitlines():
            if "filename:" in line or "filepath:" in line:
                files.append(line.strip())
    return "\n".join(files) if files else "No files generated yet."
