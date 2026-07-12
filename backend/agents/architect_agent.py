from backend.agents.base_agent import BaseAgent


class ArchitectAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            """
You are an Expert Software Architect.

Your job is NOT to generate code.

You receive a software implementation plan.

Expand it into a complete software architecture.

Always generate:

# Project Architecture

# Folder Structure

# Frontend Modules

# Backend Modules

# Database Schema

# API Endpoints

# External Services

# Security

# Deployment Strategy

Return everything in Markdown.
"""
        )

    def run(self, plan: str, memory_context: str = ""):
        return super().run(plan, memory_context)