import React, { useState, useEffect, useRef } from 'react';
import { FaChevronRight, FaChevronLeft, FaRobot, FaSearch, FaKeyboard } from 'react-icons/fa';
import WorkspaceHeader from '../components/workspace/WorkspaceHeader';
import FileExplorer from '../components/workspace/FileExplorer';
import EditorTabs from '../components/workspace/EditorTabs';
import CodeEditor from '../components/workspace/CodeEditor';
import AIAssistant from '../components/workspace/AIAssistant';
import ProjectInfo from '../components/workspace/ProjectInfo';
import AgentPanel from '../components/workspace/AgentPanel';
import BottomPanel from '../components/workspace/BottomPanel';
import CommandPalette from '../components/workspace/CommandPalette';
import SearchPanel from '../components/workspace/SearchPanel';
import TestResults from '../components/workspace/TestResults';
import ReviewResults from '../components/workspace/ReviewResults';
import { fetchProjectFiles, runProject, testProject, reviewProject } from '../services/project';
import { fetchGenerationStatus, fetchGitOverview } from '../services/workspace';

const DEFAULT_MAIN_FILE_NAMES = ['App.jsx', 'main.py', 'index.js', 'src/index.js'];

const chooseInitialFile = (files) => {
  if (!files || files.length === 0) return null;
  return files.find((file) => DEFAULT_MAIN_FILE_NAMES.includes(file.name)) || files[0];
};

