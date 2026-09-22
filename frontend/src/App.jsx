import { useState, useEffect, lazy, Suspense } from "react";
import Sidebar from "./components/Sidebar";
import TopNav from "./components/navigation/TopNav";
import CommandPalette from "./components/navigation/CommandPalette";
import MainLayout from "./layouts/MainLayout";
import { AuthProvider } from "./auth/AuthProvider";
import ProtectedRoute from "./auth/ProtectedRoute";

// Route-level code splitting: each view is only fetched when it is first
// navigated to, instead of all ~55 pages being bundled into one chunk.
const ChatBox = lazy(() => import("./components/ChatBox"));
const LiveCanvasPage = lazy(() => import("./pages/LiveCanvasPage"));
const ProjectGenerator = lazy(() => import("./pages/ProjectGenerator"));
const ReflectionDashboard = lazy(() => import("./components/ReflectionDashboard"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const MissionControlPage = lazy(() => import("./pages/MissionControlPage"));
const ProjectsPage = lazy(() => import("./pages/ProjectsPage"));
const AgentsPage = lazy(() => import("./pages/AgentsPage"));
const AIToolsPage = lazy(() => import("./pages/AIToolsPage"));
const MemoryPage = lazy(() => import("./pages/MemoryPage"));
const TasksPage = lazy(() => import("./pages/TasksPage"));
const DeepResearchPage = lazy(() => import("./pages/DeepResearchPage"));
const AutonomousWorkflowPage = lazy(() => import("./pages/AutonomousWorkflowPage"));
const AnalyticsPage = lazy(() => import("./pages/AnalyticsPage"));
const SavedOutputsPage = lazy(() => import("./pages/SavedOutputsPage"));
const ActivityHistoryPage = lazy(() => import("./pages/ActivityHistoryPage"));
const LearningDashboard = lazy(() => import("./pages/LearningDashboard"));
const F1Website = lazy(() => import("./components/F1Website"));
const SentinelPage = lazy(() => import("./pages/SentinelPage"));
const CyberCopilotPage = lazy(() => import("./pages/CyberCopilotPage"));
const VerifiableAiPage = lazy(() => import("./pages/VerifiableAiPage"));
const AiOsControlCenterPage = lazy(() => import("./pages/AiOsControlCenterPage"));
const ComputerAgentPage = lazy(() => import("./pages/ComputerAgentPage"));
const IntelligencePlatformPage = lazy(() => import("./pages/IntelligencePlatformPage"));
const KnowledgeGraphPage = lazy(() => import("./pages/KnowledgeGraphPage"));
const MultiAgentPage = lazy(() => import("./pages/MultiAgentPage"));
const LandingPage = lazy(() => import("./pages/LandingPage"));
const CreateProject = lazy(() => import("./pages/CreateProject"));
const GenerationDashboard = lazy(() => import("./pages/GenerationDashboard"));
const CodeWorkspace = lazy(() => import("./pages/CodeWorkspace"));
const QualityCenter = lazy(() => import("./pages/QualityCenter"));
const DeploymentCenter = lazy(() => import("./pages/DeploymentCenter"));
const ProjectDetails = lazy(() => import("./pages/ProjectDetails"));
const ProjectOverviewPage = lazy(() => import("./pages/ProjectOverviewPage"));
const ProjectXRayPage = lazy(() => import("./pages/ProjectXRayPage"));
const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const ResetPassword = lazy(() => import("./pages/ResetPassword"));
const Settings = lazy(() => import("./pages/Settings"));
const ApiKeys = lazy(() => import("./pages/ApiKeys"));
const ObservabilityPage = lazy(() => import("./pages/ObservabilityPage"));
const MonitoringPage = lazy(() => import("./pages/MonitoringPage"));
const GitHubDashboardPage = lazy(() => import("./pages/GitHubDashboardPage"));
const KubernetesDashboardPage = lazy(() => import("./pages/KubernetesDashboardPage"));
const InfrastructureDashboardPage = lazy(() => import("./pages/InfrastructureDashboardPage"));
const FinOpsDashboardPage = lazy(() => import("./pages/FinOpsDashboardPage"));
const EvaluationCenter = lazy(() => import("./pages/EvaluationCenter"));
const AutopilotDashboard = lazy(() => import("./pages/AutopilotDashboard"));
const FlightRecorder = lazy(() => import("./pages/FlightRecorder"));
const SimulatorPage = lazy(() => import("./pages/SimulatorPage"));
const DnaGraphPage = lazy(() => import("./pages/DnaGraphPage"));
const BugBountyPage = lazy(() => import("./pages/BugBountyPage"));
const DebateArenaPage = lazy(() => import("./pages/DebateArenaPage"));
const SoftwareAssistantPage = lazy(() => import("./pages/SoftwareAssistantPage"));
const ExecutionValidationView = lazy(() => import("./components/ExecutionValidationView"));
const CIPipelineDashboard = lazy(() => import("./components/CIPipelineDashboard"));

function PageLoader() {
    return (
        <div className="flex-1 flex items-center justify-center h-full w-full py-24 text-gray-500">
            <div className="w-6 h-6 border-2 border-gray-700 border-t-indigo-500 rounded-full animate-spin" />
        </div>
    );
}

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
            <Suspense fallback={<PageLoader />}>
                <AppContent />
            </Suspense>
        </AuthProvider>
    );
}

export default App;
