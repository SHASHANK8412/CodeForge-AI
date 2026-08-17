import { useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatBox from "./components/ChatBox";
import ProjectGenerator from "./pages/ProjectGenerator";
import ReflectionDashboard from "./components/ReflectionDashboard";
import MetricsDashboard from "./components/MetricsDashboard";
import MainLayout from "./layouts/MainLayout";
import Dashboard from "./pages/Dashboard";
import PluginsDashboard from "./pages/PluginsDashboard";
import LearningDashboard from "./pages/LearningDashboard";
import F1Website from "./components/F1Website";
import TalkToCodePage from "./pages/SoftwareAssistantPage";
import SecurityCenter from "./pages/SecurityCenter";
import LandingPage from "./pages/LandingPage";
import CreateProject from "./pages/CreateProject";
import GenerationDashboard from "./pages/GenerationDashboard";
import CodeWorkspace from "./pages/CodeWorkspace";
import QualityCenter from "./pages/QualityCenter";
import DeploymentCenter from "./pages/DeploymentCenter";
import ProjectDetails from "./pages/ProjectDetails";
import ProjectOverviewPage from "./pages/ProjectOverviewPage";
import ProjectXRayPage from "./pages/ProjectXRayPage";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Settings from "./pages/Settings";
import ObservabilityPage from "./pages/ObservabilityPage";
import ObservabilityDashboard from "./pages/ObservabilityDashboard";
import MonitoringPage from "./pages/MonitoringPage";
import GitHubDashboardPage from "./pages/GitHubDashboardPage";
import KubernetesDashboardPage from "./pages/KubernetesDashboardPage";
import InfrastructureDashboardPage from "./pages/InfrastructureDashboardPage";
import FinOpsDashboardPage from "./pages/FinOpsDashboardPage";
import EvaluationCenter from "./pages/EvaluationCenter";





import AutopilotDashboard from "./pages/AutopilotDashboard";
import FlightRecorder from "./pages/FlightRecorder";
import SimulatorPage from "./pages/SimulatorPage";
import DnaGraphPage from "./pages/DnaGraphPage";
import BugBountyPage from "./pages/BugBountyPage";
import DebateArenaPage from "./pages/DebateArenaPage";
import SoftwareAssistantPage from "./pages/SoftwareAssistantPage";
import { AuthProvider } from "./auth/AuthProvider";
import ProtectedRoute from "./auth/ProtectedRoute";


function AppContent() {
    const [view, setView] = useState("landing");
    const [activeProjectName, setActiveProjectName] = useState("");
    const [activeGenerationId, setActiveGenerationId] = useState("aiforge-demo");
    const [selectedFile, setSelectedFile] = useState(null); // { project, path, content }

    const handleFileSelect = (projectName, filePath, content) => {
        setSelectedFile({
            project: projectName,
            path: filePath,
            content: content
        });
        setView("project");
    };

    const handleGenerateSuccess = (generationId, projName) => {
        if (projName) {
            setActiveProjectName(projName);
        }
        if (generationId) {
            setActiveGenerationId(generationId);
        }
        setView("build");
    };

    // Public auth pages without main layout sidebar
    if (view === "login") return <Login setView={setView} />;
    if (view === "register") return <Register setView={setView} />;
    if (view === "forgot-password") return <ForgotPassword setView={setView} />;
    if (view === "reset-password") return <ResetPassword setView={setView} />;

    return (
        <MainLayout>
            {/* Unified Sidebar managing the active view */}
            <Sidebar currentView={view} setView={setView} />
            
            {/* Active Workspace Panel */}
            <div className={`flex-1 flex flex-col min-w-0 min-h-0 bg-bg-base ${view === "code" ? "overflow-hidden" : "overflow-y-auto"}`}>
                {view === "landing" && <LandingPage setView={setView} />}
                
                {/* Protected Routes */}
                {view === "create" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <CreateProject setView={setView} onGenerateSuccess={handleGenerateSuccess} />
                    </ProtectedRoute>
                )}
                {view === "build" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <GenerationDashboard generationId={activeGenerationId} setView={setView} setActiveProjectName={setActiveProjectName} />
                    </ProtectedRoute>
                )}
                {view === "code" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <CodeWorkspace generationId={activeGenerationId} setView={setView} />
                    </ProtectedRoute>
                )}
                {view === "dashboard" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <Dashboard setView={setView} setActiveProjectName={setActiveProjectName} setActiveGenerationId={setActiveGenerationId} />
                    </ProtectedRoute>
                )}
                {view === "project-details" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <ProjectDetails generationId={activeGenerationId} setView={setView} />
                    </ProtectedRoute>
                )}
                {(view === "project-overview" || view === "project-memory") && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <ProjectOverviewPage projectId={activeProjectName || activeGenerationId} setView={setView} setActiveProjectName={setActiveProjectName} setActiveGenerationId={setActiveGenerationId} />
                    </ProtectedRoute>
                )}
                {view === "xray" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <ProjectXRayPage projectId={activeProjectName || activeGenerationId} setView={setView} />
                    </ProtectedRoute>
                )}
                {view === "metrics" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <QualityCenter generationId={activeGenerationId} setView={setView} />
                    </ProtectedRoute>
                )}
                {(view === "plugins" || view === "deploy") && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <DeploymentCenter generationId={activeGenerationId} setView={setView} />
                    </ProtectedRoute>
                )}
                {view === "settings" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <Settings setView={setView} />
                    </ProtectedRoute>
                )}
                {view === "api-keys" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <ApiKeys />
                    </ProtectedRoute>
                )}
                {view === "observability" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <ObservabilityPage projectId={activeGenerationId} />
                    </ProtectedRoute>
                )}

                {view === "evaluations" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <EvaluationCenter />
                    </ProtectedRoute>
                )}
                {view === "autopilot" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <AutopilotDashboard generationId={activeGenerationId} setView={setView} setActiveGenerationId={setActiveGenerationId} />
                    </ProtectedRoute>
                )}
                {view === "flight-recorder" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <FlightRecorder projectId={activeGenerationId} setView={setView} />
                    </ProtectedRoute>
                )}
                {view === "simulator" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <SimulatorPage projectId={activeGenerationId} />
                    </ProtectedRoute>
                )}
                {view === "dna" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <DnaGraphPage projectId={activeGenerationId} />
                    </ProtectedRoute>
                )}
                {view === "bug-bounty" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <BugBountyPage projectId={activeGenerationId} />
                    </ProtectedRoute>
                )}
                {view === "debate" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <DebateArenaPage generationId={activeGenerationId} />
                    </ProtectedRoute>
                )}
                {view === "talk" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <SoftwareAssistantPage projectId={activeGenerationId} />
                    </ProtectedRoute>
                )}


                {/* Additional views */}
                {view === "security" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <SecurityCenter projectId={activeGenerationId} />
                    </ProtectedRoute>
                )}
                {view === "chat" && <ChatBox />}
                {view === "project" && (
                    <ProjectGenerator 
                        activeProjectName={activeProjectName}
                        setActiveProjectName={setActiveProjectName}
                        selectedFile={selectedFile}
                        setSelectedFile={setSelectedFile}
                        onFileSelect={handleFileSelect}
                    />
                )}
                {view === "reflection" && <ReflectionDashboard />}
                {view === "learning" && <LearningDashboard />}
                {view === "monitoring" && <MonitoringPage />}
                {view === "github" && <GitHubDashboardPage />}
                {view === "kubernetes" && <KubernetesDashboardPage />}
                {view === "infrastructure" && <InfrastructureDashboardPage />}
                {view === "finops" && <FinOpsDashboardPage />}
                {view === "f1" && <F1Website />}




            </div>
        </MainLayout>
    );
}

function App() {
    return (
        <AuthProvider>
            <AppContent />
        </AuthProvider>
    );
}

export default App;


