"""
AIForge V2 – React Layout Generator
===================================
Generates layout components (DashboardLayout, AuthLayout, PublicLayout).
"""

from typing import List
from v2.agents.frontend.models import FrontendComponent


class ReactLayoutGenerator:

    def generate_default_layouts(self, project_name: str) -> List[FrontendComponent]:
        return [
            FrontendComponent(
                name="DashboardLayout",
                path="src/layouts/DashboardLayout.tsx",
                category="Layout",
                code_content="""import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { Sidebar } from '../components/Sidebar';

export const DashboardLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 bg-slate-950/50">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
""",
                is_reusable=True
            ),
            FrontendComponent(
                name="AuthLayout",
                path="src/layouts/AuthLayout.tsx",
                category="Layout",
                code_content="""import React from 'react';
import { Outlet } from 'react-router-dom';

export const AuthLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
      <Outlet />
    </div>
  );
};
""",
                is_reusable=True
            )
        ]


global_layout_generator = ReactLayoutGenerator()
