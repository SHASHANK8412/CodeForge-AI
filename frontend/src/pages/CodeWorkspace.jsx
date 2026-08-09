import React, { useState, useEffect } from 'react';
import WorkspaceHeader from '../components/workspace/WorkspaceHeader';
import FileExplorer from '../components/workspace/FileExplorer';
import EditorTabs from '../components/workspace/EditorTabs';
import CodeEditor from '../components/workspace/CodeEditor';
import Terminal from '../components/workspace/Terminal';
import AIAssistant from '../components/workspace/AIAssistant';
import ProjectInfo from '../components/workspace/ProjectInfo';
import TestResults from '../components/workspace/TestResults';
import ReviewResults from '../components/workspace/ReviewResults';
import { fetchProjectFiles, runProject, testProject, reviewProject } from '../services/project';

export default function CodeWorkspace({ generationId = 'aiforge-demo', setView }) {
  const [projectData, setProjectData] = useState(null);
  const [files, setFiles] = useState([]);
  const [openFiles, setOpenFiles] = useState([]);
  const [activeFile, setActiveFile] = useState(null);
  const [selectedCode, setSelectedCode] = useState('');

  // Terminal & Execution State
  const [terminalOpen, setTerminalOpen] = useState(true);
  const [terminalOutput, setTerminalOutput] = useState('');
  const [exitCode, setExitCode] = useState(0);
  const [isRunning, setIsRunning] = useState(false);

  // Modals State
  const [testModalData, setTestModalData] = useState(null);
  const [reviewModalData, setReviewModalData] = useState(null);
  const [projectInfoOpen, setProjectInfoOpen] = useState(true);

  useEffect(() => {
    const loadFiles = async () => {
      const data = await fetchProjectFiles(generationId);
      setProjectData(data);
      if (data && data.files && data.files.length > 0) {
        setFiles(data.files);
        const mainFile = data.files.find((f) => f.name === 'App.jsx' || f.name === 'main.py') || data.files[0];
        setOpenFiles([mainFile]);
        setActiveFile(mainFile);
      }
    };

    loadFiles();
  }, [generationId]);

  const handleFileSelect = (file) => {
    if (!openFiles.some((f) => f.path === file.path)) {
      setOpenFiles([...openFiles, file]);
    }
    setActiveFile(file);
  };

  const handleCloseTab = (fileToClose) => {
    const remaining = openFiles.filter((f) => f.path !== fileToClose.path);
    setOpenFiles(remaining);
    if (activeFile?.path === fileToClose.path) {
      setActiveFile(remaining.length > 0 ? remaining[remaining.length - 1] : null);
    }
  };

  const handleBackToGeneration = () => {
    if (setView) {
      setView('build');
    } else {
      window.location.href = `/projects/${generationId}/build`;
    }
  };

  const handleRun = async () => {
    setTerminalOpen(true);
    setIsRunning(true);
    setTerminalOutput(`$ npm install\n$ npm run dev\nStarting dev servers...`);

    const res = await runProject(generationId);
    setIsRunning(false);
    setExitCode(res.exit_code || 0);
    setTerminalOutput(res.stdout || '$ Server started successfully on http://localhost:8000');
  };

  const handleTest = async () => {
    setTerminalOpen(true);
    setTerminalOutput(`$ python -m pytest\nExecuting automated unit & integration tests...`);

    const res = await testProject(generationId);
    setExitCode(res.failed > 0 ? 1 : 0);
    setTerminalOutput(res.output || '48 passed in 0.42s');
    setTestModalData(res);
  };

  const handleReview = async () => {
    const res = await reviewProject(generationId);
    setReviewModalData(res);
  };

  const handleQualityReport = () => {
    if (setView) {
      setView('metrics');
    } else {
      window.location.href = `/projects/${generationId}/quality`;
    }
  };

  const handleDeploy = () => {
    if (setView) {
      setView('plugins');
    } else {
      window.location.href = `/projects/${generationId}/deploy`;
    }
  };

  const handleSelectionAction = (actionType, text) => {
    setSelectedCode(text);
  };

  return (
    <div className="h-screen bg-[#090d16] text-slate-100 font-sans flex flex-col overflow-hidden select-none">
      {/* Workspace Header Navbar */}
      <WorkspaceHeader
        projectName={projectData?.project_name || 'FoodDelivery AI'}
        generationId={generationId}
        onBackToGeneration={handleBackToGeneration}
        onRun={handleRun}
        onTest={handleTest}
        onReview={handleReview}
        onQualityReport={handleQualityReport}
        onDeploy={handleDeploy}
      />

      {/* Main 3-Column Workspace Pane */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* Column 1: File Explorer */}
        <FileExplorer files={files} activeFile={activeFile} onFileSelect={handleFileSelect} />

        {/* Column 2: Editor Tabs, Code Editor & Bottom Terminal */}
        <div className="flex-1 flex flex-col min-w-0 bg-[#0b0f19] border-r border-slate-800/80 overflow-hidden">
          <EditorTabs
            openFiles={openFiles}
            activeFile={activeFile}
            onSelectTab={setActiveFile}
            onCloseTab={handleCloseTab}
          />

          <CodeEditor activeFile={activeFile} onSelectionAction={handleSelectionAction} />

          <Terminal
            outputText={terminalOutput}
            isRunning={isRunning}
            exitCode={exitCode}
            isOpen={terminalOpen}
            onToggle={() => setTerminalOpen(!terminalOpen)}
          />
        </div>

        {/* Column 3: AI Assistant & Project Info */}
        <div className="flex flex-col shrink-0">
          <ProjectInfo
            projectName={projectData?.project_name || 'FoodDelivery AI'}
            qualityScore={96.0}
            testsPassed={48}
            totalTests={48}
            isOpen={projectInfoOpen}
            onToggle={() => setProjectInfoOpen(!projectInfoOpen)}
          />
          <AIAssistant activeFile={activeFile} selectedCode={selectedCode} />
        </div>
      </div>

      {/* Action Modals */}
      <TestResults testData={testModalData} onClose={() => setTestModalData(null)} />
      <ReviewResults reviewData={reviewModalData} onClose={() => setReviewModalData(null)} />
    </div>
  );
}
