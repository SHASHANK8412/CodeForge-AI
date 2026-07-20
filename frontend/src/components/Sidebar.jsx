import { useEffect, useMemo, useState } from "react";
import { FaCommentAlt, FaHammer, FaBrain, FaChartBar, FaPlus, FaSearch, FaTrash, FaPen, FaFolderOpen, FaServer } from "react-icons/fa";
import {
    createConversation,
    deleteConversation,
    listConversations,
    renameConversation,
} from "../services/conversationApi";
import { getActiveSessionId, setActiveSessionId } from "../utils/chatStorage";

function Sidebar({ currentView, setView }) {
    const [sessions, setSessions] = useState([]);
    const [activeSessionId, setSidebarActiveSessionId] = useState(() => getActiveSessionId());
    const [searchTerm, setSearchTerm] = useState("");
    const [loading, setLoading] = useState(false);

    const visibleSessions = useMemo(() => {
        const query = searchTerm.trim().toLowerCase();
        if (!query) {
            return sessions;
        }
        return sessions.filter((session) => session.title.toLowerCase().includes(query));
    }, [searchTerm, sessions]);

    const refreshSessions = async () => {
        setLoading(true);
        try {
            const conversations = await listConversations();
            setSessions(conversations);

            const persistedSessionId = getActiveSessionId();
            const activeConversation = conversations.find((conversation) => conversation.conversation_id === persistedSessionId);

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

            const createdConversation = await createConversation();
            setSessions([createdConversation]);
            setSidebarActiveSessionId(createdConversation.conversation_id);
            setActiveSessionId(createdConversation.conversation_id);
            window.dispatchEvent(new CustomEvent("aiforge:new-chat", { detail: { sessionId: createdConversation.conversation_id } }));
        } finally {
            setLoading(false);
        }
    };

    const handleNewChat = async () => {
        const conversation = await createConversation();
        setSidebarActiveSessionId(conversation.conversation_id);
        setActiveSessionId(conversation.conversation_id);
        setSessions((current) => [conversation, ...current]);
        window.dispatchEvent(new CustomEvent("aiforge:new-chat", { detail: { sessionId: conversation.conversation_id } }));
        window.dispatchEvent(new CustomEvent("aiforge:open-session", { detail: { sessionId: conversation.conversation_id } }));
        setView("chat");
    };

    const handleOpenSession = (sessionId) => {
        setSidebarActiveSessionId(sessionId);
        setActiveSessionId(sessionId);
        window.dispatchEvent(new CustomEvent("aiforge:open-session", { detail: { sessionId } }));
        setView("chat");
    };

    const handleRenameConversation = async (sessionId, currentTitle) => {
        const nextTitle = window.prompt("Rename conversation", currentTitle);
        if (!nextTitle || nextTitle.trim() === currentTitle) {
            return;
        }

        const updatedConversation = await renameConversation(sessionId, nextTitle.trim());
        setSessions((current) =>
            current.map((conversation) =>
                conversation.conversation_id === sessionId ? updatedConversation : conversation,
            ),
        );
    };

    const handleDeleteConversation = async (sessionId) => {
        const shouldDelete = window.confirm("Delete this conversation? This cannot be undone.");
        if (!shouldDelete) {
            return;
        }

        await deleteConversation(sessionId);
        const remainingConversations = sessions.filter((conversation) => conversation.conversation_id !== sessionId);
        setSessions(remainingConversations);

        if (activeSessionId === sessionId) {
            const nextConversation = remainingConversations[0];
            if (nextConversation) {
                handleOpenSession(nextConversation.conversation_id);
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

    // Menu tabs for view toggling
    const tabs = [
        { key: "chat", label: "Chat Workspace", icon: <FaCommentAlt size={14} /> },
        { key: "project", label: "Project Builder", icon: <FaHammer size={14} /> },
        { key: "reflection", label: "Reflection Hub", icon: <FaBrain size={14} /> },
        { key: "metrics", label: "Metrics Board", icon: <FaChartBar size={14} /> },
    ];

    return (
        <div className="w-72 bg-[#0F172A] border-r border-gray-800 flex flex-col h-full text-white select-none">
            {/* Header section */}
            <div className="p-4 border-b border-gray-800 space-y-3">
                <div className="flex items-center gap-2">
                    <div className="bg-[#6366F1] p-1.5 rounded-lg text-white font-extrabold text-sm">
                        AF
                    </div>
                    <div>
                        <h1 className="text-sm font-bold tracking-tight text-white flex items-center gap-1.5">
                            🚀 AIForge
                        </h1>
                        <span className="text-[10px] text-gray-500 font-mono">WORKSPACE</span>
                    </div>
                </div>

                <button
                    onClick={handleNewChat}
                    className="w-full flex items-center justify-center gap-2 bg-[#6366F1] hover:bg-[#5053e1] text-white rounded-lg py-2.5 px-4 text-sm font-semibold transition shadow-md shadow-indigo-500/10 active:scale-95"
                >
                    <FaPlus size={12} /> New Chat
                </button>
            </div>

            {/* Navigation Tabs */}
            <div className="p-3 border-b border-gray-800 space-y-1">
                {tabs.map((tab) => (
                    <button
                        key={tab.key}
                        onClick={() => setView(tab.key)}
                        className={`w-full flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
                            currentView === tab.key
                                ? "bg-gray-800 text-white font-semibold shadow-inner border border-gray-700/50"
                                : "text-gray-400 hover:text-white hover:bg-gray-800/40"
                        }`}
                    >
                        <span className={currentView === tab.key ? "text-[#6366F1]" : ""}>
                            {tab.icon}
                        </span>
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Search and History */}
            <div className="flex-1 flex flex-col min-h-0 p-3">
                <div className="relative mb-3">
                    <span className="absolute inset-y-0 left-0 flex items-center pl-2.5 text-gray-500 pointer-events-none">
                        <FaSearch size={11} />
                    </span>
                    <input
                        type="search"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="Search chats..."
                        className="w-full bg-[#1e293b]/60 border border-gray-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-gray-500 outline-none focus:border-[#6366F1] transition"
                    />
                </div>

                <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider px-2 mb-2">
                    Recent Conversations
                </span>

                <div className="flex-1 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
                    {loading && sessions.length === 0 ? (
                        <div className="text-xs text-gray-500 italic px-2 py-4">Loading history...</div>
                    ) : visibleSessions.length === 0 ? (
                        <div className="text-xs text-gray-500 italic px-2 py-4">No discussions found.</div>
                    ) : (
                        visibleSessions.map((session) => {
                            const isActive = activeSessionId === session.conversation_id && currentView === "chat";
                            return (
                                <div
                                    key={session.conversation_id}
                                    onClick={() => handleOpenSession(session.conversation_id)}
                                    className={`group flex items-center justify-between rounded-lg px-3 py-2 text-xs transition cursor-pointer border ${
                                        isActive
                                            ? "bg-gray-800/80 border-[#6366F1] text-white font-semibold shadow-inner"
                                            : "border-transparent text-gray-400 hover:text-white hover:bg-gray-800/30"
                                    }`}
                                >
                                    <div className="min-w-0 flex-1 pr-2">
                                        <div className="truncate font-medium flex items-center gap-1.5">
                                            <span className="text-indigo-400 flex-shrink-0 text-[10px]">📄</span>
                                            <span className="truncate">{session.title}</span>
                                        </div>
                                        <div className="text-[10px] text-gray-600 truncate mt-0.5">
                                            {session.message_count || 0} messages
                                        </div>
                                    </div>

                                    {/* Action buttons shown on hover */}
                                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleRenameConversation(session.conversation_id, session.title);
                                            }}
                                            className="text-gray-500 hover:text-white transition-colors"
                                            title="Rename Chat"
                                        >
                                            <FaPen size={9} />
                                        </button>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDeleteConversation(session.conversation_id);
                                            }}
                                            className="text-gray-500 hover:text-red-400 transition-colors"
                                            title="Delete Chat"
                                        >
                                            <FaTrash size={9} />
                                        </button>
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>
            </div>

            {/* Bottom settings metadata */}
            <div className="p-4 border-t border-gray-800 bg-[#0B0F19] text-xs text-gray-500 space-y-2">
                <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                        <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                        System Online
                    </span>
                    <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-gray-800 border border-gray-700 text-gray-400">
                        v1.0.0
                    </span>
                </div>
                <div className="space-y-1">
                    <div className="flex items-center gap-1 text-[10px] text-gray-400">
                        <FaServer size={10} className="text-indigo-400" />
                        <span>Model: Gemini 3.5 Flash</span>
                    </div>
                    <div className="text-[10px] text-gray-600 truncate" title="c:\Users\Shashank\OneDrive\Documents\CODEFORGE AI">
                        Dir: CODEFORGE AI
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Sidebar;