import React, { useState, useEffect } from 'react';
import DeploymentHeader from '../components/deployment/DeploymentHeader';
import ReadinessCheck from '../components/deployment/ReadinessCheck';
import ProviderSelector from '../components/deployment/ProviderSelector';
import EnvironmentVariables from '../components/deployment/EnvironmentVariables';
import DeploymentConfig from '../components/deployment/DeploymentConfig';
import DatabaseConfig from '../components/deployment/DatabaseConfig';
import DeploymentWorkflow from '../components/deployment/DeploymentWorkflow';
import DeploymentLogs from '../components/deployment/DeploymentLogs';
import DeploymentStatus from '../components/deployment/DeploymentStatus';
import HealthMonitor from '../components/deployment/HealthMonitor';
import DeploymentHistory from '../components/deployment/DeploymentHistory';
import DeploymentAssistant from '../components/deployment/DeploymentAssistant';
import { fetchDeploymentStatus, startDeployment, validateDeployment, subscribeToDeploymentSSE } from '../services/deployment';
import { FaSpinner } from 'react-icons/fa';

export default function DeploymentCenter({ generationId = 'aiforge-demo', setView }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState('vercel');

  useEffect(() => {
    let intervalId = null;

    const loadStatus = async () => {
      const res = await fetchDeploymentStatus(generationId);
      setData(res);
      setLoading(false);
    };

    loadStatus();

    intervalId = setInterval(() => {
      loadStatus();
    }, 2000);

    const unsubscribeSSE = subscribeToDeploymentSSE(
      generationId,
      (eventData) => {
        if (eventData) {
          setData(eventData);
        }
      },
      () => {}
    );

    return () => {
      if (intervalId) clearInterval(intervalId);
      if (unsubscribeSSE) unsubscribeSSE();
    };
  }, [generationId]);

  const handleNavigate = (targetView) => {
    if (setView) {
      setView(targetView);
    } else {
      window.location.href = `/projects/${generationId}/${targetView}`;
    }
  };

  const handleStartDeployment = async () => {
    await startDeployment(generationId);
    const res = await fetchDeploymentStatus(generationId);
    setData(res);
  };

  const handleValidateConfig = async () => {
    await validateDeployment(generationId);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#090d16] text-white font-sans flex flex-col items-center justify-center p-6 space-y-4">
        <FaSpinner className="w-8 h-8 text-cyan-400 animate-spin" />
        <h3 className="text-base font-bold">AIForge Deployment Center</h3>
        <p className="text-xs text-slate-400">Inspecting deployment readiness & target manifests...</p>
      </div>
    );
  }

  const projectName = data?.project_name || 'FoodDelivery AI';
  const status = data?.status || 'LIVE';
  const readiness = data?.readiness || {};
  const providers = data?.providers || [];
  const envVars = data?.env_vars || [];
  const config = data?.config || {};
  const database = data?.database || {};
  const urls = data?.urls || {};
  const health = data?.health || {};
  const workflow = data?.workflow || [];
  const logs = data?.logs || [];
  const history = data?.history || [];

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans selection:bg-cyan-500 selection:text-white">
      {/* Stage Pipeline Header */}
      <DeploymentHeader
        projectName={projectName}
        generationId={generationId}
        onNavigate={handleNavigate}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Live Application Successful Deployment Banner */}
        <DeploymentStatus
          status={status}
          urls={urls}
          onRedeploy={handleStartDeployment}
        />

        {/* Deployment Readiness Card */}
        <ReadinessCheck
          readiness={readiness}
          onStartDeployment={handleStartDeployment}
        />

        {/* Target Provider Selector */}
        <ProviderSelector
          providers={providers}
          selectedProvider={selectedProvider}
          onSelectProvider={setSelectedProvider}
        />

        {/* Environment Variables & Secrets Vault */}
        <EnvironmentVariables
          envVars={envVars}
          onValidate={handleValidateConfig}
        />

        {/* Deployment & Database Configuration 2-Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <DeploymentConfig config={config} />
          <DatabaseConfig database={database} />
        </div>

        {/* Deployment Event Workflow Tracker */}
        <DeploymentWorkflow workflow={workflow} />

        {/* Terminal Log Output Stream */}
        <DeploymentLogs logs={logs} />

        {/* Health Probe Monitor */}
        <HealthMonitor generationId={generationId} healthData={health} />

        {/* History Audit Log & AI Assistant Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-6">
            <DeploymentHistory history={history} />
          </div>

          <div className="lg:col-span-6">
            <DeploymentAssistant generationId={generationId} />
          </div>
        </div>
      </main>
    </div>
  );
}
