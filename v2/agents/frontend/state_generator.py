"""
AIForge V2 – Zustand State Store Generator
==========================================
Generates Zustand state management stores (useAuthStore, useProjectStore, useThemeStore).
"""

from typing import List
from v2.agents.frontend.models import FrontendStore


class ReactStateGenerator:

    def generate_default_stores(self, project_name: str) -> List[FrontendStore]:
        return [
            FrontendStore(
                store_name="useAuthStore",
                state_keys=["user", "isAuthenticated", "login", "logout"],
                code_content="""import { create } from 'zustand';

interface User {
  name: str;
  email: str;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: { name: 'Demo Engineer', email: 'engineer@aiforge.io' },
  isAuthenticated: true,
  login: (user) => set({ user, isAuthenticated: true }),
  logout: () => set({ user: null, isAuthenticated: false }),
}));
"""
            ),
            FrontendStore(
                store_name="useProjectStore",
                state_keys=["projects", "activeProject", "setProjects", "setActiveProject"],
                code_content="""import { create } from 'zustand';

export interface Project {
  id: str;
  name: str;
  status: string;
  complexity: string;
}

interface ProjectState {
  projects: Project[];
  activeProject: Project | null;
  setProjects: (projects: Project[]) => void;
  setActiveProject: (project: Project) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  projects: [
    { id: 'p1', name: 'AI Resume Analyzer', status: 'Completed', complexity: 'Medium' },
    { id: 'p2', name: 'E-Commerce Platform', status: 'In Progress', complexity: 'Enterprise' }
  ],
  activeProject: null,
  setProjects: (projects) => set({ projects }),
  setActiveProject: (activeProject) => set({ activeProject }),
}));
"""
            )
        ]


global_state_generator = ReactStateGenerator()
