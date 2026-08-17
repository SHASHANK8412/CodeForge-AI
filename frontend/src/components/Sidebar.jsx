import { useEffect, useMemo, useState } from "react";
import { 
    FaCommentAlt, FaBrain, FaChartBar, FaPlus, FaSearch, FaTrash, 
    FaPen, FaServer, FaHome, FaGlobe, FaBolt, FaCode, FaRocket, 
    FaCog, FaUserCircle, FaSignOutAlt, FaShieldAlt, FaHistory, FaFolderOpen
} from "react-icons/fa";
import { useAuth } from "../auth/useAuth";
import {
    createConversation,
    deleteConversation,
    listConversations,
    renameConversation,
} from "../services/conversationApi";
import { getActiveSessionId, setActiveSessionId } from "../utils/chatStorage";

function Sidebar({ currentView, setView }) {
    const { user, logout } = useAuth();
    const [sessions, setSessions] = useState([]);
    const [activeSessionId, setSidebarActiveSessionId] = useState(() => getActiveSessionId());
    const [searchTerm, setSearchTerm] = useState("");
    const [loading, setLoading] = useState(false);
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [isLabsOpen, setIsLabsOpen] = useState(false);

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
                console.warn("Could not create initial conversation on backend:", err);
                const fallbackId = `session_default`;
                const fallbackConv = { conversation_id: fallbackId, title: "Chat Session 1", message_count: 1 };
                setSessions([fallbackConv]);
                setSidebarActiveSessionId(fallbackId);
                setActiveSessionId(fallbackId);
            }
        } catch (err) {
            console.error("Failed to refresh sessions:", err);
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
            setView("chat");
        } catch (err) {
            console.error("Failed to create new chat session:", err);
            const fallbackId = `session_${Date.now()}`;
            const fallbackConv = { conversation_id: fallbackId, title: "Untitled Conversation" };
            setSidebarActiveSessionId(fallbackId);
            setActiveSessionId(fallbackId);
            setSessions((current) => [fallbackConv, ...current]);
            window.dispatchEvent(new CustomEvent("aiforge:new-chat", { detail: { sessionId: fallbackId } }));
            window.dispatchEvent(new CustomEvent("aiforge:open-session", { detail: { sessionId: fallbackId } }));
            setView("chat");
        }
    };

    const handleOpenSession = (sessionId) => {
        setSidebarActiveSessionId(sessionId);
        setActiveSessionId(sessionId);
        window.dispatchEvent(new CustomEvent("aiforge:open-session", { detail: { sessionId } }));
        setView("chat");
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

    const coreTabs = [
        { key: "dashboard", label: "Dashboard", icon: <FaHome size={14} /> },
        { key: "create", label: "New Project", icon: <FaPlus size={14} /> },
        { key: "project-overview", label: "Project Memory", icon: <FaFolderOpen size={14} /> },
        { key: "code", label: "Workspace", icon: <FaCode size={14} /> },
        { key: "metrics", label: "AI Review", icon: <FaChartBar size={14} /> },
        { key: "observability", label: "DevOps", icon: <FaBrain size={14} /> },
        { key: "deploy", label: "Deployments", icon: <FaRocket size={14} /> },
        { key: "github", label: "GitHub", icon: <FaGlobe size={14} /> },
    ];

    const advancedTabs = [
        { key: "autopilot", label: "Autopilot", icon: <FaBolt size={12} /> },
        { key: "simulator", label: "Simulator", icon: <FaHistory size={12} /> },
        { key: "dna", label: "DNA Graph", icon: <FaBrain size={12} /> },
        { key: "bug-bounty", label: "Bug Hunter", icon: <FaShieldAlt size={12} /> },
        { key: "debate", label: "Debate Arena", icon: <FaCommentAlt size={12} /> },
        { key: "talk", label: "Talk to Code", icon: <FaCommentAlt size={12} /> },
        { key: "flight-recorder", label: "Flight Recorder", icon: <FaHistory size={12} /> },
        { key: "security", label: "Security Center", icon: <FaShieldAlt size={12} /> },
    ];

    return (
        <div 
            className={`flex flex-col h-full bg-[#0F1117] border-r border-[#242833] text-[#9AA1B2] select-none transition-all duration-200 shrink-0 overflow-hidden ${
                isCollapsed ? "w-[68px]" : "w-[260px]"
            }`}
        >
            {/* Header section with brand logo */}
            <div className="p-4 border-b border-[#242833] flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                    <div className="bg-[#8D5CF6] hover:bg-[#7c4ee4] transition p-2 rounded-lg text-white font-black text-sm shrink-0 flex items-center justify-center shadow-lg shadow-violet-500/25">
                        ⚡
                    </div>
                    {!isCollapsed && (
                        <div>
                            <span className="text-sm font-bold tracking-tight text-[#F5F7FA]">AIForge</span>
                            <span className="block text-[9px] text-[#8D5CF6] font-mono tracking-widest uppercase">ENGINEER</span>
                        </div>
                    )}
                </div>
                <button
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    className="text-[#9AA1B2] hover:text-[#F5F7FA] p-1.5 rounded-md hover:bg-[#151821] transition active:scale-95 text-xs font-bold"
                    title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
                >
                    {isCollapsed ? "➔" : "◀"}
                </button>
            </div>

            {/* Quick Actions (e.g. create project / chat) */}
            <div className="p-3 space-y-1">
                <button
                    onClick={() => setView("create")}
                    className={`w-full flex items-center justify-center gap-2 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-[#F5F7FA] rounded-md py-2 px-3 text-xs font-bold transition shadow-md shadow-violet-500/10 active:scale-95`}
                >
                    <FaPlus size={11} /> {!isCollapsed && "New Project"}
                </button>
            </div>

            {/* Navigation Body */}
            <div className="flex-1 min-h-0 overflow-y-auto p-2 space-y-4 custom-scrollbar">
                {/* Core Navigation Items */}
                <div className="space-y-0.5">
                    {coreTabs.map((tab) => {
                        const isActive = currentView === tab.key;
                        return (
                            <button
                                key={tab.key}
                                onClick={() => setView(tab.key)}
                                title={tab.label}
                                className={`w-full flex items-center rounded-md text-xs font-semibold py-2 transition-all relative group ${
                                    isCollapsed ? "justify-center px-2" : "gap-3 px-3"
                                } ${
                                    isActive
                                        ? "bg-[#151821] text-[#F5F7FA] border border-[#242833] shadow-inner"
                                        : "text-[#9AA1B2] hover:text-[#F5F7FA] hover:bg-[#151821]/50"
                                }`}
                            >
                                <span className={isActive ? "text-[#8D5CF6]" : "text-[#9AA1B2]"}>
                                    {tab.icon}
                                </span>
                                {!isCollapsed && <span>{tab.label}</span>}
                                {isCollapsed && (
                                    <div className="absolute left-[64px] bg-[#151821] border border-[#242833] text-[#F5F7FA] text-[10px] py-1 px-2.5 rounded shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 z-50 whitespace-nowrap">
                                        {tab.label}
                                    </div>
                                )}
                            </button>
                        );
                    })}
                </div>

                {/* Collapsible Advanced Lab Features */}
                <div className="border-t border-[#242833] pt-3">
                    {!isCollapsed ? (
                        <button
                            onClick={() => setIsLabsOpen(!isLabsOpen)}
                            className="w-full flex items-center justify-between text-[10px] font-bold text-[#9AA1B2] uppercase tracking-wider px-3 py-1.5 hover:text-[#F5F7FA] transition"
                        >
                            <span>Advanced Labs</span>
                            <span>{isLabsOpen ? "▼" : "▶"}</span>
                        </button>
                    ) : (
                        <div className="border-b border-[#242833] my-1" />
                    )}

                    {(isLabsOpen || isCollapsed) && (
                        <div className="space-y-0.5 mt-1">
                            {advancedTabs.map((tab) => {
                                const isActive = currentView === tab.key;
                                return (
                                    <button
                                        key={tab.key}
                                        onClick={() => setView(tab.key)}
                                        title={tab.label}
                                        className={`w-full flex items-center rounded-md text-xs py-1.5 transition-all relative group ${
                                            isCollapsed ? "justify-center px-2" : "gap-3 px-3"
                                        } ${
                                            isActive
                                                ? "bg-[#151821] text-[#F5F7FA] font-bold border border-[#242833]"
                                                : "text-[#9AA1B2] hover:text-[#F5F7FA] hover:bg-[#151821]/30"
                                        }`}
                                    >
                                        <span className={isActive ? "text-[#8D5CF6]" : "text-[#9AA1B2]"}>
                                            {tab.icon}
                                        </span>
                                        {!isCollapsed && <span>{tab.label}</span>}
                                        {isCollapsed && (
                                            <div className="absolute left-[64px] bg-[#151821] border border-[#242833] text-[#F5F7FA] text-[10px] py-1 px-2.5 rounded shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 z-50 whitespace-nowrap">
                                                {tab.label}
                                            </div>
                                        )}
                                    </button>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* Discussions / Recent Conversations Section */}
                {!isCollapsed && (
                    <div className="pt-3 border-t border-[#242833] space-y-2">
                        <div className="flex items-center justify-between px-3">
                            <span className="text-[10px] font-bold text-[#9AA1B2] uppercase tracking-wider block">
                                Chat History
                            </span>
                            <button 
                                onClick={handleNewChat}
                                className="text-[#8D5CF6] hover:text-[#7c4ee4] text-[10px] font-bold"
                                title="New Chat"
                            >
                                + New
                            </button>
                        </div>
                        <div className="relative mx-1">
                            <span className="absolute inset-y-0 left-0 flex items-center pl-2.5 text-[#9AA1B2] pointer-events-none">
                                <FaSearch size={10} />
                            </span>
                            <input
                                type="search"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                placeholder="Filter chats..."
                                className="w-full bg-[#151821] border border-[#242833] rounded-md pl-7 pr-2.5 py-1 text-[11px] text-[#F5F7FA] placeholder-[#9AA1B2]/50 outline-none focus:border-[#8D5CF6] transition"
                            />
                        </div>

                        <div className="space-y-0.5 pt-1">
                            {loading && sessions.length === 0 ? (
                                <div className="text-[11px] text-[#9AA1B2] italic px-3 py-1.5">Loading sessions...</div>
                            ) : visibleSessions.length === 0 ? (
                                <div className="text-[11px] text-[#9AA1B2] italic px-3 py-1.5">No chats found.</div>
                            ) : (
                                visibleSessions.map((session) => {
                                    const isActive = activeSessionId === session.conversation_id && currentView === "chat";
                                    return (
                                        <div
                                            key={session.conversation_id}
                                            onClick={() => handleOpenSession(session.conversation_id)}
                                            className={`group flex items-center justify-between rounded-md px-3 py-1.5 text-xs transition cursor-pointer ${
                                                isActive
                                                    ? "bg-[#151821] text-[#F5F7FA] border-l-2 border-[#8D5CF6] font-semibold"
                                                    : "text-[#9AA1B2] hover:text-[#F5F7FA] hover:bg-[#151821]/20"
                                            }`}
                                        >
                                            <div className="min-w-0 flex-1 pr-2">
                                                <div className="truncate font-medium flex items-center gap-1.5">
                                                    <span className="truncate">{session.title}</span>
                                                </div>
                                            </div>

                                            {/* Action buttons shown on hover */}
                                            <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleRenameConversation(session.conversation_id, session.title);
                                                    }}
                                                    className="text-[#9AA1B2] hover:text-white transition"
                                                    title="Rename"
                                                >
                                                    <FaPen size={8} />
                                                </button>
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleDeleteConversation(session.conversation_id);
                                                    }}
                                                    className="text-[#9AA1B2] hover:text-red-400 transition"
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

            {/* Bottom settings, settings, and profile controls */}
            <div className="p-3 border-t border-[#242833] bg-[#0F1117] space-y-2.5">
                <button
                    onClick={() => setView("settings")}
                    className={`w-full flex items-center gap-3 rounded-md py-1.5 px-3 text-xs font-semibold text-[#9AA1B2] hover:text-[#F5F7FA] hover:bg-[#151821]/50 transition ${
                        isCollapsed ? "justify-center" : ""
                    }`}
                    title="Settings"
                >
                    <FaCog size={14} />
                    {!isCollapsed && <span>Settings</span>}
                </button>

                {user && (
                    <div className={`flex items-center justify-between border-t border-[#242833] pt-3 ${isCollapsed ? "flex-col gap-2" : ""}`}>
                        <div className="flex items-center gap-2.5 min-w-0">
                            <FaUserCircle size={22} className="text-[#8D5CF6] shrink-0" />
                            {!isCollapsed && (
                                <div className="min-w-0">
                                    <span className="block text-xs font-bold text-[#F5F7FA] truncate">{user.name || "Developer"}</span>
                                    <span className="block text-[10px] text-[#9AA1B2] truncate">{user.email}</span>
                                </div>
                            )}
                        </div>
                        <button
                            onClick={logout}
                            className="text-[#9AA1B2] hover:text-red-400 p-1.5 rounded-md hover:bg-red-500/10 transition active:scale-95 shrink-0"
                            title="Sign Out"
                        >
                            <FaSignOutAlt size={13} />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

export default Sidebar;