import React, { useState, useEffect } from 'react';
import ProjectHeader from '../components/generation/ProjectHeader';
import AgentPipeline from '../components/generation/AgentPipeline';
import AgentCard from '../components/generation/AgentCard';
import AgentLogs from '../components/generation/AgentLogs';
import ProgressBar from '../components/generation/ProgressBar';
import CompletionActions from '../components/generation/CompletionActions';
import RepairLoop from '../components/generation/RepairLoop';
import { fetchGenerationStatus, cancelGeneration, subscribeToGenerationSSE } from '../services/generation';

export default function GenerationDashboard({ generationId = 'aiforge-demo', setView, setActiveProjectName }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let intervalId = null;

    const loadStatus = async () => {
      const res = await fetchGenerationStatus(generationId);
      setData(res);
      setLoading(false);
      if (res.project_name && setActiveProjectName) {
        setActiveProjectName(res.project_name);
      }
    };

    loadStatus();

    // Setup polling every 1.5 seconds while active
    intervalId = setInterval(() => {
      loadStatus();
    }, 1500);

    // Also attempt SSE subscription
    const unsubscribeSSE = subscribeToGenerationSSE(
      generationId,
      (eventData) => {
        if (eventData) {
          setData(eventData);
          if (eventData.project_name && setActiveProjectName) {
            setActiveProjectName(eventData.project_name);
          }
        }
      },
      () => {
        // SSE error callback -> polling continues seamlessly
      }
    );

    return () => {
      if (intervalId) clearInterval(intervalId);
      if (unsubscribeSSE) unsubscribeSSE();
    };
  }, [generationId]);

  const handleCancel = async () => {
    await cancelGeneration(generationId);
    const res = await fetchGenerationStatus(generationId);
    setData(res);
  };

  const handleOpenWorkspace = () => {
    if (setView) {
      setView('code');
    } else {
      window.location.href = `/projects/${generationId}/code`;
    }
  };


  const handleViewQualityReport = () => {
    if (setView) {
      setView('metrics');
    } else {
      window.location.href = `/projects/${generationId}/quality`;
    }
  };

  const projectName = data?.project_name || 'FoodDelivery AI';
  const stack = data?.stack || { frontend: 'React', backend: 'FastAPI', database: 'PostgreSQL', styling: 'Tailwind CSS' };
  const status = data?.status || 'COMPLETED';
  const progress = data?.progress ?? 100;
  const currentAgent = data?.current_agent || 'completed';
  const logs = data?.logs || [];
  const qualityScore = data?.quality_score || 96.0;
  const testsPassed = data?.tests_passed ?? 48;
  const testsFailed = data?.tests_failed ?? 0;

  // Convert array of agent objects to map
  const agentsMap = {};
  if (data?.agents && Array.isArray(data.agents)) {
    data.agents.forEach((ag) => {
      agentsMap[ag.name?.toLowerCase()] = ag;
    });
  }

  const completedAgentsCount = Object.values(agentsMap).filter((ag) => ag.status?.toLowerCase() === 'completed').length;
  const totalAgentsCount = Object.keys(agentsMap).length || 8;

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans selection:bg-cyan-500 selection:text-white">
      <ProjectHeader
        projectName={projectName}
        stack={stack}
        generationId={generationId}
        status={status}
        onCancel={handleCancel}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Completion Banner Actions */}
        {status?.toUpperCase() === 'COMPLETED' && (
          <CompletionActions
            generationId={generationId}
            qualityScore={qualityScore}
            testsPassed={testsPassed}
            totalTests={testsPassed + testsFailed}
            onOpenWorkspace={handleOpenWorkspace}
            onViewQualityReport={handleViewQualityReport}
          />
        )}

        {/* Bounded Repair Loop Banner */}
        {status?.toUpperCase() === 'REPAIRING' && (
          <RepairLoop active={true} attempt={1} maxAttempts={3} />
        )}

        {/* Overall Progress Bar */}
        <ProgressBar
          completedCount={completedAgentsCount || 8}
          totalCount={totalAgentsCount || 8}
          progress={progress}
        />

        {/* Main 2-Column Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Agent Pipeline Workflow */}
          <div className="lg:col-span-5">
            <AgentPipeline agentsMap={agentsMap} />
          </div>

          {/* Right Column: Active Agent Card & Live Logs */}
          <div className="lg:col-span-7 flex flex-col gap-6">
            <AgentCard currentAgent={currentAgent} progress={progress} />
            <AgentLogs logs={logs} />
          </div>
        </div>
      </main>
    </div>
  );
}
