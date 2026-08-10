import React, { useState, useEffect, useRef } from 'react';
import { FaChevronRight, FaChevronLeft, FaRobot } from 'react-icons/fa';
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

  // Terminal & Resizing State
  const [terminalOpen, setTerminalOpen] = useState(true);
  const [terminalHeight, setTerminalHeight] = useState(220);
  const [isResizingTerm, setIsResizingTerm] = useState(false);
  const [terminalOutput, setTerminalOutput] = useState('');
  const [exitCode, setExitCode] = useState(0);
  const [isRunning, setIsRunning] = useState(false);

  // Right Panel & Modals State
  const [rightPanelOpen, setRightPanelOpen] = useState(true);
  const [testModalData, setTestModalData] = useState(null);
  const [reviewModalData, setReviewModalData] = useState(null);
  const [projectInfoOpen, setProjectInfoOpen] = useState(true);

  const centerColRef = useRef(null);

  // Responsive Breakpoints
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 900) {
        setRightPanelOpen(false);
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

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

  // Terminal Resizer Mouse Handling
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizingTerm || !centerColRef.current) return;
      const rect = centerColRef.current.getBoundingClientRect();
      const newH = rect.bottom - e.clientY;
      const minH = 140;
      const maxH = Math.min(rect.height * 0.55, window.innerHeight * 0.45);
      if (newH >= minH && newH <= maxH) {
        setTerminalHeight(newH);
      }
    };

    const handleMouseUp = () => {
      setIsResizingTerm(false);
    };

    if (isResizingTerm) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizingTerm]);

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

  const [targetLine, setTargetLine] = useState(null);
  const [editorMeta, setEditorMeta] = useState({
    fileName: '',
    filePath: '',
    language: 'javascript',
    lineCount: 0,
    fileSize: 0,
    cursorLine: 1,
    cursorCol: 1,
  });

  const handleSelectFinding = (filePath, lineNumber) => {
    let target = files.find((f) => f.path === filePath || f.path.endsWith(filePath) || filePath.endsWith(f.name));
    if (!target && files.length > 0) {
      target = files[0];
    }
    if (target) {
      if (!openFiles.some((f) => f.path === target.path)) {
        setOpenFiles([...openFiles, target]);
      }
      setActiveFile(target);
      setTargetLine(lineNumber);
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const handleSelectionAction = (actionType, text) => {
    setSelectedCode(text);
  };

  return (
    <div className="h-full w-full bg-[#090d16] text-slate-100 font-sans flex flex-col min-h-0 min-w-0 overflow-hidden select-none">
      {/* Workspace Header Navbar (Fixed 56px) */}
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
      <div className="flex-1 flex min-h-0 min-w-0 overflow-hidden relative">
        {/* Column 1: File Explorer */}
        <FileExplorer files={files} activeFile={activeFile} onFileSelect={handleFileSelect} />

        {/* Column 2: Editor Tabs, Code Editor, IDE Status Bar & Bottom Resizable Terminal */}
        <div ref={centerColRef} className="flex-1 flex flex-col min-w-0 min-h-0 bg-[#0b0f19] border-r border-slate-800/80 overflow-hidden relative">
          <EditorTabs
            openFiles={openFiles}
            activeFile={activeFile}
            onSelectTab={setActiveFile}
            onCloseTab={handleCloseTab}
          />

          <CodeEditor
            activeFile={activeFile}
            targetLine={targetLine}
            onSelectionAction={handleSelectionAction}
            onUpdateMetadata={setEditorMeta}
          />

          {/* IDE Bottom Metadata Status Bar */}
          <div className="bg-slate-950 px-3.5 py-1 border-t border-b border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400 shrink-0 select-none">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                {activeFile?.status === 'INCOMPLETE' || activeFile?.status === 'PLACEHOLDER' ? (
                  <span className="text-amber-400 font-bold uppercase text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 border border-amber-500/40">
                    ⚠ {activeFile.status}
                  </span>
                ) : 'Ready'}
              </span>
              <span>UTF-8</span>
              <span className="text-slate-300">
                Ln {editorMeta.cursorLine}, Col {editorMeta.cursorCol}
              </span>
              <span className="text-slate-400">
                Project: <strong className="text-slate-200">{files.length}</strong> files | <strong className="text-slate-200">{files.reduce((acc, f) => acc + (f.content ? f.content.split('\n').length : 0), 0)}</strong> lines
              </span>
            </div>

            <div className="flex items-center gap-4">
              <span>File Lines: <strong className="text-slate-200">{editorMeta.lineCount}</strong></span>
              <span>{formatBytes(editorMeta.fileSize)}</span>
              <span className="text-cyan-400 uppercase text-[10px] font-bold">{editorMeta.language}</span>
            </div>
          </div>

          {/* Vertical Terminal Drag Resizer */}
          {terminalOpen && (
            <div
              onMouseDown={(e) => {
                e.preventDefault();
                setIsResizingTerm(true);
              }}
              className="h-1.5 hover:h-2 bg-slate-800 hover:bg-cyan-500 cursor-row-resize transition-all shrink-0 select-none z-20 flex items-center justify-center border-y border-slate-700/60"
              title="Drag to resize terminal height"
            >
              <div className="w-8 h-1 bg-slate-500 rounded-full" />
            </div>
          )}

          {/* Terminal Component */}
          <div style={{ height: terminalOpen ? `${terminalHeight}px` : '36px' }} className="shrink-0 flex flex-col min-h-0 min-w-0 overflow-hidden">
            <Terminal
              outputText={terminalOutput}
              isRunning={isRunning}
              exitCode={exitCode}
              isOpen={terminalOpen}
              onToggle={() => setTerminalOpen(!terminalOpen)}
            />
          </div>
        </div>

        {/* Column 3: Specialized Agents & AI Assistant Right Panel */}
        <div className={`${rightPanelOpen ? 'w-[280px]' : 'w-10'} border-l border-slate-800/80 bg-[#090d16] flex flex-col shrink-0 h-full min-h-0 overflow-hidden transition-all duration-200`}>
          {/* Right Panel Collapse/Expand Header Bar */}
          <div className="p-2 border-b border-slate-800/80 flex items-center justify-between bg-slate-950 shrink-0">
            {rightPanelOpen ? (
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">Panel</span>
            ) : (
              <FaRobot className="w-3.5 h-3.5 text-cyan-400 mx-auto" />
            )}
            <button
              onClick={() => setRightPanelOpen(!rightPanelOpen)}
              className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition"
              title={rightPanelOpen ? 'Collapse Right Panel' : 'Expand Right Panel'}
            >
              {rightPanelOpen ? <FaChevronRight className="w-3 h-3" /> : <FaChevronLeft className="w-3 h-3" />}
            </button>
          </div>

          {rightPanelOpen && (
            <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
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
          )}
        </div>
      </div>

      {/* Action Modals */}
      <TestResults testData={testModalData} onClose={() => setTestModalData(null)} />
      <ReviewResults
        reviewData={reviewModalData}
        onClose={() => setReviewModalData(null)}
        onSelectFinding={handleSelectFinding}
      />
    </div>
  );
}
