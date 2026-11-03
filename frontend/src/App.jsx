import { useState, useEffect, lazy, Suspense } from "react";
import Sidebar from "./components/Sidebar";
import TopNav from "./components/navigation/TopNav";
import CommandPalette from "./components/navigation/CommandPalette";
import MainLayout from "./layouts/MainLayout";
import { AuthProvider } from "./auth/AuthProvider";
import ProtectedRoute from "./auth/ProtectedRoute";
import { fetchProjects } from "./services/projects";

// Route-level code splitting: each view is only fetched when it is first
// navigated to, instead of all ~55 pages being bundled into one chunk.
const ChatBox = lazy(() => import("./components/ChatBox"));
const LiveCanvasPage = lazy(() => import("./pages/LiveCanvasPage"));
const ProjectGenerator = lazy(() => import("./pages/ProjectGenerator"));
const ReflectionDashboard = lazy(() => import("./components/ReflectionDashboard"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const ProjectsPage = lazy(() => import("./pages/ProjectsPage"));
const AgentsPage = lazy(() => import("./pages/AgentsPage"));
const AIToolsPage = lazy(() => import("./pages/AIToolsPage"));
const MemoryPage = lazy(() => import("./pages/MemoryPage"));
const TasksPage = lazy(() => import("./pages/TasksPage"));
const AnalyticsPage = lazy(() => import("./pages/AnalyticsPage"));
const SavedOutputsPage = lazy(() => import("./pages/SavedOutputsPage"));
const ActivityHistoryPage = lazy(() => import("./pages/ActivityHistoryPage"));
const LearningDashboard = lazy(() => import("./pages/LearningDashboard"));
const VerifiableAiPage = lazy(() => import("./pages/VerifiableAiPage"));
const SwarmPage = lazy(() => import("./pages/SwarmPage"));
const RealitySimulatorPage = lazy(() => import("./pages/RealitySimulatorPage"));
const ExecutionGuardianPage = lazy(() => import("./pages/ExecutionGuardianPage"));
const IntegrationEnginePage = lazy(() => import("./pages/IntegrationEnginePage"));
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
const BenchmarkLabPage = lazy(() => import("./pages/BenchmarkLabPage"));
const AutopilotDashboard = lazy(() => import("./pages/AutopilotDashboard"));
const AutopilotEvolutionPage = lazy(() => import("./pages/AutopilotEvolutionPage"));
const DigitalTwinPage = lazy(() => import("./pages/DigitalTwinPage"));
const PerformanceEngineerPage = lazy(() => import("./pages/PerformanceEngineerPage"));
const ChaosEngineerPage = lazy(() => import("./pages/ChaosEngineerPage"));
const SecurityGuardianPage = lazy(() => import("./pages/SecurityGuardianPage"));
const EvolutionEnginePage = lazy(() => import("./pages/EvolutionEnginePage"));
const TimeMachinePage = lazy(() => import("./pages/TimeMachinePage"));
const FlightRecorder = lazy(() => import("./pages/FlightRecorder"));
const SimulatorPage = lazy(() => import("./pages/SimulatorPage"));
const DnaGraphPage = lazy(() => import("./pages/DnaGraphPage"));
const BugBountyPage = lazy(() => import("./pages/BugBountyPage"));
const DebateArenaPage = lazy(() => import("./pages/DebateArenaPage"));
const SoftwareAssistantPage = lazy(() => import("./pages/SoftwareAssistantPage"));
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
    // Starts on the most recently updated real project (see effect below), not a demo id.
    const [activeGenerationId, setActiveGenerationId] = useState("");

    // Project pages need a real project. With none selected (a new account, or none created yet) they show how
    // to get one instead of querying a placeholder project that does not exist.
    const withProject = (page) => (activeGenerationId ? page : (
        <div className="h-full flex flex-col items-center justify-center gap-3 p-8 text-center text-slate-300">
            <h2 className="text-lg font-bold text-white">No project selected</h2>
            <p className="text-sm text-slate-400 max-w-md">This page works on one of your projects. Create a project, or open one from Projects.</p>
            <div className="flex gap-2">
                <button onClick={() => setView("create")} className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold">New Project</button>
                <button onClick={() => setView("projects")} className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-sm font-semibold">Projects</button>
            </div>
        </div>
    ));
    const [selectedFile, setSelectedFile] = useState(null);
    const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
    const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

    useEffect(() => {
        let cancelled = false;
        fetchProjects({ page: 1, pageSize: 1, sort: "recently_updated" }).then((res) => {
            const latest = res?.projects?.[0];
            if (!cancelled && latest) {
                // The run's generation id when there is one: the folder name is not a generation id.
                setActiveGenerationId((current) => current || latest.latest_generation_id || latest.generation_id);
                setActiveProjectName((current) => current || latest.project_name);
            }
        });
        return () => { cancelled = true; };
    }, []);

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
                    {(view === "multi-agent" || view === "swarm") && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <SwarmPage activeProjectId={activeGenerationId} />
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
                    {view === "verifiable-ai" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <VerifiableAiPage setView={setView} activeProjectId={activeProjectName || activeGenerationId} />
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
                    {view === "ci-pipeline" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            {withProject(<CIPipelineDashboard 
                                projectId={activeProjectName || activeGenerationId} 
                                onBack={() => setView("dashboard")} 
                            />)}
                        </ProtectedRoute>
                    )}
                    {view === "code" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            {withProject(<CodeWorkspace generationId={activeGenerationId} setView={setView} />)}
                        </ProtectedRoute>
                    )}
                    {view === "project-details" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            {withProject(<ProjectDetails generationId={activeGenerationId} setView={setView} />)}
                        </ProtectedRoute>
                    )}
                    {(view === "project-overview" || view === "project-memory") && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <ProjectOverviewPage projectId={activeProjectName || activeGenerationId} setView={setView} setActiveProjectName={setActiveProjectName} setActiveGenerationId={setActiveGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "xray" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            {withProject(<ProjectXRayPage projectId={activeGenerationId || activeProjectName} setView={setView} />)}
                        </ProtectedRoute>
                    )}
                    {view === "metrics" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            {withProject(<QualityCenter generationId={activeGenerationId} setView={setView} />)}
                        </ProtectedRoute>
                    )}
                    {(view === "plugins" || view === "deploy") && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            {withProject(<DeploymentCenter generationId={activeGenerationId} setView={setView} />)}
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
                            {withProject(<ObservabilityPage projectId={activeGenerationId} />)}
                        </ProtectedRoute>
                    )}
                    {view === "evaluations" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <EvaluationCenter />
                        </ProtectedRoute>
                    )}
                    {view === "benchmark-lab" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <BenchmarkLabPage />
                        </ProtectedRoute>
                    )}
                    {view === "chaos-engineer" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <ChaosEngineerPage activeProjectId={activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "security-guardian" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <SecurityGuardianPage activeProjectId={activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "evolution-engine" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <EvolutionEnginePage activeProjectId={activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "time-machine" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <TimeMachinePage activeProjectId={activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "reality-simulator" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <RealitySimulatorPage activeProjectId={activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "execution-guardian" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <ExecutionGuardianPage activeProjectId={activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "integration-engine" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <IntegrationEnginePage activeProjectId={activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "performance-engineer" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <PerformanceEngineerPage activeProjectId={activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "digital-twin" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <DigitalTwinPage activeProjectId={activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "evolution-autopilot" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            <AutopilotEvolutionPage activeProjectId={activeGenerationId} />
                        </ProtectedRoute>
                    )}
                    {view === "autopilot" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            {withProject(<AutopilotDashboard generationId={activeGenerationId} setView={setView} setActiveGenerationId={setActiveGenerationId} />)}
                        </ProtectedRoute>
                    )}
                    {view === "flight-recorder" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            {withProject(<FlightRecorder projectId={activeGenerationId} setView={setView} />)}
                        </ProtectedRoute>
                    )}
                    {view === "simulator" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            {withProject(<SimulatorPage projectId={activeGenerationId} />)}
                        </ProtectedRoute>
                    )}
                    {view === "dna" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            {withProject(<DnaGraphPage projectId={activeGenerationId} />)}
                        </ProtectedRoute>
                    )}
                    {view === "bug-bounty" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            {withProject(<BugBountyPage projectId={activeGenerationId} />)}
                        </ProtectedRoute>
                    )}
                    {view === "debate" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            {withProject(<DebateArenaPage projectId={activeGenerationId} />)}
                        </ProtectedRoute>
                    )}
                    {view === "talk" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            {withProject(<SoftwareAssistantPage projectId={activeGenerationId} />)}
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
                    {view === "monitoring" && <ProtectedRoute onRedirectLogin={() => setView("login")}>{withProject(<MonitoringPage projectId={activeGenerationId} />)}</ProtectedRoute>}
                    {view === "github" && (
                        <ProtectedRoute onRedirectLogin={() => setView("login")}>
                            {withProject(<GitHubDashboardPage projectId={activeGenerationId} />)}
                        </ProtectedRoute>
                    )}
                    {view === "kubernetes" && <ProtectedRoute onRedirectLogin={() => setView("login")}>{withProject(<KubernetesDashboardPage projectId={activeGenerationId} />)}</ProtectedRoute>}
                    {view === "infrastructure" && <ProtectedRoute onRedirectLogin={() => setView("login")}>{withProject(<InfrastructureDashboardPage projectId={activeGenerationId} />)}</ProtectedRoute>}
                    {view === "finops" && <ProtectedRoute onRedirectLogin={() => setView("login")}>{withProject(<FinOpsDashboardPage projectId={activeGenerationId} />)}</ProtectedRoute>}
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
