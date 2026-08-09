import React, { useState, useEffect } from 'react';
import QualityHeader from '../components/quality/QualityHeader';
import OverallScore from '../components/quality/OverallScore';
import CategoryScores from '../components/quality/CategoryScores';
import QualityGates from '../components/quality/QualityGates';
import TestResults from '../components/quality/TestResults';
import SecurityDashboard from '../components/quality/SecurityDashboard';
import PerformanceDashboard from '../components/quality/PerformanceDashboard';
import ReviewerFindings from '../components/quality/ReviewerFindings';
import TestingFindings from '../components/quality/TestingFindings';
import RepairWorkflow from '../components/quality/RepairWorkflow';
import Recommendations from '../components/quality/Recommendations';
import { fetchQualityReport, triggerAutomaticRepair } from '../services/quality';
import { FaSpinner, FaExclamationTriangle, FaRedo } from 'react-icons/fa';

export default function QualityCenter({ generationId = 'aiforge-demo', setView }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Repair State
  const [repairActive, setRepairActive] = useState(false);
  const [repairStep, setRepairStep] = useState(1);
  const [repairComplete, setRepairComplete] = useState(false);

  const loadReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const report = await fetchQualityReport(generationId);
      setData(report);
    } catch (err) {
      console.error('Failed to load quality report:', err);
      setError('The quality service could not be reached.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, [generationId]);

  const handleNavigate = (targetView) => {
    if (setView) {
      setView(targetView);
    } else {
      window.location.href = `/projects/${generationId}/${targetView}`;
    }
  };

  const handleStartRepair = async () => {
    setRepairActive(true);
    setRepairStep(1);
    setRepairComplete(false);

    // Simulate step progression through repair workflow stages
    setTimeout(() => setRepairStep(2), 1200);
    setTimeout(() => setRepairStep(3), 2400);

    const repairRes = await triggerAutomaticRepair(generationId);

    setTimeout(() => setRepairStep(4), 3600);
    setTimeout(() => setRepairStep(5), 4800);
    setTimeout(() => {
      setRepairComplete(true);
      loadReport();
    }, 6000);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#090d16] text-white font-sans flex flex-col items-center justify-center p-6 space-y-4">
        <FaSpinner className="w-8 h-8 text-cyan-400 animate-spin" />
        <h3 className="text-base font-bold">AIForge Quality Analysis</h3>
        <p className="text-xs text-slate-400">Running quality checks & static AST inspections...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#090d16] text-white font-sans flex flex-col items-center justify-center p-6 text-center">
        <div className="bg-slate-950 border border-rose-500/30 rounded-2xl p-8 max-w-md shadow-2xl">
          <FaExclamationTriangle className="w-10 h-10 text-rose-400 mx-auto mb-4" />
          <h3 className="text-lg font-bold mb-2">Unable to load quality report</h3>
          <p className="text-xs text-slate-300 mb-6">{error}</p>
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={loadReport}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-xs font-bold text-white transition flex items-center gap-1.5"
            >
              <FaRedo /> Retry
            </button>
            <button
              onClick={() => handleNavigate('build')}
              className="px-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs font-semibold text-slate-300 hover:text-white transition"
            >
              Back to Build
            </button>
          </div>
        </div>
      </div>
    );
  }

  const projectName = data?.project_name || 'FoodDelivery AI';
  const overallScore = data?.overall_score || 96.0;
  const categories = data?.categories || {};
  const gates = data?.quality_gates || [];
  const passedGates = data?.passed_gates_count || 15;
  const totalGates = data?.total_gates_count || 15;
  const tests = data?.tests || {};
  const testBreakdown = data?.test_breakdown || {};
  const security = data?.security || {};
  const performance = data?.performance || {};
  const reviewerFindings = data?.reviewer_findings || [];
  const testingFindings = data?.testing_findings || {};
  const recommendations = data?.recommendations || [];

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans selection:bg-cyan-500 selection:text-white">
      {/* Header Bar */}
      <QualityHeader
        projectName={projectName}
        generationId={generationId}
        onNavigate={handleNavigate}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Active Self-Repair Workflow Banner */}
        {repairActive && (
          <RepairWorkflow
            step={repairStep}
            isComplete={repairComplete}
            onClose={() => setRepairActive(false)}
          />
        )}

        {/* Overall Score & Category Scores */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-4">
            <OverallScore score={overallScore} />
          </div>

          <div className="lg:col-span-8">
            <CategoryScores categories={categories} />
          </div>
        </div>

        {/* 15 Quality Gates Breakdown */}
        <QualityGates gates={gates} passedCount={passedGates} totalCount={totalGates} />

        {/* Testing & Security Dashboards Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TestResults tests={tests} breakdown={testBreakdown} />
          <SecurityDashboard security={security} />
        </div>

        {/* Runtime Performance Latency Dashboard */}
        <PerformanceDashboard performance={performance} />

        {/* Reviewer & Testing Agent Findings Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ReviewerFindings findings={reviewerFindings} />
          <TestingFindings testing={testingFindings} onTriggerRepair={handleStartRepair} />
        </div>

        {/* AI Recommendations */}
        <Recommendations recommendations={recommendations} />
      </main>
    </div>
  );
}
