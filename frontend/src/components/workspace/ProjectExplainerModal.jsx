import React, { useState } from 'react';
import {
  FaRobot,
  FaTimes,
  FaLayerGroup,
  FaServer,
  FaCode,
  FaDatabase,
  FaLock,
  FaRocket,
  FaLightbulb
} from 'react-icons/fa';

export default function ProjectExplainerModal({
  open = false,
  onClose = null,
  projectName = 'AIForge Application'
}) {
  const [activeSection, setActiveSection] = useState('overview');

  if (!open) return null;

  const sections = {
    overview: {
      title: 'Full-Stack Project Overview',
      icon: FaLayerGroup,
      content: `This application is an autonomous full-stack software system architected by AIForge.\n\n- Frontend: React 18 + Vite provides a responsive, component-driven user experience.\n- Backend: FastAPI provides async REST endpoints with strict Pydantic contract validation.\n- Database: PostgreSQL stores relational entities with foreign-key constraints.\n- Workflow: End-to-end data flow operates from React client → FastAPI router → Service layer → SQLAlchemy ORM → PostgreSQL.`
    },
    backend: {
      title: 'Backend API & Business Logic',
      icon: FaServer,
      content: `The backend follows clean layered architecture:\n\n- Routing: FastAPI APIRouter manages endpoints in modular files (auth.py, products.py, orders.py).\n- Validation: Request/response schemas ensure type-safety and fail-safe inputs.\n- Services: Dedicated service classes isolate business rules from HTTP handling.\n- Error Handling: Centralized exception handlers return structured JSON error payloads.`
    },
    frontend: {
      title: 'Frontend Component Architecture',
      icon: FaCode,
      content: `The frontend is built with React and Tailwind CSS:\n\n- State Management: React hooks (useState, useEffect, useMemo) manage client-side state.\n- API Client: Axios instances with standardized interceptors and timeout protections.\n- UI Components: Reusable, responsive modular elements designed for accessibility.\n- Live Reload: Vite HMR ensures sub-second feedback during development.`
    },
    database: {
      title: 'Database Schema & Relations',
      icon: FaDatabase,
      content: `The database uses PostgreSQL with relational integrity:\n\n- Users: Primary entity with unique email constraints and hashed credentials.\n- Entities: Products, Orders, Wishlist items linked via 1-to-Many foreign keys.\n- Migrations: Managed via versioned schema DDL scripts with rollback safeguards.\n- Indexing: B-Tree indexes on foreign keys and search query columns.`
    },
    security: {
      title: 'Authentication & Security Policy',
      icon: FaLock,
      content: `Security safeguards configured:\n\n- Authentication: JWT tokens with HS256 algorithm and expiration TTL.\n- Sensitive Data: Password hashing via bcrypt, .env secret masking.\n- Sandbox: Path traversal protection on all file endpoints (blocks '../' and secret files).\n- Sanitization: Input escaping prevents SQL injection and XSS attacks.`
    }
  };

  const current = sections[activeSection];
  const Icon = current.icon;

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-slate-950 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden font-sans flex flex-col">
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-800 bg-[#070c18] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <FaLightbulb className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white">AI Project Explainer</h2>
              <p className="text-[10px] text-slate-400">{projectName}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-900 transition cursor-pointer"
          >
            <FaTimes className="w-4 h-4" />
          </button>
        </div>

        {/* Section Navigation Chips */}
        <div className="px-5 py-2.5 border-b border-slate-800/80 bg-slate-950 flex gap-2 overflow-x-auto custom-scrollbar">
          {Object.entries(sections).map(([key, sec]) => {
            const SecIcon = sec.icon;
            const isActive = activeSection === key;
            return (
              <button
                key={key}
                onClick={() => setActiveSection(key)}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition shrink-0 cursor-pointer ${
                  isActive
                    ? 'bg-cyan-600/20 text-cyan-300 border border-cyan-500/40'
                    : 'text-slate-400 hover:text-white hover:bg-slate-900'
                }`}
              >
                <SecIcon className="w-3 h-3" />
                <span className="capitalize">{key}</span>
              </button>
            );
          })}
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto max-h-96 space-y-4">
          <div className="flex items-center gap-2.5">
            <Icon className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-bold text-white">{current.title}</h3>
          </div>
          <div className="p-4 rounded-xl bg-[#060911] border border-slate-800/80 font-sans text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
            {current.content}
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-800 bg-[#070c18] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold cursor-pointer"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
