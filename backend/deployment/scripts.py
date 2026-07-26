import logging

logger = logging.getLogger("aiforge.deployment.scripts")


class DeploymentScriptGenerator:
    """
    DeploymentScriptGenerator builds executable one-click deployment scripts
    for Linux (deploy.sh) and Windows PowerShell (deploy.ps1).
    """

    def generate_deploy_sh(self) -> str:
        return """#!/usr/bin/env bash
# AIForge Autonomous One-Click Deployment Script (Linux/macOS)
set -e

echo "🚀 Starting AIForge Application Deployment..."

# 1. Verify Docker Installation
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# 2. Build and Launch Containers
echo "📦 Building Docker containers..."
docker compose build

echo "▶️ Launching containers in detached mode..."
docker compose up -d

# 3. Health Check
echo "🔍 Performing Service Health Check..."
sleep 5
docker compose ps

echo "✅ Deployment Successful!"
echo "🌐 Frontend running at: http://localhost"
echo "🔌 Backend API running at: http://localhost:8000"
"""

    def generate_deploy_ps1(self) -> str:
        return """# AIForge Autonomous One-Click Deployment Script (Windows PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting AIForge Application Deployment..." -ForegroundColor Green

# 1. Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Error: Docker Desktop is not installed or running." -ForegroundColor Red
    Exit 1
}

# 2. Build & Launch
Write-Host "📦 Building Docker containers..." -ForegroundColor Cyan
docker compose build

Write-Host "▶️ Launching containers..." -ForegroundColor Cyan
docker compose up -d

# 3. Status
Start-Sleep -Seconds 5
docker compose ps

Write-Host "✅ Deployment Successful!" -ForegroundColor Green
Write-Host "🌐 Frontend running at: http://localhost" -ForegroundColor Yellow
Write-Host "🔌 Backend API running at: http://localhost:8000" -ForegroundColor Yellow
"""


# Global DeploymentScriptGenerator Instance
global_deployment_script_generator = DeploymentScriptGenerator()