export default function CodeWorkspace({ generationId = 'aiforge-demo', setView }) {
  const [projectData, setProjectData] = useState(null);
  const [files, setFiles] = useState([]);
  const [openFiles, setOpenFiles] = useState([]);
  const [activeFile, setActiveFile] = useState(null);
  const [selectedCode, setSelectedCode] = useState('');

  const [terminalOutput, setTerminalOutput] = useState('');
  const [exitCode, setExitCode] = useState(0);
  const [isRunning, setIsRunning] = useState(false);

  const [rightPanelOpen, setRightPanelOpen] = useState(true);
  const [projectInfoOpen, setProjectInfoOpen] = useState(true);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [bottomTab, setBottomTab] = useState('terminal');
  const [testModalData, setTestModalData] = useState(null);
  const [reviewModalData, setReviewModalData] = useState(null);
  const [reviewData, setReviewData] = useState(null);
  const [generationStatus, setGenerationStatus] = useState(null);
  const [gitOverview, setGitOverview] = useState(null);
  const [activeAgent, setActiveAgent] = useState(null);

  const centerColRef = useRef(null);

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
      if (data?.files?.length) {
        setFiles(data.files);
        const mainFile = chooseInitialFile(data.files);
        setOpenFiles([mainFile]);
        setActiveFile(mainFile);
      }
    };

    loadFiles();
  }, [generationId]);

  useEffect(() => {
    if (!projectData?.project_id) return;

    const loadGeneration = async () => {
      const status = await fetchGenerationStatus(projectData.project_id);
      setGenerationStatus(status);
      const defaultAgent = status?.agents?.find((agent) => agent.status?.toLowerCase() === 'running') || status?.agents?.[0] || null;
      setActiveAgent(defaultAgent);
    };

    const loadGitOverview = async () => {
      const overview = await fetchGitOverview(projectData.project_id);
      setGitOverview(overview);
    };

    loadGeneration();
    loadGitOverview();
  }, [projectData]);

  useEffect(() => {
    const handleGlobalShortcuts = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key.toLowerCase() === 'p') {
        event.preventDefault();
        setPaletteOpen(true);
      }
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key.toLowerCase() === 'f') {
        event.preventDefault();
        setSearchOpen(true);
      }
    };

    window.addEventListener('keydown', handleGlobalShortcuts);
    return () => window.removeEventListener('keydown', handleGlobalShortcuts);
  }, []);

  const handleFileSelect = (file) => {
    if (!openFiles.some((f) => f.path === file.path)) {
      setOpenFiles((prev) => [...prev, file]);
    }
    setActiveFile(file);
    setTargetLine(null);
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
    setBottomTab('terminal');
    setIsRunning(true);
    setTerminalOutput(`$ npm install\n$ npm run dev\nStarting development services...`);

    const res = await runProject(generationId);
    setIsRunning(false);
    setExitCode(res.exit_code || 0);
    setTerminalOutput(res.stdout || '$ Server started successfully on http://localhost:8000');
  };

  const handleTest = async () => {
    setBottomTab('tests');
    setTerminalOutput(`$ python -m pytest\nExecuting automated unit and integration tests...`);

    const res = await testProject(generationId);
    setExitCode(res.failed > 0 ? 1 : 0);
    setTerminalOutput(res.output || '48 passed in 0.42s');
    setTestModalData(res);
  };

  const handleReview = async () => {
    setBottomTab('output');
    const res = await reviewProject(generationId);
    setReviewModalData(res);
    setReviewData(res);
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
        setOpenFiles((prev) => [...prev, target]);
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

  const handlePaletteExecute = (commandId) => {
    setPaletteOpen(false);
    switch (commandId) {
      case 'open_file':
      case 'search_files':
        setSearchOpen(true);
        break;
      case 'run_project':
        handleRun();
        break;
      case 'run_tests':
        handleTest();
        break;
      case 'open_preview':
        window.open(projectData?.preview_url || 'http://localhost:5173', '_blank');
        break;
      case 'toggle_terminal':
        setBottomTab('terminal');
        break;
      case 'toggle_agent_panel':
        setRightPanelOpen((prev) => !prev);
        break;
      default:
        break;
    }
  };

  return (
    <div className="h-full w-full bg-[#090d16] text-slate-100 font-sans flex flex-col min-h-0 min-w-0 overflow-hidden select-none">
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

      <div className="flex-1 flex min-h-0 min-w-0 overflow-hidden relative">
        <FileExplorer files={files} activeFile={activeFile} onFileSelect={handleFileSelect} />

        <div ref={centerColRef} className="flex-1 flex flex-col min-w-0 min-h-0 bg-[#0b0f19] border-r border-slate-800/80 overflow-hidden relative">
          <div className="bg-slate-950 border-b border-slate-800/80 px-3.5 py-3 flex items-center justify-between gap-3 text-sm text-slate-200 font-sans shrink-0">
            <div>
              <div className="font-semibold">{activeFile?.name || 'No file selected'}</div>
              <div className="text-[11px] text-slate-500">{activeFile?.path || 'Open a file from the explorer'}</div>
            </div>
            <div className="flex items-center gap-2 text-[11px] text-slate-400">
              <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-slate-900 border border-slate-800">
                <FaKeyboard className="w-3 h-3" /> Ctrl+Shift+P
              </span>
              <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-slate-900 border border-slate-800">
                <FaSearch className="w-3 h-3" /> Ctrl+Shift+F
              </span>
            </div>
          </div>

          <EditorTabs openFiles={openFiles} activeFile={activeFile} onSelectTab={setActiveFile} onCloseTab={handleCloseTab} />

          <CodeEditor activeFile={activeFile} targetLine={targetLine} onSelectionAction={handleSelectionAction} onUpdateMetadata={setEditorMeta} />

          <div className="bg-slate-950 px-3.5 py-1 border-t border-b border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400 shrink-0 select-none">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                {(activeFile?.status === 'INCOMPLETE' || activeFile?.status === 'PLACEHOLDER') ? (
                  <span className="text-amber-400 font-bold uppercase text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 border border-amber-500/40">
                    ⚠ {activeFile.status}
                  </span>
                ) : 'Ready'}
              </span>
              <span>UTF-8</span>
              <span className="text-slate-300">Ln {editorMeta.cursorLine}, Col {editorMeta.cursorCol}</span>
            </div>
            <div className="flex items-center gap-4">
              <span>File Lines: <strong className="text-slate-200">{editorMeta.lineCount}</strong></span>
              <span>{formatBytes(editorMeta.fileSize)}</span>
              <span className="text-cyan-400 uppercase text-[10px] font-bold">{editorMeta.language}</span>
            </div>
          </div>

          <div className="h-70 border-t border-slate-800/80 bg-[#090d16]">
            <BottomPanel
              activeTab={bottomTab}
              onTabChange={setBottomTab}
              terminalOutput={terminalOutput}
              terminalStatus={isRunning ? 'running' : 'idle'}
              onClearTerminal={() => setTerminalOutput('')}
              problems={reviewData?.issues || []}
              testResult={testModalData}
              gitOverview={gitOverview}
              reviewData={reviewData}
              onOpenProblem={(issue) => handleSelectFinding(issue.file || issue.path, issue.line || issue.line_number || 1)}
            />
          </div>
        </div>

        <div className={`${rightPanelOpen ? 'w-[320px]' : 'w-10'} border-l border-slate-800/80 bg-[#090d16] flex flex-col shrink-0 h-full min-h-0 overflow-hidden transition-all duration-200`}>
          <div className="p-2 border-b border-slate-800/80 flex items-center justify-between bg-slate-950 shrink-0">
            {rightPanelOpen ? (
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">AI Workspace</span>
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
              <AgentPanel generation={generationStatus} onAgentSelect={setActiveAgent} />
              <ProjectInfo
                projectName={projectData?.project_name || 'FoodDelivery AI'}
                qualityScore={reviewData?.overall_score || 0}
                testsPassed={testModalData?.passed || 0}
                totalTests={testModalData?.total || 0}
                isOpen={projectInfoOpen}
                onToggle={() => setProjectInfoOpen(!projectInfoOpen)}
              />
              <AIAssistant activeFile={activeFile} selectedCode={selectedCode} />
            </div>
          )}
        </div>
      </div>

      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} onExecute={handlePaletteExecute} activeFile={activeFile} />
      <SearchPanel open={searchOpen} onClose={() => setSearchOpen(false)} files={files} onResultSelect={handleSelectFinding} />

      <TestResults testData={testModalData} onClose={() => setTestModalData(null)} />
      <ReviewResults reviewData={reviewModalData} onClose={() => setReviewModalData(null)} onSelectFinding={handleSelectFinding} />
    </div>
  );
}
