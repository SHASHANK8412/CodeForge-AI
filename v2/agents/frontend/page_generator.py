"""
AIForge V2 – React Page Generator
=================================
Generates page components (Dashboard, ResumeUpload, Login, Register, Profile, Settings, Admin, NotFound).
"""

from typing import List
from v2.agents.frontend.models import FrontendPage


class ReactPageGenerator:

    def generate_default_pages(self, project_name: str) -> List[FrontendPage]:
        return [
            FrontendPage(
                name="Dashboard",
                route_path="/dashboard",
                code_content="""import React from 'react';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { FileText, Award, TrendingUp, AlertTriangle } from 'lucide-react';

export const Dashboard: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Project Dashboard</h1>
          <p className="text-slate-400 text-sm">Autonomous Engineering Telemetry & Status</p>
        </div>
        <Button variant="primary">New Analysis</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="flex items-center gap-4">
          <div className="p-3 bg-blue-600/20 text-blue-400 rounded-xl"><FileText /></div>
          <div>
            <div className="text-2xl font-bold text-white">48</div>
            <div className="text-xs text-slate-400">Resumes Processed</div>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="p-3 bg-emerald-600/20 text-emerald-400 rounded-xl"><Award /></div>
          <div>
            <div className="text-2xl font-bold text-white">94.7%</div>
            <div className="text-xs text-slate-400">Avg ATS Score</div>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="p-3 bg-indigo-600/20 text-indigo-400 rounded-xl"><TrendingUp /></div>
          <div>
            <div className="text-2xl font-bold text-white">12.4ms</div>
            <div className="text-xs text-slate-400">Avg Latency</div>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="p-3 bg-amber-600/20 text-amber-400 rounded-xl"><AlertTriangle /></div>
          <div>
            <div className="text-2xl font-bold text-white">0</div>
            <div className="text-xs text-slate-400">Critical Risks</div>
          </div>
        </Card>
      </div>
    </div>
  );
};
""",
                is_protected=True
            ),
            FrontendPage(
                name="ResumeUpload",
                route_path="/upload",
                code_content="""import React, { useState } from 'react';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { UploadCloud, CheckCircle } from 'lucide-react';

export const ResumeUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleUpload = () => {
    setIsProcessing(true);
    setTimeout(() => setIsProcessing(false), 2000);
  };

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">Upload Resume</h1>
      <Card title="Upload PDF or DOCX Resume">
        <div className="border-2 border-dashed border-slate-700 hover:border-blue-500 rounded-xl p-12 text-center space-y-4 transition bg-slate-950/40">
          <UploadCloud className="w-12 h-12 text-slate-400 mx-auto" />
          <p className="text-slate-300 font-medium">Drag and drop your file here, or click to browse</p>
          <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} className="hidden" id="fileInput" />
          <label htmlFor="fileInput">
            <Button variant="secondary">Select File</Button>
          </label>
        </div>
        {file && (
          <div className="mt-4 p-4 bg-slate-800/80 rounded-lg flex items-center justify-between text-sm">
            <span className="text-slate-200">{file.name}</span>
            <Button variant="primary" isLoading={isProcessing} onClick={handleUpload}>
              Analyze Resume
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};
""",
                is_protected=True
            ),
            FrontendPage(
                name="Login",
                route_path="/login",
                code_content="""import React, { useState } from 'react';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { useAuthStore } from '../stores/useAuthStore';
import { useNavigate } from 'react-router-dom';

export const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login({ name: username || 'User', email: 'user@aiforge.io' });
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-950">
      <Card title="Sign In to AIForge V2" className="w-full max-w-md">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1 uppercase">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-white focus:border-blue-500 focus:outline-none"
              placeholder="Enter username"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1 uppercase">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-white focus:border-blue-500 focus:outline-none"
              placeholder="Enter password"
            />
          </div>
          <Button variant="primary" className="w-full">Sign In</Button>
        </form>
      </Card>
    </div>
  );
};
""",
                is_protected=False
            )
        ]


global_page_generator = ReactPageGenerator()
