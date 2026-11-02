import React, { useState, useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';
import {
  FaCopy,
  FaCheck,
  FaSearch,
  FaTimes,
  FaLightbulb,
  FaWrench,
  FaAlignLeft,
  FaListOl,
  FaSave,
  FaMagic,
  FaBug,
  FaVial,
  FaBook,
  FaBolt
} from 'react-icons/fa';

const getLanguage = (fileName) => {
  if (!fileName) return 'javascript';
  const ext = fileName.split('.').pop().toLowerCase();
  switch (ext) {
    case 'py': return 'python';
    case 'js':
    case 'jsx': return 'javascript';
    case 'ts':
    case 'tsx': return 'typescript';
    case 'sql': return 'sql';
    case 'json': return 'json';
    case 'md': return 'markdown';
    case 'yml':
    case 'yaml': return 'yaml';
    case 'html': return 'html';
    case 'css': return 'css';
    default: return 'plaintext';
  }
};

export default function CodeEditor({
  activeFile,
  targetLine,
  onSelectionAction,
  onUpdateMetadata,
  value,
  onChange,
  onSave
}) {
  const [copied, setCopied] = useState(false);
  const [wordWrap, setWordWrap] = useState(true);
  const [selectedText, setSelectedText] = useState('');
  const [cursorPos, setCursorPos] = useState({ line: 1, col: 1 });
  const editorRef = useRef(null);

  const displayContent = value !== undefined ? value : (activeFile?.content || '');
  const linesCount = displayContent.split('\n').length;
  const fileSize = new Blob([displayContent]).size;
  const language = getLanguage(activeFile?.name || activeFile?.path);

  useEffect(() => {
    if (activeFile && onUpdateMetadata) {
      onUpdateMetadata({
        fileName: activeFile.name || activeFile.path?.split('/').pop(),
        filePath: activeFile.path || '',
        language: language,
        lineCount: linesCount,
        fileSize: fileSize,
        cursorLine: cursorPos.line,
        cursorCol: cursorPos.col,
      });
    }
  }, [activeFile?.path, linesCount, fileSize, cursorPos, onUpdateMetadata, language]);

  // Scroll to target line when specified by problems/diagnostics panel
  useEffect(() => {
    if (targetLine && editorRef.current) {
      const lineNum = parseInt(targetLine, 10);
      if (!isNaN(lineNum)) {
        editorRef.current.revealLineInCenter(lineNum);
        editorRef.current.setPosition({ lineNumber: lineNum, column: 1 });
        editorRef.current.focus();
      }
    }
  }, [targetLine, activeFile?.path]);

  if (!activeFile) {
    return (
      <div className="flex-1 bg-[#0b0f19] flex flex-col items-center justify-center text-slate-500 font-sans text-xs gap-2 select-none">
        <FaListOl className="w-8 h-8 text-slate-700" />
        <span>Select a file from the explorer to open in the editor...</span>
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(displayContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;

    // Custom theme matching AIForge dark styling
    monaco.editor.defineTheme('aiforge-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [],
      colors: {
        'editor.background': '#0F1117',
        'editor.lineHighlightBackground': '#151821/60',
        'editorGutter.background': '#0F1117',
        'editorLineNumber.foreground': '#9AA1B2/50',
        'editorLineNumber.activeForeground': '#8D5CF6',
        'editor.selectionBackground': '#8D5CF6/25',
      }
    });
    monaco.editor.setTheme('aiforge-dark');

    // Track cursor position
    editor.onDidChangeCursorPosition((e) => {
      setCursorPos({
        line: e.position.lineNumber,
        col: e.position.column
      });
    });

    // Track selection changes
    editor.onDidChangeCursorSelection((e) => {
      const selection = editor.getSelection();
      const model = editor.getModel();
      if (selection && model) {
        const text = model.getValueInRange(selection);
        if (text && text.trim().length > 0) {
          setSelectedText(text);
        } else {
          setSelectedText('');
        }
      }
    });

    // Add Ctrl+S / Cmd+S saving shortcut
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      if (onSave) {
        onSave();
      }
    });
  };

  return (
    <div className="flex-1 bg-[#0F1117] flex flex-col min-h-0 min-w-0 relative font-mono text-xs overflow-hidden">
      {/* Editor Toolbar */}
      <div className="bg-[#0F1117] px-3.5 py-1.5 border-b border-[#242833] flex items-center justify-between text-[11px] font-sans text-[#9AA1B2] shrink-0 select-none">
        <div className="flex items-center gap-2 truncate max-w-[50%]">
          <span className="font-mono text-[#F5F7FA] font-semibold truncate">{activeFile.path}</span>
          {targetLine && (
            <span className="bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] px-2 py-0.5 rounded font-mono font-bold animate-pulse">
              Line {targetLine}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => setWordWrap(!wordWrap)}
            className={`flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono transition cursor-pointer ${
              wordWrap ? 'bg-[#8D5CF6]/20 text-[#8D5CF6] border border-[#8D5CF6]/30 font-bold' : 'text-[#9AA1B2] hover:text-[#F5F7FA] hover:bg-[#151821]'
            }`}
            title="Toggle Word Wrap"
          >
            <FaAlignLeft className="w-2.5 h-2.5" />
            <span>Wrap</span>
          </button>

          <span className="uppercase tracking-wider font-mono text-[#8D5CF6] text-[10px] font-bold px-1.5 py-0.5 bg-[#08090D] rounded border border-[#242833]">
            {language}
          </span>

          <span className="text-[10px] font-mono text-slate-500 hidden sm:inline">
            Ln {cursorPos.line}, Col {cursorPos.col}
          </span>

          <button
            onClick={onSave}
            className="flex items-center gap-1 px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-sans text-[10px] font-bold transition cursor-pointer shadow-sm border border-emerald-500/30"
            title="Save file changes (Ctrl+S)"
          >
            <FaSave />
            <span>Save</span>
          </button>

          <button
            onClick={handleCopy}
            className="flex items-center gap-1 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded font-sans text-[10px] font-bold transition cursor-pointer shadow-sm"
          >
            {copied ? <FaCheck className="text-green-300" /> : <FaCopy />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>

      {/* Floating AI Actions Toolbar on Selection */}
      {selectedText && (
        <div className="absolute top-10 left-6 z-30 bg-[#0F1117] border border-[#242833] rounded-xl p-1.5 shadow-2xl flex flex-wrap items-center gap-1.5 text-xs font-sans animate-fade-in backdrop-blur-md">
          <span className="text-[10px] text-[#9AA1B2] px-1.5 font-mono">Selected: {selectedText.length} chars</span>
          
          <button
            onClick={() => onSelectionAction && onSelectionAction('explain', selectedText)}
            className="px-2 py-0.5 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white rounded text-[10px] font-semibold flex items-center gap-1 cursor-pointer transition"
          >
            <FaLightbulb className="w-2.5 h-2.5" /> Explain
          </button>

          <button
            onClick={() => onSelectionAction && onSelectionAction('fix', selectedText)}
            className="px-2 py-0.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-[10px] font-semibold flex items-center gap-1 cursor-pointer transition"
          >
            <FaWrench className="w-2.5 h-2.5" /> Fix
          </button>

          <button
            onClick={() => onSelectionAction && onSelectionAction('refactor', selectedText)}
            className="px-2 py-0.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-[10px] font-semibold flex items-center gap-1 cursor-pointer transition"
          >
            <FaMagic className="w-2.5 h-2.5" /> Refactor
          </button>

          <button
            onClick={() => onSelectionAction && onSelectionAction('tests', selectedText)}
            className="px-2 py-0.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[10px] font-semibold flex items-center gap-1 cursor-pointer transition"
          >
            <FaVial className="w-2.5 h-2.5" /> Tests
          </button>

          <button
            onClick={() => onSelectionAction && onSelectionAction('docs', selectedText)}
            className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-[10px] font-semibold flex items-center gap-1 cursor-pointer transition"
          >
            <FaBook className="w-2.5 h-2.5" /> Docs
          </button>

          <button
            onClick={() => onSelectionAction && onSelectionAction('optimize', selectedText)}
            className="px-2 py-0.5 bg-amber-600 hover:bg-amber-500 text-white rounded text-[10px] font-semibold flex items-center gap-1 cursor-pointer transition"
          >
            <FaBolt className="w-2.5 h-2.5" /> Optimize
          </button>

          <button
            onClick={() => onSelectionAction && onSelectionAction('bugs', selectedText)}
            className="px-2 py-0.5 bg-rose-600 hover:bg-rose-500 text-white rounded text-[10px] font-semibold flex items-center gap-1 cursor-pointer transition"
          >
            <FaBug className="w-2.5 h-2.5" /> Bug
          </button>
        </div>
      )}

      {/* Monaco Editor Container */}
      <div className="flex-1 min-h-0 min-w-0 bg-[#0F1117]">
        <Editor
          height="100%"
          language={language}
          theme="aiforge-dark"
          value={displayContent}
          onChange={(val) => onChange && onChange(val)}
          onMount={handleEditorDidMount}
          options={{
            fontSize: 12,
            fontFamily: 'JetBrains Mono, Consolas, Monaco, "Andale Mono", monospace',
            wordWrap: wordWrap ? 'on' : 'off',
            minimap: { enabled: true },
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
          }}
        />
      </div>
    </div>
  );
}
