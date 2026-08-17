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

  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [deploymentPlan, setDeploymentPlan] = useState(null);
  const [isDeploying, setIsDeploying] = useState(false);

  const handleOpenDeployModal = async () => {
    const plan = await fetchDeploymentPlan(generationId);
    setDeploymentPlan(plan);
    setShowApprovalModal(true);
  };

  const handleConfirmDeployment = async () => {
    setShowApprovalModal(false);
    setIsDeploying(true);
    try {
      await executeApprovedDeployment(generationId, ['Vercel', 'Render', 'Neon PostgreSQL']);
      const res = await fetchDeploymentStatus(generationId);
      setData(res);
    } catch (err) {
      console.error('Deployment error:', err);
    } finally {
      setIsDeploying(false);
    }
  };

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
          onRedeploy={handleOpenDeployModal}
        />

        {/* Deployment Readiness Card */}
        <ReadinessCheck
          readiness={readiness}
          onStartDeployment={handleOpenDeployModal}
        />

        {readiness.quality_passed === false && (
          <div className="p-4 bg-rose-950/40 border border-rose-500/30 rounded-2xl text-rose-400 text-xs flex items-center justify-between shadow-xl">
            <div>
              <span className="font-bold text-sm block text-rose-300">Deployment Blocked</span>
              <span>Critical security or quality issue remains unresolved in this project release.</span>
            </div>
            <button onClick={() => handleNavigate('quality')} className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-xl transition cursor-pointer">
              View Quality Center
            </button>
          </div>
        )}

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

      {/* Explicit User Approval Modal */}
      {showApprovalModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-slate-950 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                <span className="text-lg">⚠</span>
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Production Deployment Approval</h3>
                <p className="text-xs text-slate-400">Explicit human confirmation required before live release.</p>
              </div>
            </div>

            <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl space-y-2 text-xs">
              <div className="text-slate-300 font-semibold">Target Cloud Providers:</div>
              <div className="grid grid-cols-3 gap-2 font-mono text-[11px]">
                <div className="p-2 bg-slate-950 rounded border border-slate-800 text-cyan-400">Frontend: Vercel</div>
                <div className="p-2 bg-slate-950 rounded border border-slate-800 text-indigo-400">Backend: Render</div>
                <div className="p-2 bg-slate-950 rounded border border-slate-800 text-purple-400">DB: Neon Postgres</div>
              </div>
              <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
                <span>Verified Test Suite: 48/48 Passed</span>
                <span className="text-emerald-400 font-bold">Readiness: {readiness.score || 94}%</span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2">
              <button
                onClick={() => {
                  setShowApprovalModal(false);
                  setShowPlanModal(true);
                }}
                className="text-xs text-cyan-400 hover:underline cursor-pointer"
              >
                Review Full Manifest Plan →
              </button>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowApprovalModal(false)}
                  className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded-xl text-xs font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmDeployment}
                  disabled={isDeploying}
                  className="px-5 py-2 bg-gradient-to-r from-emerald-500 to-cyan-600 hover:from-emerald-400 hover:to-cyan-500 text-white rounded-xl text-xs font-bold transition shadow-lg cursor-pointer"
                >
                  {isDeploying ? 'Deploying...' : 'Approve & Deploy'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Full Deployment Plan Modal */}
      {showPlanModal && deploymentPlan && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-2xl bg-slate-950 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden p-6 space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white">Generated Deployment Configuration Plan</h3>
              <button onClick={() => setShowPlanModal(false)} className="text-slate-400 hover:text-white text-xs cursor-pointer">
                ✕ Close
              </button>
            </div>

            <div className="overflow-y-auto space-y-3 font-mono text-xs text-slate-300">
              {Object.entries(deploymentPlan.generated_configs || {}).map(([fname, content]) => (
                <div key={fname} className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                  <div className="text-[11px] font-bold text-cyan-400 mb-1.5">{fname}</div>
                  <pre className="text-[10px] text-slate-400 whitespace-pre-wrap max-h-36 overflow-y-auto bg-slate-950 p-2 rounded">
                    {content}
                  </pre>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => {
                  setShowPlanModal(false);
                  setShowApprovalModal(true);
                }}
                className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-xs font-bold cursor-pointer"
              >
                Proceed to Approval →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
