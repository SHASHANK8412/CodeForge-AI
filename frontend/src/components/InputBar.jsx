import { useState } from "react";
import { FaPaperPlane, FaBook } from "react-icons/fa";

function InputBar({ onSend, loading }) {
    const [message, setMessage] = useState("");
    const [showTemplates, setShowTemplates] = useState(false);

    const templates = [
        "Generate a CRUD REST API with FastAPI and SQLAlchemy",
        "Create a modular React sidebar layout with dark/light themes",
        "Draft a production docker-compose script with DB and caching",
        "Write full unit tests with pytest assertions and mocks"
    ];

    const handleSend = () => {
        if (!message.trim() || loading) return;
        onSend(message);
        setMessage("");
        setShowTemplates(false);
    };

    const handleTemplateClick = (tpl) => {
        setMessage(tpl);
        setShowTemplates(false);
    };

    // Calculate mock token count (roughly chars/4)
    const tokenCount = Math.round(message.length / 4);

    return (
        <div className="relative w-full bg-[#1E293B] border border-gray-800/80 rounded-xl p-3 shadow-lg flex flex-col gap-2">
            {/* Template Selector Popup */}
            {showTemplates && (
                <div className="absolute bottom-full left-0 mb-2 w-72 bg-[#0F172A] border border-gray-800 rounded-xl p-2 shadow-2xl z-50 animate-fade-in">
                    <div className="text-[10px] font-bold text-gray-500 px-2 py-1 uppercase tracking-wider">
                        Prompt Templates
                    </div>
                    <div className="mt-1 space-y-1">
                        {templates.map((tpl, idx) => (
                            <button
                                key={idx}
                                onClick={() => handleTemplateClick(tpl)}
                                className="w-full text-left text-xs text-gray-300 hover:text-white hover:bg-gray-800 p-2 rounded-lg transition-colors truncate cursor-pointer"
                                title={tpl}
                            >
                                {tpl}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Textarea Input */}
            <textarea
                value={message}
                placeholder="Ask AIForge to write code, design schemas, or test projects..."
                disabled={loading}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                    }
                }}
                rows={2}
                className="w-full bg-transparent text-white placeholder-gray-500 text-sm outline-none resize-none disabled:opacity-60 font-sans"
            />

            {/* Actions Bar */}
            <div className="flex items-center justify-between border-t border-gray-800/50 pt-2 text-xs">
                {/* Left tools */}
                <div className="flex items-center gap-3">
                    <button
                        type="button"
                        onClick={() => setShowTemplates(!showTemplates)}
                        className="flex items-center gap-1.5 text-gray-400 hover:text-[#6366F1] transition-colors py-1 px-2 rounded hover:bg-gray-800/40 cursor-pointer"
                        title="Browse templates"
                    >
                        <FaBook size={11} />
                        <span>/Templates</span>
                    </button>
                    <span className="text-[10px] text-gray-600 font-mono">
                        Tokens: {tokenCount} / 8,192
                    </span>
                </div>

                {/* Right actions */}
                <div className="flex items-center gap-3">
                    <span className="text-[10px] text-gray-600 hidden sm:inline">
                        Enter to Send, Shift+Enter for new line
                    </span>

                    <button
                        onClick={handleSend}
                        disabled={loading || !message.trim()}
                        className="
                            flex
                            items-center
                            justify-center
                            gap-1.5
                            bg-[#6366F1]
                            hover:bg-[#5053e1]
                            disabled:bg-gray-800
                            disabled:text-gray-600
                            disabled:cursor-not-allowed
                            text-white
                            px-4
                            py-1.5
                            rounded-lg
                            font-semibold
                            transition-all
                            cursor-pointer
                            active:scale-95
                        "
                    >
                        {loading ? (
                            <span className="animate-pulse">Thinking...</span>
                        ) : (
                            <>
                                <FaPaperPlane size={10} />
                                <span>Send</span>
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default InputBar;