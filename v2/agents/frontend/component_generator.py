"""
AIForge V2 – React UI Component Generator
=========================================
Generates modular, styled React + TypeScript UI components (Navbar, Sidebar, Button, Card, Modal, Loader, Toast, Table).
"""

from typing import List
from v2.agents.frontend.models import FrontendComponent


class ReactComponentGenerator:

    def generate_default_components(self, project_name: str) -> List[FrontendComponent]:
        return [
            FrontendComponent(
                name="Navbar",
                path="src/components/Navbar.tsx",
                category="Navigation",
                code_content="""import React from 'react';
import { useAuthStore } from '../stores/useAuthStore';
import { LogOut, User, Bell } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuthStore();
  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center gap-3">
        <span className="font-bold text-xl bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
          AIForge App
        </span>
      </div>
      <div className="flex items-center gap-4">
        <button className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition">
          <Bell className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-3 pl-4 border-l border-slate-800">
          <div className="w-9 h-9 rounded-full bg-blue-600/20 text-blue-400 flex items-center justify-center font-medium">
            {user?.name?.[0] || 'U'}
          </div>
          <span className="text-sm font-medium text-slate-200">{user?.name || 'User'}</span>
          <button onClick={logout} className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition" title="Logout">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
""",
                is_reusable=True
            ),
            FrontendComponent(
                name="Sidebar",
                path="src/components/Sidebar.tsx",
                category="Navigation",
                code_content="""import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FileText, Layers, Settings, ShieldCheck } from 'lucide-react';

const navItems = [
  { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { label: 'Resume Upload', path: '/upload', icon: FileText },
  { label: 'Projects', path: '/projects', icon: Layers },
  { label: 'Settings', path: '/settings', icon: Settings },
  { label: 'Admin', path: '/admin', icon: ShieldCheck },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900 min-h-screen p-4 flex flex-col gap-2">
      <div className="px-3 py-4 text-xs font-semibold uppercase tracking-wider text-slate-400">
        Navigation
      </div>
      {navItems.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                isActive
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`
            }
          >
            <Icon className="w-4 h-4" />
            {item.label}
          </NavLink>
        );
      })}
    </aside>
  );
};
""",
                is_reusable=True
            ),
            FrontendComponent(
                name="Button",
                path="src/components/Button.tsx",
                category="UI",
                code_content="""import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({ variant = 'primary', isLoading, children, className = '', ...props }) => {
  const base = "px-4 py-2 rounded-lg font-medium text-sm transition flex items-center justify-center gap-2 disabled:opacity-50";
  const variants = {
    primary: "bg-blue-600 text-white hover:bg-blue-500 shadow-lg shadow-blue-500/20",
    secondary: "bg-slate-800 text-slate-200 hover:bg-slate-700 border border-slate-700",
    danger: "bg-red-600 text-white hover:bg-red-500 shadow-lg shadow-red-500/20",
    ghost: "text-slate-400 hover:text-white hover:bg-slate-800"
  };

  return (
    <button className={`${base} ${variants[variant]} ${className}`} disabled={isLoading || props.disabled} {...props}>
      {isLoading ? <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" /> : children}
    </button>
  );
};
""",
                is_reusable=True
            ),
            FrontendComponent(
                name="Card",
                path="src/components/Card.tsx",
                category="UI",
                code_content="""import React from 'react';

export const Card: React.FC<{ title?: string; children: React.ReactNode; className?: string }> = ({ title, children, className = '' }) => {
  return (
    <div className={`rounded-xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur ${className}`}>
      {title && <h3 className="text-lg font-semibold text-slate-100 mb-4">{title}</h3>}
      {children}
    </div>
  );
};
""",
                is_reusable=True
            )
        ]


global_component_generator = ReactComponentGenerator()
