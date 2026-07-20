import { useState, useEffect } from "react";
import { FaFolder, FaFolderOpen, FaFile, FaFileCode, FaSync, FaDownload } from "react-icons/fa";
import { fetchProjects, fetchProjectFiles } from "../services/projectApi";

function FileExplorer({ activeProjectName, onFileSelect, onProjectChange }) {
    const [projects, setProjects] = useState([]);
    const [selectedProject, setSelectedProject] = useState(activeProjectName || "");
    const [fileTree, setFileTree] = useState([]);
    const [openFolders, setOpenFolders] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    // Sync selected project with prop from parent
    useEffect(() => {
        if (activeProjectName) {
            setSelectedProject(activeProjectName);
        }
    }, [activeProjectName]);

    // Load available projects on mount
    const loadProjectsList = async () => {
        try {
            const list = await fetchProjects();
            setProjects(list);
            if (list.length > 0 && !selectedProject) {
                setSelectedProject(list[0]);
                if (onProjectChange) onProjectChange(list[0]);
            }
        } catch (err) {
            console.error("Failed to load projects", err);
        }
    };

    useEffect(() => {
        loadProjectsList();
    }, []);

    // Load file tree when selected project changes
    const loadFileTree = async () => {
        if (!selectedProject) {
            setFileTree([]);
            return;
        }

        setLoading(true);
        setError("");
        try {
            const tree = await fetchProjectFiles(selectedProject);
            setFileTree(tree);
        } catch (err) {
            setError("Failed to load files.");
            setFileTree([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadFileTree();
    }, [selectedProject]);

    const toggleFolder = (folderPath) => {
        setOpenFolders((prev) => ({
            ...prev,
            [folderPath]: !prev[folderPath],
        }));
    };

    const handleProjectChange = (e) => {
        const next = e.target.value;
        setSelectedProject(next);
        if (onProjectChange) onProjectChange(next);
    };

    const renderNode = (node) => {
        const isOpen = !!openFolders[node.path];

        if (node.is_dir) {
            return (
                <div key={node.path} className="select-none">
                    <button
                        onClick={() => toggleFolder(node.path)}
                        className="flex items-center gap-2 w-full text-left py-1 px-2 rounded hover:bg-[#2d3748] text-gray-300 transition-colors text-sm font-medium"
                    >
                        <span className="text-[#6366F1]">
                            {isOpen ? <FaFolderOpen size={14} /> : <FaFolder size={14} />}
                        </span>
                        <span className="truncate">{node.name}</span>
                    </button>

                    {isOpen && node.children && (
                        <div className="pl-4 border-l border-gray-700/50 ml-3 mt-0.5 space-y-0.5">
                            {node.children.map((child) => renderNode(child))}
                        </div>
                    )}
                </div>
            );
        }

        // It is a file
        const isCodeFile = /\.(js|jsx|ts|tsx|py|css|html|json|sql|sh|yml|yaml)$/i.test(node.name);

        return (
            <button
                key={node.path}
                onClick={() => onFileSelect(selectedProject, node.path)}
                className="flex items-center gap-2 w-full text-left py-1 px-2 rounded hover:bg-[#2d3748] text-gray-400 hover:text-white transition-colors text-sm pl-6"
            >
                <span className="text-gray-500">
                    {isCodeFile ? <FaFileCode size={12} /> : <FaFile size={12} />}
                </span>
                <span className="truncate">{node.name}</span>
            </button>
        );
    };

    return (
        <div className="flex flex-col h-full bg-[#111827] text-white border-l border-gray-800">
            {/* Top selection bar */}
            <div className="p-4 border-b border-gray-800 space-y-3">
                <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                        Workspace Files
                    </span>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={loadFileTree}
                            disabled={loading || !selectedProject}
                            className="p-1.5 rounded bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
                            title="Refresh file explorer"
                        >
                            <FaSync size={11} className={loading ? "animate-spin" : ""} />
                        </button>
                        {selectedProject && (
                            <a
                                href={`http://127.0.0.1:8000/download-project/${encodeURIComponent(selectedProject)}`}
                                download
                                className="p-1.5 rounded bg-[#6366F1] hover:bg-[#5053e1] text-white transition-colors"
                                title="Download Project ZIP"
                            >
                                <FaDownload size={11} />
                            </a>
                        )}
                    </div>
                </div>

                <div className="space-y-1">
                    <label className="text-xs text-gray-500">Active Project</label>
                    <select
                        value={selectedProject}
                        onChange={handleProjectChange}
                        className="w-full bg-[#1f2937] border border-gray-800 text-sm rounded-lg px-2.5 py-1.5 outline-none focus:border-[#6366F1] text-gray-200"
                    >
                        {projects.length === 0 ? (
                            <option value="">No projects generated yet</option>
                        ) : (
                            projects.map((proj) => (
                                <option key={proj} value={proj}>
                                    {proj}
                                </option>
                            ))
                        )}
                    </select>
                </div>
            </div>

            {/* Tree listing */}
            <div className="flex-1 overflow-y-auto p-4 space-y-1">
                {loading && fileTree.length === 0 ? (
                    <div className="text-sm text-gray-500 italic py-4 text-center">Loading file tree...</div>
                ) : error ? (
                    <div className="text-sm text-red-400 py-4 text-center">{error}</div>
                ) : fileTree.length === 0 ? (
                    <div className="text-sm text-gray-500 italic py-8 text-center px-4">
                        Generate a project or select one to view its file structure.
                    </div>
                ) : (
                    fileTree.map((node) => renderNode(node))
                )}
            </div>
        </div>
    );
}

export default FileExplorer;
