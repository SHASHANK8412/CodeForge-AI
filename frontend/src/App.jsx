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
import LandingPage from "./pages/LandingPage";
import CreateProject from "./pages/CreateProject";
import GenerationDashboard from "./pages/GenerationDashboard";
import CodeWorkspace from "./pages/CodeWorkspace";
import QualityCenter from "./pages/QualityCenter";
import DeploymentCenter from "./pages/DeploymentCenter";
import ProjectDetails from "./pages/ProjectDetails";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Settings from "./pages/Settings";
import ApiKeys from "./pages/ApiKeys";
import ObservabilityDashboard from "./pages/ObservabilityDashboard";
import EvaluationCenter from "./pages/EvaluationCenter";
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
            <div className="flex-1 flex flex-col min-w-0 bg-[#0B0F19] overflow-y-auto">
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
                        <ObservabilityDashboard />
                    </ProtectedRoute>
                )}
                {view === "evaluations" && (
                    <ProtectedRoute onRedirectLogin={() => setView("login")}>
                        <EvaluationCenter />
                    </ProtectedRoute>
                )}


                {/* Additional views */}
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


