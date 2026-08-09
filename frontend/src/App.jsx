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

function App() {
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

    return (
        <MainLayout>
            {/* Unified Sidebar managing the active view */}
            <Sidebar currentView={view} setView={setView} />
            
            {/* Active Workspace Panel */}
            <div className="flex-1 flex flex-col min-w-0 bg-[#0B0F19] overflow-y-auto">
                {view === "landing" && <LandingPage setView={setView} />}
                {view === "create" && <CreateProject setView={setView} onGenerateSuccess={handleGenerateSuccess} />}
                {view === "build" && <GenerationDashboard generationId={activeGenerationId} setView={setView} setActiveProjectName={setActiveProjectName} />}
                {view === "code" && <CodeWorkspace generationId={activeGenerationId} setView={setView} />}
                {view === "dashboard" && <Dashboard setView={setView} />}
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
                {view === "metrics" && <QualityCenter generationId={activeGenerationId} setView={setView} />}
                {(view === "plugins" || view === "deploy") && <DeploymentCenter generationId={activeGenerationId} setView={setView} />}
                {view === "learning" && <LearningDashboard />}
                {view === "f1" && <F1Website />}
            </div>
        </MainLayout>
    );
}






export default App;

