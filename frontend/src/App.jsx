import { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import TopNav from "./components/navigation/TopNav";
import CommandPalette from "./components/navigation/CommandPalette";
import ChatBox from "./components/ChatBox";
import LiveCanvasPage from "./pages/LiveCanvasPage";
import ProjectGenerator from "./pages/ProjectGenerator";
import ReflectionDashboard from "./components/ReflectionDashboard";
import MainLayout from "./layouts/MainLayout";
import Dashboard from "./pages/Dashboard";
import MissionControlPage from "./pages/MissionControlPage";
import ProjectsPage from "./pages/ProjectsPage";
import AgentsPage from "./pages/AgentsPage";
import AIToolsPage from "./pages/AIToolsPage";
import MemoryPage from "./pages/MemoryPage";
import TasksPage from "./pages/TasksPage";
import DeepResearchPage from "./pages/DeepResearchPage";
import WorkflowsPage from "./pages/WorkflowsPage";
import AutonomousWorkflowPage from "./pages/AutonomousWorkflowPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import SavedOutputsPage from "./pages/SavedOutputsPage";
import ActivityHistoryPage from "./pages/ActivityHistoryPage";
import LearningDashboard from "./pages/LearningDashboard";
import F1Website from "./components/F1Website";
import SecurityCenter from "./pages/SecurityCenter";
import SentinelPage from "./pages/SentinelPage";
import CyberCopilotPage from "./pages/CyberCopilotPage";
import VerifiableAiPage from "./pages/VerifiableAiPage";
import AiOsControlCenterPage from "./pages/AiOsControlCenterPage";
import ComputerAgentPage from "./pages/ComputerAgentPage";
import IntelligencePlatformPage from "./pages/IntelligencePlatformPage";
import KnowledgeGraphPage from "./pages/KnowledgeGraphPage";
import MultiAgentPage from "./pages/MultiAgentPage";
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
import ApiKeys from "./pages/ApiKeys";
import ObservabilityPage from "./pages/ObservabilityPage";
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
import ExecutionValidationView from "./components/ExecutionValidationView";
import CIPipelineDashboard from "./components/CIPipelineDashboard";
import { AuthProvider } from "./auth/AuthProvider";
import ProtectedRoute from "./auth/ProtectedRoute";

function AppContent() {
    const [view, setView] = useState("dashboard");
    const [activeProjectName, setActiveProjectName] = useState("");
    const [activeGenerationId, setActiveGenerationId] = useState("aiforge-fooddelivery-ai");
    const [selectedFile, setSelectedFile] = useState(null);
    const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
    const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

    // Global keyboard shortcut for Command Palette (Ctrl+K or Cmd+K)
    useEffect(() => {
        const handleKeyDown = (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
                e.preventDefault();
                setIsCommandPaletteOpen((prev) => !prev);
            }
        };
        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, []);

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
    if (view === "landing") return <LandingPage setView={setView} />;
    if (view === "login") return <Login setView={setView} />;
    if (view === "register") return <Register setView={setView} />;
    if (view === "forgot-password") return <ForgotPassword setView={setView} />;
    if (view === "reset-password") return <ResetPassword setView={setView} />;

    return (
        <MainLayout>
            {/* Left Sidebar Navigation */}
            <Sidebar 
                currentView={view} 
                setView={setView} 
                isMobileOpen={isMobileSidebarOpen}
                onCloseMobile={() => setIsMobileSidebarOpen(false)}
            />
            
            {/* Active Workspace View Area with TopNav */}
            <div className="flex-1 flex flex-col min-w-0 min-h-0 bg-[#08090D] overflow-hidden">
                {/* Top Navigation Bar */}
                <TopNav
                    currentView={view}
                    setView={setView}
                    onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
                    onToggleSidebar={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
                />

                {/* Main Content Area */}
                <main className={`flex-1 min-w-0 min-h-0 ${view === "code" ? "overflow-hidden" : "overflow-y-auto custom-scrollbar"}`}>
                    {/* Primary Dashboard / Command Center */}
                    {view === "dashboard" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <Dashboard 
                                setView={setView} 
                                setActiveProjectName={setActiveProjectName} 
                                setActiveGenerationId={setActiveGenerationId} 
                            />
                        </ProtectedRoute>
                    )}

                    {/* Dedicated Navigation Views */}
                    {view === "mission-control" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <MissionControlPage setView={setView} activeProjectId={activeProjectName || activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "chat" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <ChatBox />
                        </ProtectedRoute>
                    )}
                    {view === "canvas" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <LiveCanvasPage setView={setView} activeProjectId={activeProjectName || activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "agents" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <AgentsPage setView={setView} activeProjectId={activeProjectName || activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "multi-agent" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <MultiAgentPage setView={setView} activeProjectId={activeProjectName || activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "projects" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <ProjectsPage 
                                setView={setView} 
                                setActiveProjectName={setActiveProjectName} 
                                setActiveGenerationId={setActiveGenerationId} 
                            />
                        </ProtectedRoute>
                    )}
                    {view === "tools" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <AIToolsPage setView={setView} />
                        </ProtectedRoute>
                    )}
                    {view === "memory" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <MemoryPage setView={setView} activeProjectId={activeProjectName || activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "tasks" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <TasksPage setView={setView} activeProjectId={activeProjectName || activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "knowledge-graph" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <KnowledgeGraphPage setView={setView} activeProjectId={activeProjectName || activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "research" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <DeepResearchPage setView={setView} activeProjectId={activeProjectName || activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "workflows" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <AutonomousWorkflowPage setView={setView} activeProjectId={activeProjectName || activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "analytics" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <AnalyticsPage setView={setView} />
                        </ProtectedRoute>
                    )}
                    {view === "saved" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <SavedOutputsPage setView={setView} />
                        </ProtectedRoute>
                    )}
                    {view === "history" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <ActivityHistoryPage setView={setView} />
                        </ProtectedRoute>
                    )}
                    {view === "cyber-copilot" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <CyberCopilotPage setView={setView} activeProjectId={activeProjectName || activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "verifiable-ai" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <VerifiableAiPage setView={setView} activeProjectId={activeProjectName || activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "ai-os" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <AiOsControlCenterPage setView={setView} activeProjectId={activeProjectName || activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "computer-agent" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <ComputerAgentPage setView={setView} activeProjectId={activeProjectName || activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "intelligence" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <IntelligencePlatformPage setView={setView} activeProjectId={activeProjectName || activeGenerationId} />
                        </ProtectedRoute>
                    )}

                    {/* Specialized Engineering Suite Pages */}
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
                    {view === "execution-validation" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <ExecutionValidationView />
                        </ProtectedRoute>
                    )}
                    {view === "ci-pipeline" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <CIPipelineDashboard 
                                projectId={activeProjectName || activeGenerationId} 
                                onBack={() => setView("dashboard")} 
                            />
                        </ProtectedRoute>
                    )}
                    {view === "code" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <CodeWorkspace generationId={activeGenerationId} setView={setView} />
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
                    {(view === "security" || view === "sentinel") && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <SentinelPage setView={setView} activeProjectId={activeProjectName || activeGenerationId} />
                        </ProtectedRoute>
                    )}
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
                    {view === "github" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <GitHubDashboardPage />
                        </ProtectedRoute>
                    )}
                    {view === "kubernetes" && <KubernetesDashboardPage />}
                    {view === "infrastructure" && <InfrastructureDashboardPage />}
                    {view === "finops" && <FinOpsDashboardPage />}
                    {view === "f1" && <F1Website />}
                </main>
            </div>

            {/* Global Command Palette Modal */}
            <CommandPalette
                isOpen={isCommandPaletteOpen}
                onClose={() => setIsCommandPaletteOpen(false)}
                setView={setView}
            />
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
