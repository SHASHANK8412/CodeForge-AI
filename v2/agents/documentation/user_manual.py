"""
AIForge V2 – User Manual Generator
==================================
Generates USER_MANUAL.md guiding end users step-by-step through UI features.
"""

class UserManualGenerator:

    def generate_user_manual(self, project_name: str) -> str:
        return f"""# User Manual – {project_name}

## 1. Getting Started
1. Open your web browser and navigate to `http://localhost:3000`.
2. On the Sign In page, enter your username and password, then click **Sign In**.

## 2. Navigating the Dashboard
- **Telemetry Cards**: View active projects, overall status, average latency, and critical risk alerts.
- **Sidebar**: Navigate between **Dashboard**, **Resume Upload**, **Projects**, **Settings**, and **Admin**.

## 3. Uploading & Analyzing Resumes
1. Click **Resume Upload** in the navigation sidebar.
2. Drag and drop your PDF resume file or click **Select File**.
3. Click **Analyze Resume** to trigger autonomous AI processing.
"""


global_user_manual = UserManualGenerator()
