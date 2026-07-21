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

function App() {
    const [view, setView] = useState("dashboard");
    const [activeProjectName, setActiveProjectName] = useState("");
    const [selectedFile, setSelectedFile] = useState(null); // { project, path, content }

    const handleFileSelect = (projectName, filePath, content) => {
        setSelectedFile({
            project: projectName,
            path: filePath,
            content: content
        });
        setView("project");
    };

    return (
        <MainLayout>
            {/* Unified Sidebar managing the active view */}
            <Sidebar currentView={view} setView={setView} />
            
            {/* Active Workspace Panel */}
            <div className="flex-1 flex flex-col min-w-0 bg-[#0B0F19]">
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
                {view === "metrics" && <MetricsDashboard />}
                {view === "plugins" && <PluginsDashboard />}
                {view === "learning" && <LearningDashboard />}
            </div>
        </MainLayout>
    );
}

export default App;
