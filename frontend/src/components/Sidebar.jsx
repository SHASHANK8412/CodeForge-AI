import { useEffect, useState } from "react";
import { getActiveSessionId, getChatSessions } from "../utils/chatStorage";

function Sidebar() {
    const [sessions, setSessions] = useState(() => getChatSessions());
    const [activeSessionId, setActiveSessionId] = useState(() => getActiveSessionId());

    const handleNewChat = () => {
        window.dispatchEvent(new Event("aiforge:new-chat"));
    };

    const handleOpenSession = (sessionId) => {
        setActiveSessionId(sessionId);
        window.dispatchEvent(new CustomEvent("aiforge:open-session", { detail: { sessionId } }));
    };

    useEffect(() => {
        const refreshSessions = () => {
            setSessions(getChatSessions());
            setActiveSessionId(getActiveSessionId());
        };

        window.addEventListener("storage", refreshSessions);
        window.addEventListener("aiforge:new-chat", refreshSessions);
        window.addEventListener("aiforge:session-changed", refreshSessions);

        return () => {
            window.removeEventListener("storage", refreshSessions);
            window.removeEventListener("aiforge:new-chat", refreshSessions);
            window.removeEventListener("aiforge:session-changed", refreshSessions);
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

            <div className="mt-6 text-gray-400 text-sm font-semibold uppercase tracking-wide">
                History
            </div>

            <div className="mt-3 space-y-2 overflow-y-auto">
                {sessions.length === 0 ? (
                    <div className="text-sm text-gray-500 italic">No chats yet.</div>
                ) : (
                    sessions.map((session) => (
                        <button
                            key={session.sessionId}
                            onClick={() => handleOpenSession(session.sessionId)}
                            className={`w-full text-left rounded-lg px-3 py-2 transition border ${
                                activeSessionId === session.sessionId
                                    ? "bg-gray-700 border-gray-500 text-white"
                                    : "bg-transparent border-gray-700 text-gray-300 hover:bg-gray-700"
                            }`}
                        >
                            <div className="text-sm font-medium truncate">{session.label}</div>
                            <div className="text-xs text-gray-500">{session.messageCount} messages</div>
                        </button>
                    ))
                )}
            </div>

        </div>
    );
}

export default Sidebar;