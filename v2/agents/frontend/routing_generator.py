"""
AIForge V2 – React Router Generator
====================================
Generates React Router 6 route declarations and ProtectedRoute guards.
"""

from typing import List
from v2.agents.frontend.models import FrontendRoute, FrontendComponent


class ReactRoutingGenerator:

    def generate_routes(self) -> List[FrontendRoute]:
        return [
            FrontendRoute(path="/login", element="Login", layout="AuthLayout", is_protected=False, is_lazy=False),
            FrontendRoute(path="/dashboard", element="Dashboard", layout="DashboardLayout", is_protected=True, is_lazy=True),
            FrontendRoute(path="/upload", element="ResumeUpload", layout="DashboardLayout", is_protected=True, is_lazy=True),
            FrontendRoute(path="/projects", element="Dashboard", layout="DashboardLayout", is_protected=True, is_lazy=True),
            FrontendRoute(path="/settings", element="Dashboard", layout="DashboardLayout", is_protected=True, is_lazy=True)
        ]

    def generate_router_component(self) -> FrontendComponent:
        return FrontendComponent(
            name="AppRouter",
            path="src/routes/AppRouter.tsx",
            category="Navigation",
            code_content="""import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { AuthLayout } from '../layouts/AuthLayout';
import { Dashboard } from '../pages/Dashboard';
import { ResumeUpload } from '../pages/ResumeUpload';
import { Login } from '../pages/Login';
import { useAuthStore } from '../stores/useAuthStore';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

export const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<Login />} />
        </Route>

        <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/upload" element={<ResumeUpload />} />
          <Route path="/projects" element={<Dashboard />} />
          <Route path="/settings" element={<Dashboard />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
};
""",
            is_reusable=True
        )


global_routing_generator = ReactRoutingGenerator()
