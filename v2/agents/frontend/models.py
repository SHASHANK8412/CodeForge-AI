"""
AIForge V2 – Frontend Agent Data Models
=======================================
Data structures for React Components, Pages, Layouts, Routes, Zustand Stores, Custom Hooks, API Services, and Tailwind Configs.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class FrontendComponent(BaseModel):
    name: str
    path: str
    category: str  # UI, Layout, Form, Navigation, Feedback
    code_content: str
    is_reusable: bool = True


class FrontendPage(BaseModel):
    name: str
    route_path: str
    code_content: str
    is_protected: bool = False


class FrontendRoute(BaseModel):
    path: str
    element: str
    layout: str = "DashboardLayout"
    is_protected: bool = True
    is_lazy: bool = True


class FrontendStore(BaseModel):
    store_name: str
    state_keys: List[str]
    code_content: str


class FrontendHook(BaseModel):
    hook_name: str
    purpose: str
    code_content: str


class FrontendService(BaseModel):
    service_name: str
    endpoints_covered: List[str]
    code_content: str


class FrontendReport(BaseModel):
    project_id: str
    project_name: str
    folder_structure: List[str]
    components: List[FrontendComponent]
    pages: List[FrontendPage]
    routes: List[FrontendRoute]
    stores: List[FrontendStore]
    hooks: List[FrontendHook]
    services: List[FrontendService]
    tailwind_config: str
    main_entry: str
    dependencies: List[str] = Field(
        default_factory=lambda: ["react", "react-dom", "react-router-dom", "zustand", "axios", "lucide-react", "tailwindcss"]
    )
    build_status: str = "success"
    confidence_score: float = 97.0
