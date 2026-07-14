import { useEffect, useMemo, useState } from "react";
import {
    createConversation,
    deleteConversation,
    listConversations,
    renameConversation,
} from "../services/conversationApi";
import { getActiveSessionId, setActiveSessionId } from "../utils/chatStorage";

function Sidebar() {
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
    };

    const handleOpenSession = (sessionId) => {
        setSidebarActiveSessionId(sessionId);
        setActiveSessionId(sessionId);
        window.dispatchEvent(new CustomEvent("aiforge:open-session", { detail: { sessionId } }));
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

    return (
        <div className="w-64 bg-[#202123] p-4 flex flex-col">

            <button
                onClick={handleNewChat}
                className="
                    border
                    border-gray-600
                    rounded-lg
                    p-3
                    hover:bg-gray-700
                    transition
                "
            >
                + New Chat
            </button>

            <input
                type="search"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search conversations"
                className="mt-4 w-full rounded-lg border border-gray-700 bg-[#343541] px-3 py-2 text-sm text-white outline-none placeholder:text-gray-500"
            />

            <div className="mt-6 text-gray-400 text-sm font-semibold uppercase tracking-wide">
                History
            </div>

            <div className="mt-3 space-y-2 overflow-y-auto flex-1">
                {loading ? (
                    <div className="text-sm text-gray-500 italic">Loading conversations...</div>
                ) : visibleSessions.length === 0 ? (
                    <div className="text-sm text-gray-500 italic">No conversations yet.</div>
                ) : (
                    visibleSessions.map((session) => (
                        <button
                            key={session.conversation_id}
                            onClick={() => handleOpenSession(session.conversation_id)}
                            className={`w-full text-left rounded-lg px-3 py-2 transition border ${
                                activeSessionId === session.conversation_id
                                    ? "bg-gray-700 border-gray-500 text-white"
                                    : "bg-transparent border-gray-700 text-gray-300 hover:bg-gray-700"
                            }`}
                        >
                            <div className="flex items-start justify-between gap-2">
                                <div className="min-w-0 flex-1">
                                    <div className="text-sm font-medium truncate">{session.title}</div>
                                    <div className="text-xs text-gray-500">{session.message_count} messages</div>
                                </div>

                                <div className="flex gap-2 text-xs text-gray-400">
                                    <span
                                        onClick={(event) => {
                                            event.stopPropagation();
                                            handleRenameConversation(session.conversation_id, session.title);
                                        }}
                                        className="cursor-pointer hover:text-white"
                                    >
                                        Rename
                                    </span>
                                    <span
                                        onClick={(event) => {
                                            event.stopPropagation();
                                            handleDeleteConversation(session.conversation_id);
                                        }}
                                        className="cursor-pointer hover:text-red-300"
                                    >
                                        Delete
                                    </span>
                                </div>
                            </div>
                        </button>
                    ))
                )}
            </div>

        </div>
    );
}

export default Sidebar;