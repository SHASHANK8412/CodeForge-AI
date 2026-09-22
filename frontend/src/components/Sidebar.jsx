import { useEffect, useMemo, useState } from "react";
import { 
    FaHome, FaCommentAlt, FaFolderOpen, FaBrain, FaBookmark, FaHistory, 
    FaCog, FaPlus, FaSearch, FaTrash, FaPen, FaCode, FaRocket, FaShieldAlt, 
    FaUserCircle, FaSignOutAlt, FaBolt, FaProjectDiagram, FaServer, FaTimes, FaRobot, FaPaintBrush,
    FaTasks, FaChartLine
} from "react-icons/fa";
import { useAuth } from "../auth/useAuth";
import {
    createConversation,
    deleteConversation,
    listConversations,
    renameConversation,
} from "../services/conversationApi";
import { getActiveSessionId, setActiveSessionId } from "../utils/chatStorage";

export default function Sidebar({ 
    currentView, 
    setView, 
    isMobileOpen = false, 
    onCloseMobile 
}) {
    const { user, logout } = useAuth();
    const [sessions, setSessions] = useState([]);
    const [activeSessionId, setSidebarActiveSessionId] = useState(() => getActiveSessionId());
    const [searchTerm, setSearchTerm] = useState("");
    const [loading, setLoading] = useState(false);
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [isSuiteOpen, setIsSuiteOpen] = useState(false);

    const visibleSessions = useMemo(() => {
        const query = searchTerm.trim().toLowerCase();
        if (!query) return sessions;
        return sessions.filter((session) => session.title.toLowerCase().includes(query));
    }, [searchTerm, sessions]);

    const refreshSessions = async () => {
        setLoading(true);
        try {
            const conversations = await listConversations();
            setSessions(conversations);
            const persistedSessionId = getActiveSessionId();
            const activeConversation = conversations.find((c) => c.conversation_id === persistedSessionId);

            if (activeConversation) {
                setSidebarActiveSessionId(activeConversation.conversation_id);
                return;
            }

            if (conversations.length > 0) {
                const nextConversation = conversations[0];
                setSidebarActiveSessionId(nextConversation.conversation_id);
                setActiveSessionId(nextConversation.conversation_id);
                window.dispatchEvent(new CustomEvent("aiforge:open-session", { detail: { sessionId: nextConversation.conversation_id } }));
                return;
            }

            try {
                const createdConversation = await createConversation();
                setSessions([createdConversation]);
                setSidebarActiveSessionId(createdConversation.conversation_id);
                setActiveSessionId(createdConversation.conversation_id);
                window.dispatchEvent(new CustomEvent("aiforge:new-chat", { detail: { sessionId: createdConversation.conversation_id } }));
            } catch (err) {
                const fallbackId = `session_default`;
                const fallbackConv = { conversation_id: fallbackId, title: "Chat Session 1", message_count: 1 };
                setSessions([fallbackConv]);
                setSidebarActiveSessionId(fallbackId);
                setActiveSessionId(fallbackId);
            }
        } catch (err) {
            const fallbackId = `session_default`;
            const fallbackConv = { conversation_id: fallbackId, title: "Chat Session 1", message_count: 1 };
            setSessions([fallbackConv]);
            setSidebarActiveSessionId(fallbackId);
            setActiveSessionId(fallbackId);
        } finally {
            setLoading(false);
        }
    };

    const handleNewChat = async () => {
        try {
            const conversation = await createConversation();
            setSidebarActiveSessionId(conversation.conversation_id);
            setActiveSessionId(conversation.conversation_id);
            setSessions((current) => [conversation, ...current.filter(c => c.conversation_id !== conversation.conversation_id)]);
            window.dispatchEvent(new CustomEvent("aiforge:new-chat", { detail: { sessionId: conversation.conversation_id } }));
            window.dispatchEvent(new CustomEvent("aiforge:open-session", { detail: { sessionId: conversation.conversation_id } }));
            handleNavClick("chat");
        } catch (err) {
            const fallbackId = `session_${Date.now()}`;
            const fallbackConv = { conversation_id: fallbackId, title: "Untitled Conversation" };
            setSidebarActiveSessionId(fallbackId);
            setActiveSessionId(fallbackId);
            setSessions((current) => [fallbackConv, ...current]);
            window.dispatchEvent(new CustomEvent("aiforge:new-chat", { detail: { sessionId: fallbackId } }));
            window.dispatchEvent(new CustomEvent("aiforge:open-session", { detail: { sessionId: fallbackId } }));
            handleNavClick("chat");
        }
    };

    const handleOpenSession = (sessionId) => {
        setSidebarActiveSessionId(sessionId);
        setActiveSessionId(sessionId);
        window.dispatchEvent(new CustomEvent("aiforge:open-session", { detail: { sessionId } }));
        handleNavClick("chat");
    };

    const handleRenameConversation = async (sessionId, currentTitle) => {
        const nextTitle = window.prompt("Rename conversation", currentTitle);
        if (!nextTitle || nextTitle.trim() === currentTitle) return;

        const updatedConversation = await renameConversation(sessionId, nextTitle.trim());
        setSessions((current) =>
            current.map((c) => c.conversation_id === sessionId ? updatedConversation : c)
        );
    };

    const handleDeleteConversation = async (sessionId) => {
        const shouldDelete = window.confirm("Delete this conversation? This cannot be undone.");
        if (!shouldDelete) return;

        await deleteConversation(sessionId);
        const remaining = sessions.filter((c) => c.conversation_id !== sessionId);
        setSessions(remaining);

        if (activeSessionId === sessionId) {
            const nextConv = remaining[0];
            if (nextConv) {
                handleOpenSession(nextConv.conversation_id);
            } else {
                await handleNewChat();
            }
        }
    };

    const handleNavClick = (viewKey) => {
        setView(viewKey);
        if (onCloseMobile) onCloseMobile();
    };

    useEffect(() => {
        refreshSessions();

        const syncActiveSession = (event) => {
            const nextSessionId = event.detail?.sessionId || getActiveSessionId();
            if (nextSessionId) {
                setSidebarActiveSessionId(nextSessionId);
            }
            refreshSessions();
        };

        window.addEventListener("storage", refreshSessions);
        window.addEventListener("aiforge:new-chat", syncActiveSession);
        window.addEventListener("aiforge:open-session", syncActiveSession);
        window.addEventListener("aiforge:session-changed", syncActiveSession);

        return () => {
            window.removeEventListener("storage", refreshSessions);
            window.removeEventListener("aiforge:new-chat", syncActiveSession);
            window.removeEventListener("aiforge:open-session", syncActiveSession);
            window.removeEventListener("aiforge:session-changed", syncActiveSession);
        };
    }, []);

    // Primary Navigation items
    const primaryNavItems = [
        { key: "dashboard", label: "Dashboard", icon: <FaHome size={14} /> },
        { key: "chat", label: "AI Chat", icon: <FaCommentAlt size={14} /> },
        { key: "mission-control", label: "Mission Control", icon: <FaRocket size={14} /> },
        { key: "agents", label: "Agents", icon: <FaRobot size={14} /> },
        { key: "projects", label: "Projects", icon: <FaFolderOpen size={14} /> },
        { key: "canvas", label: "Canvas", icon: <FaPaintBrush size={14} /> },
        { key: "research", label: "Research", icon: <FaSearch size={14} /> },
        { key: "tasks", label: "Tasks", icon: <FaTasks size={14} /> },
        { key: "memory", label: "Memory", icon: <FaBrain size={14} /> },
        { key: "tools", label: "AI Tools", icon: <FaBrain size={14} /> },
        { key: "workflows", label: "Workflows", icon: <FaProjectDiagram size={14} /> },
        { key: "saved", label: "Saved", icon: <FaBookmark size={14} /> },
        { key: "history", label: "History", icon: <FaHistory size={14} /> },
        { key: "analytics", label: "Analytics", icon: <FaChartLine size={14} /> },
        { key: "settings", label: "Settings", icon: <FaCog size={14} /> },
    ];

    // Preserved specialized engineering tools suite
    const engineeringSuiteItems = [
        { key: "execution-validation", label: "Validation Sandbox", icon: <FaShieldAlt size={12} /> },
        { key: "ci-pipeline", label: "CI/CD Pipeline", icon: <FaProjectDiagram size={12} /> },
        { key: "github", label: "GitHub Integration", icon: <FaRocket size={12} /> },
        { key: "code", label: "Code Workspace", icon: <FaCode size={12} /> },
        { key: "autopilot", label: "Autopilot Engine", icon: <FaRocket size={12} /> },
        { key: "xray", label: "Project X-Ray", icon: <FaBrain size={12} /> },
        { key: "dna", label: "DNA Graph", icon: <FaProjectDiagram size={12} /> },
        { key: "debate", label: "Debate Arena", icon: <FaCommentAlt size={12} /> },
        { key: "bug-bounty", label: "Bug Hunter SAST", icon: <FaShieldAlt size={12} /> },
        { key: "metrics", label: "Quality Center", icon: <FaBrain size={12} /> },
        { key: "observability", label: "Observability APM", icon: <FaBolt size={12} /> },
        { key: "deploy", label: "Cloud Deployments", icon: <FaServer size={12} /> },
    ];

    const sidebarContent = (
        <div className="flex flex-col h-full bg-[#0F1117] border-r border-[#242833] text-[#9AA1B2] select-none">
            {/* Header / Brand Logo */}
            <div className="p-4 border-b border-[#242833] flex items-center justify-between">
                <div 
                    onClick={() => handleNavClick("dashboard")}
                    className="flex items-center gap-2.5 cursor-pointer group"
                >
                    <div className="bg-gradient-to-tr from-[#8D5CF6] to-[#6366F1] group-hover:scale-105 transition-transform p-2 rounded-xl text-white font-black text-xs shrink-0 flex items-center justify-center shadow-lg shadow-violet-500/25">
                        ⚡
                    </div>
                    {!isCollapsed && (
                        <div>
                            <span className="text-sm font-extrabold tracking-tight text-white group-hover:text-violet-300 transition-colors">
                                AIForge
                            </span>
                            <span className="block text-[9px] text-[#8D5CF6] font-mono tracking-widest uppercase font-bold">
                                COMMAND CENTER
                            </span>
                        </div>
                    )}
                </div>

                {/* Mobile close button / Desktop collapse toggle */}
                <div className="flex items-center">
                    <button
                        onClick={onCloseMobile}
                        className="md:hidden text-[#9AA1B2] hover:text-white p-1.5 rounded-lg hover:bg-[#151821] transition"
                        title="Close Sidebar"
                    >
                        <FaTimes size={13} />
                    </button>
                    <button
                        onClick={() => setIsCollapsed(!isCollapsed)}
                        className="hidden md:block text-[#9AA1B2] hover:text-white p-1.5 rounded-lg hover:bg-[#151821] transition active:scale-95 text-xs font-bold"
                        title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
                    >
                        {isCollapsed ? "➔" : "◀"}
                    </button>
                </div>
            </div>

            {/* Quick Action: New Project */}
            <div className="p-3">
                <button
                    onClick={() => handleNavClick("create")}
                    className={`w-full flex items-center justify-center gap-2 bg-gradient-to-r from-[#8D5CF6] to-[#6366F1] hover:from-[#7c4ee4] hover:to-[#4f46e5] text-white rounded-xl py-2 px-3 text-xs font-bold transition shadow-md shadow-violet-500/20 active:scale-95 cursor-pointer`}
                >
                    <FaPlus size={10} /> {!isCollapsed && "New Project"}
                </button>
            </div>

            {/* Navigation Body */}
            <div className="flex-1 min-h-0 overflow-y-auto p-2 space-y-4 custom-scrollbar">
                {/* 7 Required Primary Navigation Tabs */}
                <div className="space-y-0.5">
                    {!isCollapsed && (
                        <span className="text-[10px] font-bold text-[#64748B] uppercase tracking-wider px-3 py-1 block">
                            Workspace
                        </span>
                    )}
                    {primaryNavItems.map((tab) => {
                        const isActive = currentView === tab.key;
                        return (
                            <button
                                key={tab.key}
                                onClick={() => handleNavClick(tab.key)}
                                title={tab.label}
                                className={`w-full flex items-center rounded-xl text-xs font-semibold py-2 transition-all relative group cursor-pointer ${
                                    isCollapsed ? "justify-center px-2" : "gap-3 px-3"
                                } ${
                                    isActive
                                        ? "bg-[#8D5CF6]/15 text-white border border-[#8D5CF6]/40 shadow-sm"
                                        : "text-[#9AA1B2] hover:text-white hover:bg-[#151821]"
                                }`}
                            >
                                <span className={isActive ? "text-[#8D5CF6]" : "text-[#9AA1B2] group-hover:text-white"}>
                                    {tab.icon}
                                </span>
                                {!isCollapsed && <span>{tab.label}</span>}
                                {isCollapsed && (
                                    <div className="absolute left-[64px] bg-[#0F1117] border border-[#242833] text-white text-[10px] py-1 px-2.5 rounded-lg shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 z-50 whitespace-nowrap">
                                        {tab.label}
                                    </div>
                                )}
                            </button>
                        );
                    })}
                </div>

                {/* Collapsible AI Engineering Suite */}
                <div className="border-t border-[#242833] pt-3">
                    {!isCollapsed ? (
                        <button
                            onClick={() => setIsSuiteOpen(!isSuiteOpen)}
                            className="w-full flex items-center justify-between text-[10px] font-bold text-[#64748B] uppercase tracking-wider px-3 py-1.5 hover:text-white transition cursor-pointer"
                        >
                            <span>Engineering Suite</span>
                            <span>{isSuiteOpen ? "▼" : "▶"}</span>
                        </button>
                    ) : (
                        <div className="border-b border-[#242833] my-1" />
                    )}

                    {(isSuiteOpen || isCollapsed) && (
                        <div className="space-y-0.5 mt-1">
                            {engineeringSuiteItems.map((tab) => {
                                const isActive = currentView === tab.key;
                                return (
                                    <button
                                        key={tab.key}
                                        onClick={() => handleNavClick(tab.key)}
                                        title={tab.label}
                                        className={`w-full flex items-center rounded-xl text-xs py-1.5 transition-all relative group cursor-pointer ${
                                            isCollapsed ? "justify-center px-2" : "gap-3 px-3"
                                        } ${
                                            isActive
                                                ? "bg-[#151821] text-white font-bold border border-[#242833]"
                                                : "text-[#9AA1B2] hover:text-white hover:bg-[#151821]/50"
                                        }`}
                                    >
                                        <span className={isActive ? "text-[#8D5CF6]" : "text-[#9AA1B2] group-hover:text-white"}>
                                            {tab.icon}
                                        </span>
                                        {!isCollapsed && <span className="text-[11px]">{tab.label}</span>}
                                        {isCollapsed && (
                                            <div className="absolute left-[64px] bg-[#0F1117] border border-[#242833] text-white text-[10px] py-1 px-2.5 rounded-lg shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 z-50 whitespace-nowrap">
                                                {tab.label}
                                            </div>
                                        )}
                                    </button>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* Discussions / Chat History */}
                {!isCollapsed && (
                    <div className="pt-3 border-t border-[#242833] space-y-2">
                        <div className="flex items-center justify-between px-3">
                            <span className="text-[10px] font-bold text-[#64748B] uppercase tracking-wider block">
                                Chat History
                            </span>
                            <button 
                                onClick={handleNewChat}
                                className="text-[#8D5CF6] hover:text-[#a78bfa] text-[10px] font-bold cursor-pointer"
                                title="New Chat"
                            >
                                + New
                            </button>
                        </div>
                        <div className="relative mx-1">
                            <span className="absolute inset-y-0 left-0 flex items-center pl-2.5 text-[#64748B] pointer-events-none">
                                <FaSearch size={10} />
                            </span>
                            <input
                                type="search"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                placeholder="Filter chats..."
                                className="w-full bg-[#151821] border border-[#242833] rounded-xl pl-7 pr-2.5 py-1 text-[11px] text-[#F5F7FA] placeholder-[#64748B] outline-none focus:border-[#8D5CF6] transition"
                            />
                        </div>

                        <div className="space-y-0.5 pt-1 max-h-40 overflow-y-auto custom-scrollbar">
                            {loading && sessions.length === 0 ? (
                                <div className="text-[11px] text-[#64748B] italic px-3 py-1.5">Loading chats...</div>
                            ) : visibleSessions.length === 0 ? (
                                <div className="text-[11px] text-[#64748B] italic px-3 py-1.5">No chats found.</div>
                            ) : (
                                visibleSessions.map((session) => {
                                    const isActive = activeSessionId === session.conversation_id && currentView === "chat";
                                    return (
                                        <div
                                            key={session.conversation_id}
                                            onClick={() => handleOpenSession(session.conversation_id)}
                                            className={`group flex items-center justify-between rounded-xl px-3 py-1.5 text-xs transition cursor-pointer ${
                                                isActive
                                                    ? "bg-[#151821] text-white border-l-2 border-[#8D5CF6] font-semibold"
                                                    : "text-[#9AA1B2] hover:text-white hover:bg-[#151821]/40"
                                            }`}
                                        >
                                            <div className="min-w-0 flex-1 pr-2">
                                                <div className="truncate font-medium flex items-center gap-1.5">
                                                    <span className="truncate text-[11px]">{session.title}</span>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleRenameConversation(session.conversation_id, session.title);
                                                    }}
                                                    className="text-[#64748B] hover:text-white transition"
                                                    title="Rename"
                                                >
                                                    <FaPen size={8} />
                                                </button>
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleDeleteConversation(session.conversation_id);
                                                    }}
                                                    className="text-[#64748B] hover:text-rose-400 transition"
                                                    title="Delete"
                                                >
                                                    <FaTrash size={8} />
                                                </button>
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Bottom profile and sign out */}
            <div className="p-3 border-t border-[#242833] bg-[#0F1117] space-y-2">
                {user && (
                    <div className={`flex items-center justify-between ${isCollapsed ? "flex-col gap-2" : ""}`}>
                        <div className="flex items-center gap-2.5 min-w-0">
                            <div className="w-6 h-6 rounded-lg bg-[#8D5CF6]/20 border border-[#8D5CF6]/40 flex items-center justify-center text-xs font-bold text-violet-300 shrink-0">
                                {(user.name || "D").charAt(0).toUpperCase()}
                            </div>
                            {!isCollapsed && (
                                <div className="min-w-0">
                                    <span className="block text-xs font-bold text-white truncate">{user.name || "Developer"}</span>
                                    <span className="block text-[10px] text-[#64748B] truncate">{user.email}</span>
                                </div>
                            )}
                        </div>
                        <button
                            onClick={logout}
                            className="text-[#64748B] hover:text-rose-400 p-1.5 rounded-lg hover:bg-rose-500/10 transition active:scale-95 shrink-0 cursor-pointer"
                            title="Sign Out"
                        >
                            <FaSignOutAlt size={12} />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );

    return (
        <>
            {/* Desktop Sidebar */}
            <aside
                className={`hidden md:flex flex-col h-full shrink-0 transition-all duration-200 overflow-hidden ${
                    isCollapsed ? "w-[68px]" : "w-[260px]"
                }`}
            >
                {sidebarContent}
            </aside>

            {/* Mobile Drawer Overlay */}
            {isMobileOpen && (
                <div className="fixed inset-0 z-50 md:hidden flex">
                    <div 
                        className="fixed inset-0 bg-black/70 backdrop-blur-sm animate-fade-in"
                        onClick={onCloseMobile}
                    />
                    <aside className="relative w-72 h-full z-50 shadow-2xl animate-fade-in">
                        {sidebarContent}
                    </aside>
                </div>
            )}
        </>
    );
}