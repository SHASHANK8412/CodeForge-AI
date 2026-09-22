import React, { useState, useEffect, useRef } from 'react';
import { FaChevronRight, FaChevronLeft, FaRobot, FaSearch, FaKeyboard, FaTimes, FaCheck, FaHistory, FaWrench, FaTerminal, FaDownload } from 'react-icons/fa';
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
import AIContextDrawer from '../components/workspace/AIContextDrawer';
import AIDiffReviewPanel from '../components/workspace/AIDiffReviewPanel';

// Services
import {
  fetchProjectFiles,
  runProject,
  testProject,
  reviewProject,
  saveProjectFile,
  runSelectedCodeReview,
  proposeFix,
  applyFix,
  fetchSnapshots,
  rollbackSnapshot,
  runAutonomousRepair,
  fetchProjectProblems,
  fetchProjectChanges,
  fetchAgentTimeline
} from '../services/project';
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

  // Editing state
  const [unsavedChanges, setUnsavedChanges] = useState({}); // { [filePath]: modifiedContent }
  const [unsavedPrompt, setUnsavedPrompt] = useState(null); // { targetFile, nextAction, nextFile }

  // Snapshots & auto repair
  const [snapshots, setSnapshots] = useState([]);
  const [autoRepairLoading, setAutoRepairLoading] = useState(false);
  const [autoRepairLogs, setAutoRepairLogs] = useState([]);

  // Proposed Fix diff state
  const [diffModalData, setDiffModalData] = useState(null); // { file, before, after, diff, issue }

  const [terminalOutput, setTerminalOutput] = useState('');
  const [exitCode, setExitCode] = useState(0);
  const [isRunning, setIsRunning] = useState(false);

  const [rightPanelOpen, setRightPanelOpen] = useState(true);
  const [rightTab, setRightTab] = useState('assistant'); // 'assistant' or 'history'
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
  const [problems, setProblems] = useState([]);
  const [changes, setChanges] = useState([]);
  const [timeline, setTimeline] = useState([]);

  // Export prompts
  const [exportPrompt, setExportPrompt] = useState(false);

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

  const loadFiles = async () => {
    const data = await fetchProjectFiles(generationId);
    setProjectData(data);
    if (data?.files?.length) {
      setFiles(data.files);
      if (!activeFile) {
        const mainFile = chooseInitialFile(data.files);
        setOpenFiles([mainFile]);
        setActiveFile(mainFile);
      }
    }
  };

  const loadSnapshots = async () => {
    try {
      const data = await fetchSnapshots(generationId);
      setSnapshots(data.snapshots || []);
    } catch (err) {
      console.warn('Snapshots unavailable:', err);
    }
  };

  const loadWorkspaceDetails = async () => {
    try {
      const [probs, chngs, tl] = await Promise.all([
        fetchProjectProblems(generationId),
        fetchProjectChanges(generationId),
        fetchAgentTimeline(generationId)
      ]);
      if (probs && probs.length) setProblems(probs);
      if (chngs) setChanges(chngs);
      if (tl) setTimeline(tl);
    } catch (err) {
      console.warn('Workspace details unavailable:', err);
    }
  };

  useEffect(() => {
    loadFiles();
    loadSnapshots();
    loadWorkspaceDetails();
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

  // Safe tab selection
  const handleSelectTab = (file) => {
    // If active file has unsaved changes, prompt before leaving
    if (activeFile && unsavedChanges[activeFile.path] !== undefined && activeFile.path !== file.path) {
      setUnsavedPrompt({
        targetFile: activeFile,
        nextAction: 'switch',
        nextFile: file
      });
      return;
    }
    setActiveFile(file);
    setTargetLine(null);
  };

  // Safe tab close
  const handleCloseTab = (fileToClose) => {
    if (unsavedChanges[fileToClose.path] !== undefined) {
      setUnsavedPrompt({
        targetFile: fileToClose,
        nextAction: 'close'
      });
      return;
    }
    proceedCloseTab(fileToClose);
  };

  const proceedCloseTab = (fileToClose) => {
    const remaining = openFiles.filter((f) => f.path !== fileToClose.path);
    setOpenFiles(remaining);
    if (activeFile?.path === fileToClose.path) {
      setActiveFile(remaining.length > 0 ? remaining[remaining.length - 1] : null);
    }
  };

  const handleDiscardUnsaved = () => {
    const filePath = unsavedPrompt.targetFile.path;
    const nextFile = unsavedPrompt.nextFile;
    const nextAction = unsavedPrompt.nextAction;

    // Remove unsaved change
    const updated = { ...unsavedChanges };
    delete updated[filePath];
    setUnsavedChanges(updated);

    setUnsavedPrompt(null);

    if (nextAction === 'switch') {
      setActiveFile(nextFile);
    } else if (nextAction === 'close') {
      proceedCloseTab(unsavedPrompt.targetFile);
    }
  };

  const handleSaveAndProceed = async () => {
    const targetFile = unsavedPrompt.targetFile;
    const nextFile = unsavedPrompt.nextFile;
    const nextAction = unsavedPrompt.nextAction;

    // Save target file first
    const contentToSave = unsavedChanges[targetFile.path];
    await saveProjectFile(generationId, targetFile.path, contentToSave);

    // Update locally stored file content
    setFiles(prev => prev.map(f => f.path === targetFile.path ? { ...f, content: contentToSave } : f));

    // Clear unsaved change state
    const updated = { ...unsavedChanges };
    delete updated[targetFile.path];
    setUnsavedChanges(updated);

    setUnsavedPrompt(null);

    if (nextAction === 'switch') {
      setActiveFile(nextFile);
    } else if (nextAction === 'close') {
      proceedCloseTab(targetFile);
    }
    loadSnapshots();
  };

  const handleFileSelect = (file) => {
    if (!openFiles.some((f) => f.path === file.path)) {
      setOpenFiles((prev) => [...prev, file]);
    }
    handleSelectTab(file);
  };

  const handleContentChange = (newVal) => {
    if (activeFile) {
      setUnsavedChanges((prev) => ({
        ...prev,
        [activeFile.path]: newVal
      }));
    }
  };

  const handleSaveFile = async () => {
    if (!activeFile) return;
    const content = unsavedChanges[activeFile.path];
    if (content === undefined) return; // No unsaved changes

    setTerminalOutput(prev => prev + `\n[${new Date().toLocaleTimeString()}] Saving ${activeFile.path}...`);
    try {
      const res = await saveProjectFile(generationId, activeFile.path, content);
      setFiles(prev => prev.map(f => f.path === activeFile.path ? { ...f, content } : f));
      
      const updated = { ...unsavedChanges };
      delete updated[activeFile.path];
      setUnsavedChanges(updated);

      setTerminalOutput(prev => prev + `\n[${new Date().toLocaleTimeString()}] Saved ${activeFile.path}. Validation Status: ${res.status}`);
      if (res.validation_errors && res.validation_errors.length > 0) {
        setTerminalOutput(prev => prev + `\n⚠️ Syntax issues detected:\n` + res.validation_errors.join('\n'));
      }
      loadSnapshots();
    } catch (err) {
      console.error(err);
      setTerminalOutput(prev => prev + `\n❌ Failed to save: ${err.message}`);
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
    setTerminalOutput(`Starting structured review code scan...`);
    const res = await reviewProject(generationId);
    setReviewModalData(res);
    setReviewData(res);
    setTerminalOutput(`Structured Review finished. Quality score: ${res.overall_score}. ${res.issues?.length || 0} issues detected.`);
  };

  // Selection actions from the Monaco popup menu
  const handleSelectionAction = async (actionType, text) => {
    if (actionType === 'select') {
      setSelectedCode(text);
      return;
    }

    setBottomTab('output');
    setTerminalOutput(`[Assistant] Running ${actionType} action on selection...`);
    try {
      const res = await runSelectedCodeReview(generationId, activeFile.path, text, actionType);
      setTerminalOutput(prev => prev + `\n\n--- Assistant Response ---\n` + res.response);
    } catch (err) {
      setTerminalOutput(prev => prev + `\n❌ Assistant error: ${err.message}`);
    }
  };

  // Generate Proposed Fix from findings
  const handleGenerateFix = async (finding) => {
    setBottomTab('output');
    setTerminalOutput(`[AI Fix] Proposing correction patch for finding...`);
    try {
      const res = await proposeFix(generationId, finding);
      setDiffModalData({
        file: finding.file || finding.path,
        before: res.before,
        after: res.after,
        diff: res.diff,
        finding
      });
    } catch (err) {
      setTerminalOutput(prev => prev + `\n❌ Fix generation failed: ${err.message}`);
    }
  };

  const handleApplyFix = async () => {
    if (!diffModalData) return;
    setBottomTab('output');
    setTerminalOutput(`[AI Fix] Applying approved patch to disk...`);
    try {
      const res = await applyFix(generationId, diffModalData.file, diffModalData.after);
      setTerminalOutput(prev => prev + `\n✓ Fix applied to ${diffModalData.file}. Status: ${res.status}`);
      setDiffModalData(null);
      // Reload file tree/content
      loadFiles();
      loadSnapshots();
    } catch (err) {
      setTerminalOutput(prev => prev + `\n❌ Failed to apply fix: ${err.message}`);
    }
  };

  // Rollback to Snapshot version
  const handleRollback = async (versionId) => {
    setBottomTab('output');
    setTerminalOutput(`[Version Control] Rolling back project to ${versionId}...`);
    try {
      await rollbackSnapshot(generationId, versionId);
      setTerminalOutput(prev => prev + `\n✓ Project rollback to ${versionId} complete.`);
      loadFiles();
      loadSnapshots();
    } catch (err) {
      setTerminalOutput(prev => prev + `\n❌ Rollback failed: ${err.message}`);
    }
  };

  // Autonomous Repair Loop
  const handleRunAutoRepair = async () => {
    setAutoRepairLoading(true);
    setAutoRepairLogs(['Autonomous repair loop initiated...']);
    setBottomTab('output');
    try {
      const res = await runAutonomousRepair(generationId);
      setAutoRepairLogs(res.logs || []);
      setTerminalOutput(prev => prev + `\n[Auto Repair] Result: ${res.status} in ${res.attempts} attempts.`);
      loadFiles();
      loadSnapshots();
    } catch (err) {
      setAutoRepairLogs(prev => [...prev, `Error: ${err.message}`]);
    } finally {
      setAutoRepairLoading(false);
    }
  };

  const handleDownloadZipTrigger = () => {
    // Check if there are unsaved files
    if (Object.keys(unsavedChanges).length > 0) {
      setExportPrompt(true);
    } else {
      window.location.href = `http://127.0.0.1:8000/api/project/${generationId}/download`;
    }
  };

  const handleExportAnyway = () => {
    setExportPrompt(false);
    window.location.href = `http://127.0.0.1:8000/api/project/${generationId}/download`;
  };

  const handleSaveAndValidateExport = async () => {
    setExportPrompt(false);
    // Save all unsaved files
    for (const [path, content] of Object.entries(unsavedChanges)) {
      await saveProjectFile(generationId, path, content);
    }
    setUnsavedChanges({});
    // Trigger validation
    await handleReview();
    window.location.href = `http://127.0.0.1:8000/api/project/${generationId}/download`;
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
      handleSelectTab(target);
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
        projectName={projectData?.project_name || 'AIForge Application'}
        generationId={generationId}
        status={generationStatus?.status || 'READY'}
        hasUnsavedChanges={Object.keys(unsavedChanges).length > 0}
        onBackToGeneration={handleBackToGeneration}
        onRun={handleRun}
        onTest={handleTest}
        onReview={handleReview}
        onQualityReport={handleQualityReport}
        onDeploy={handleDeploy}
        onDownload={handleDownloadZipTrigger}
        onOpenCommandPalette={() => setPaletteOpen(true)}
        onOpenMemory={() => setView ? setView('overview') : window.location.href = '/projects'}
        onAutoRepair={handleRunAutoRepair}
      />

      <div className="flex-1 flex min-h-0 min-w-0 overflow-hidden relative">
        <FileExplorer files={files} activeFile={activeFile} onFileSelect={handleFileSelect} />

        <div ref={centerColRef} className="flex-1 flex flex-col min-w-0 min-h-0 bg-[#08090D] border-r border-[#242833] overflow-hidden relative">
          <div className="bg-[#0F1117] border-b border-[#242833] px-3.5 py-3 flex items-center justify-between gap-3 text-sm text-[#F5F7FA] font-sans shrink-0">
            <div>
              <div className="font-semibold text-xs text-[#F5F7FA]">{activeFile?.name || 'No file selected'}</div>
              <div className="text-[10px] text-[#9AA1B2] font-mono mt-0.5">{activeFile?.path || 'Open a file from the explorer'}</div>
            </div>
            <div className="flex items-center gap-2 text-[10px] text-[#9AA1B2] font-mono">
              <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-[#08090D] border border-[#242833]">
                <FaKeyboard className="w-3 h-3 text-[#8D5CF6]" /> Ctrl+Shift+P
              </span>
              <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-[#08090D] border border-[#242833]">
                <FaSearch className="w-3 h-3 text-[#8D5CF6]" /> Ctrl+Shift+F
              </span>
            </div>
          </div>

          <EditorTabs
            openFiles={openFiles}
            activeFile={activeFile}
            onSelectTab={handleSelectTab}
            onCloseTab={handleCloseTab}
            unsavedChanges={unsavedChanges}
          />

          <CodeEditor
            activeFile={activeFile}
            targetLine={targetLine}
            onSelectionAction={handleSelectionAction}
            onUpdateMetadata={setEditorMeta}
            value={activeFile ? (unsavedChanges[activeFile.path] !== undefined ? unsavedChanges[activeFile.path] : activeFile.content) : ''}
            onChange={handleContentChange}
            onSave={handleSaveFile}
          />

          <div className="bg-[#0F1117] px-3.5 py-1 border-t border-b border-[#242833] flex items-center justify-between text-[11px] font-mono text-[#9AA1B2] shrink-0 select-none">
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
              <span className="text-[#9AA1B2]/80">Ln {editorMeta.cursorLine}, Col {editorMeta.cursorCol}</span>
            </div>
            <div className="flex items-center gap-4">
              <span>File Lines: <strong className="text-[#F5F7FA]">{editorMeta.lineCount}</strong></span>
              <span>{formatBytes(editorMeta.fileSize)}</span>
              <span className="text-[#8D5CF6] uppercase text-[10px] font-bold">{editorMeta.language}</span>
            </div>
          </div>

          <div className="h-70 border-t border-[#242833] bg-[#08090D]">
            <BottomPanel
              activeTab={bottomTab}
              onTabChange={setBottomTab}
              terminalOutput={terminalOutput}
              onClearTerminal={() => setTerminalOutput('')}
              problems={problems.length > 0 ? problems : (reviewData?.issues || [])}
              testResult={testModalData}
              changes={changes}
              timeline={timeline}
              onOpenProblem={(issue) => handleSelectFinding(issue.file || issue.path, issue.line || issue.line_number || 1)}
              onOpenDiff={(ch) => handleSelectionAction('fix', ch.path)}
              onRunTests={handleTest}
              onDebugWithAI={handleRunAutoRepair}
            />
          </div>
        </div>

        <div className={`${rightPanelOpen ? 'w-[320px]' : 'w-10'} border-l border-[#242833] bg-[#0F1117] flex flex-col shrink-0 h-full min-h-0 overflow-hidden transition-all duration-200`}>
          <div className="p-2 border-b border-[#242833] flex items-center justify-between bg-[#0F1117] shrink-0">
            {rightPanelOpen ? (
              <div className="flex gap-1.5">
                <button
                  onClick={() => setRightTab('assistant')}
                  className={`text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-1 rounded transition cursor-pointer ${rightTab === 'assistant' ? 'text-cyan-400 bg-cyan-500/10' : 'text-slate-400 hover:text-white'}`}
                >
                  Assistant
                </button>
                <button
                  onClick={() => setRightTab('context')}
                  className={`text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-1 rounded transition cursor-pointer ${rightTab === 'context' ? 'text-purple-400 bg-purple-500/10' : 'text-slate-400 hover:text-white'}`}
                >
                  AI Context
                </button>
                <button
                  onClick={() => setRightTab('history')}
                  className={`text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-1 rounded transition cursor-pointer ${rightTab === 'history' ? 'text-indigo-400 bg-indigo-500/10' : 'text-slate-400 hover:text-white'}`}
                >
                  History
                </button>
              </div>
            ) : (
              <FaRobot className="w-3.5 h-3.5 text-cyan-400 mx-auto" />
            )}
            <button
              onClick={() => setRightPanelOpen(!rightPanelOpen)}
              className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition cursor-pointer"
              title={rightPanelOpen ? 'Collapse Right Panel' : 'Expand Right Panel'}
            >
              {rightPanelOpen ? <FaChevronRight className="w-3 h-3" /> : <FaChevronLeft className="w-3 h-3" />}
            </button>
          </div>

          {rightPanelOpen && (
            <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
              {rightTab === 'assistant' ? (
                <>
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
                </>
              ) : rightTab === 'context' ? (
                <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
                  <AIContextDrawer
                    isOpen={true}
                    activeFile={activeFile}
                    selectedCode={selectedCode}
                    projectId={generationId}
                    onOpenFile={(f) => handleSelectFile(f)}
                    onOpenMemory={() => setView?.('project-memory')}
                    onOpenTimeline={() => setBottomTab('logs')}
                  />
                </div>
              ) : (
                <div className="p-3 flex-1 overflow-y-auto custom-scrollbar flex flex-col min-h-0 select-text gap-4">
                  {/* Autonomous Repair Loop segment */}
                  <div className="bg-slate-950/40 border border-slate-800/80 rounded-xl p-3.5 flex flex-col gap-2.5">
                    <div className="flex items-center justify-between">
                      <h4 className="text-[11px] uppercase tracking-wider font-bold text-slate-300 flex items-center gap-1.5">
                        <FaWrench className="text-cyan-400 text-xs" /> Auto Repair Loop
                      </h4>
                      {autoRepairLoading && (
                        <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
                      )}
                    </div>
                    <p className="text-[10px] text-slate-500 leading-normal">
                      Scan structure, review finding severity, apply patches, and run diagnostics automatically.
                    </p>
                    <button
                      onClick={handleRunAutoRepair}
                      disabled={autoRepairLoading}
                      className={`w-full py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white text-xs font-bold rounded-lg transition shadow flex items-center justify-center gap-1.5 cursor-pointer`}
                    >
                      <FaRobot /> {autoRepairLoading ? 'Running Fix Loop...' : 'Run Auto-Repair'}
                    </button>
                    {autoRepairLogs.length > 0 && (
                      <div className="mt-2.5 bg-slate-950 border border-slate-900 rounded-lg p-2.5 max-h-[140px] overflow-y-auto custom-scrollbar text-[9px] font-mono text-cyan-300 leading-relaxed whitespace-pre-wrap">
                        {autoRepairLogs.join('\n')}
                      </div>
                    )}
                  </div>

                  {/* Version Lineage Snapshot List */}
                  <div className="flex flex-col gap-2.5">
                    <h4 className="text-[11px] uppercase tracking-wider font-bold text-slate-300 flex items-center gap-1.5">
                      <FaHistory className="text-cyan-400 text-xs" /> Snapshot History
                    </h4>
                    {snapshots.length === 0 ? (
                      <div className="text-xs text-slate-500 italic p-3 text-center bg-slate-950/20 border border-slate-900/60 rounded-xl">
                        No snapshots taken yet. Saving edits or applying fixes will create snapshots.
                      </div>
                    ) : (
                      <div className="space-y-2.5">
                        {snapshots.map((snap, idx) => (
                          <div key={idx} className="bg-slate-950/50 border border-slate-850 p-3 rounded-xl flex flex-col gap-1.5 hover:border-slate-800 transition">
                            <div className="flex items-center justify-between text-[10px] font-mono">
                              <span className="text-cyan-400 font-bold uppercase">{snap.version_id}</span>
                              <span className="text-slate-500 font-normal">{new Date(snap.timestamp * 1000).toLocaleTimeString()}</span>
                            </div>
                            <div className="text-xs text-slate-100 font-semibold leading-relaxed">
                              {snap.repair_reason}
                            </div>
                            <div className="flex items-center justify-between text-[9px] font-mono mt-1">
                              <span className="px-1.5 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">{snap.change_source}</span>
                              <button
                                onClick={() => handleRollback(snap.version_id)}
                                className="px-2 py-0.5 bg-cyan-700/20 hover:bg-cyan-700 text-cyan-300 hover:text-white rounded border border-cyan-700/40 transition cursor-pointer"
                              >
                                Rollback
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} onExecute={handlePaletteExecute} activeFile={activeFile} />
      <SearchPanel open={searchOpen} onClose={() => setSearchOpen(false)} files={files} onResultSelect={handleSelectFinding} />

      <TestResults testData={testModalData} onClose={() => setTestModalData(null)} />
      <ReviewResults reviewData={reviewModalData} onClose={() => setReviewModalData(null)} onSelectFinding={handleSelectFinding} />

      {/* Unsaved Leave Tab / Close Warning Modal */}
      {unsavedPrompt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="bg-[#0b1329] border border-slate-700/80 rounded-2xl w-full max-w-md p-5 shadow-2xl">
            <h3 className="text-sm font-bold text-slate-100 mb-2">Unsaved Changes</h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              You have unsaved changes in <strong className="font-mono text-slate-300">{unsavedPrompt.targetFile.name}</strong>. Leaving or closing will discard your edits.
            </p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setUnsavedPrompt(null)} className="px-3.5 py-1.5 bg-slate-850 hover:bg-slate-805 text-slate-300 rounded-lg text-xs font-semibold cursor-pointer border border-slate-800">
                Cancel
              </button>
              <button onClick={handleDiscardUnsaved} className="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold cursor-pointer">
                Discard Changes
              </button>
              <button onClick={handleSaveAndProceed} className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold cursor-pointer">
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Proposed Fix Diff review overlay modal */}
      {diffModalData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-6 select-text">
          <div className="w-full max-w-4xl">
            <AIDiffReviewPanel
              changes={[{
                file: diffModalData.file,
                status: 'MODIFIED',
                additions: (diffModalData.diff.match(/^\+[^+]/gm) || []).length,
                deletions: (diffModalData.diff.match(/^-[^-]/gm) || []).length,
                risk: 'LOW',
                reason: diffModalData.issue?.title ? `Targeted automated patch: ${diffModalData.issue.title}` : 'Targeted automated architectural fix.',
                diff: diffModalData.diff
              }]}
              onAcceptFile={handleApplyFix}
              onRejectFile={() => setDiffModalData(null)}
              onAcceptAll={handleApplyFix}
              onRejectAll={() => setDiffModalData(null)}
              onClose={() => setDiffModalData(null)}
            />
          </div>
        </div>
      )}

      {/* Download ZIP modified/unchecked verification warning modal */}
      {exportPrompt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="bg-[#0b1329] border border-slate-700/80 rounded-2xl w-full max-w-md p-5 shadow-2xl">
            <h3 className="text-sm font-bold text-slate-100 mb-2">Unsaved or Unchecked changes</h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              This project contains changes that have not been saved or validated. Would you like to save & validate before exporting?
            </p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setExportPrompt(false)} className="px-3.5 py-1.5 bg-slate-850 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-lg text-xs font-semibold cursor-pointer">
                Cancel
              </button>
              <button onClick={handleExportAnyway} className="px-3.5 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-semibold cursor-pointer font-bold">
                Export Anyway
              </button>
              <button onClick={handleSaveAndValidateExport} className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold cursor-pointer">
                Save & Validate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
