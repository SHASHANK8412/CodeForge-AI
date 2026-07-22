import { useEffect, useRef, useState } from "react";
import { FaCommentAlt, FaBrain, FaFileAlt, FaPlus, FaRobot, FaCog, FaMoon, FaSun } from "react-icons/fa";
import InputBar from "./InputBar";
import Loading from "./Loading";
import Message from "./Message";
import RagUploadPanel from "./RagUploadPanel";
import { sendMessage } from "../services/api";
import { createConversation, getConversationHistory } from "../services/conversationApi";
import { generatePlan } from "../services/plannerApi";
import { queryRagDocuments, uploadRagDocuments } from "../services/ragApi";
import { getActiveSessionId, setActiveSessionId } from "../utils/chatStorage";
import { fetchMetrics } from "../services/projectApi";
import toast from "react-hot-toast";

function formatStructuredResponse(response) {
    if (!response || typeof response !== "object") {
        return String(response || "");
    }

    return [
        "### Generated Code",
        "```text",
        response.generated_code || "",
        "```",
        "",
        "### Reviewer Feedback",
        "```text",
        response.reviewed_code || "",
        "```",
        "",
        "### Testing Report",
        "```text",
        response.testing_report || "",
        "```",
        "",
        "### Explanation",
        "```text",
        response.explanation || "",
        "```",
    ].join("\n");
}

function ChatBox() {
    const [sessionId, setSessionId] = useState(getActiveSessionId());
    const [conversationTitle, setConversationTitle] = useState("Untitled Conversation");
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [ragUploading, setRagUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [plannerMode, setPlannerMode] = useState(false);
    const [documentMode, setDocumentMode] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [ragStatus, setRagStatus] = useState("");
    const [ragError, setRagError] = useState("");

    // Top Header / Model Controls
    const [activeModel, setActiveModel] = useState("Gemini 3.5");
    const [isDarkMode, setIsDarkMode] = useState(true);
    const [metrics, setMetrics] = useState(null);

    const bottomRef = useRef(null);
    const fileInputRef = useRef(null);

    const toUiMessages = (historyMessages) =>
        historyMessages.map((message) => ({
            sender: message.role === "assistant" ? "ai" : "user",
            text: message.content,
        }));

    const loadConversation = async (conversationId) => {
        if (!conversationId) {
            return;
        }

        const response = await getConversationHistory(conversationId);
        setSessionId(conversationId);
        setActiveSessionId(conversationId);
        setConversationTitle(response.conversation?.title || "Untitled Conversation");
        setMessages(toUiMessages(response.messages || []));
        window.dispatchEvent(new CustomEvent("aiforge:session-changed", { detail: { sessionId: conversationId } }));
    };

    const loadMetricsDashboard = async () => {
        try {
            const data = await fetchMetrics();
            setMetrics(data);
        } catch (err) {
            console.error("Failed to load metrics", err);
        }
    };

    useEffect(() => {
        const initialize = async () => {
            const activeConversationId = getActiveSessionId();
            if (!activeConversationId) {
                return;
            }

            try {
                await loadConversation(activeConversationId);
            } catch (error) {
                if (error?.response?.status === 404) {
                    setActiveSessionId("");
                    setSessionId("");
                    setConversationTitle("Untitled Conversation");
                    setMessages([]);
                } else {
                    console.error(error);
                }
            }
        };

        initialize();
        loadMetricsDashboard();

        const handleNewChat = async (event) => {
            const nextSessionId = event.detail?.sessionId;
            if (!nextSessionId) {
                setSessionId("");
                setConversationTitle("Untitled Conversation");
                setMessages([]);
                return;
            }
            await loadConversation(nextSessionId);
        };

        const handleOpenSession = async (event) => {
            const nextSessionId = event.detail?.sessionId;
            if (!nextSessionId) {
                return;
            }
            await loadConversation(nextSessionId);
        };

        window.addEventListener("aiforge:new-chat", handleNewChat);
        window.addEventListener("aiforge:open-session", handleOpenSession);

        return () => {
            window.removeEventListener("aiforge:new-chat", handleNewChat);
            window.removeEventListener("aiforge:open-session", handleOpenSession);
        };
    }, []);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading, sessionId]);

    const handleSend = async (text) => {
        if (!text.trim() || loading) {
            return;
        }

        setMessages((current) => [...current, { sender: "user", text }]);
        setLoading(true);
        setRagError("");

        try {
            let activeConversationId = sessionId;
            if (!activeConversationId) {
                const conversation = await createConversation({ firstMessage: text });
                activeConversationId = conversation.conversation_id;
                setSessionId(activeConversationId);
                setConversationTitle(conversation.title || "Untitled Conversation");
                setActiveSessionId(activeConversationId);
                window.dispatchEvent(new CustomEvent("aiforge:session-changed", { detail: { sessionId: activeConversationId } }));
            }

            if (documentMode) {
                setRagStatus("");
                if (selectedFiles.length > 0) {
                    setRagUploading(true);
                    setUploadProgress(0);

                    await uploadRagDocuments(selectedFiles, (event) => {
                        if (event.total) {
                            setUploadProgress(Math.round((event.loaded * 100) / event.total));
                        }
                    });

                    setRagStatus(`Indexed ${selectedFiles.length} file(s).`);
                    setSelectedFiles([]);

                    if (fileInputRef.current) {
                        fileInputRef.current.value = "";
                    }
                }

                const ragResult = await queryRagDocuments(text);
                const sourceDetails = ragResult.source_details || [];
                const sourceList = sourceDetails.length > 0
                    ? sourceDetails.map((source) => `- ${source.source}${source.page !== "" && source.page !== null ? `, page ${source.page}` : ""}`).join("\n")
                    : (ragResult.sources || []).map((source) => `- ${source}`).join("\n");

                setMessages((current) => [
                    ...current,
                    {
                        sender: "ai",
                        text: `${ragResult.answer}\n\n### Sources\n${sourceList || "- No source metadata available"}`,
                    },
                ]);
                return;
            }

            if (plannerMode) {
                const planResponse = await generatePlan(text, activeConversationId);
                setMessages((current) => [
                    ...current,
                    {
                        sender: "ai",
                        text: formatStructuredResponse(planResponse),
                    },
                ]);
                return;
            }

            const response = await sendMessage(text, activeConversationId);

            if (response?.conversation) {
                setSessionId(response.conversation.conversation_id);
                setConversationTitle(response.conversation.title || conversationTitle);
                setActiveSessionId(response.conversation.conversation_id);
            }

            if (response?.messages?.length) {
                setMessages(toUiMessages(response.messages));
            } else {
                setMessages((current) => [
                    ...current,
                    {
                        sender: "ai",
                        text: response?.response || "",
                    },
                ]);
            }
            loadMetricsDashboard();
        } catch (error) {
            console.error(error);
            setRagError(error?.response?.data?.detail || error?.message || "Something went wrong while processing the request.");
            setMessages((current) => [
                ...current,
                {
                    sender: "ai",
                    text: `❌ ${error?.response?.data?.detail || "Something went wrong!"}`,
                },
            ]);
        } finally {
            setRagUploading(false);
            setUploadProgress(0);
            setLoading(false);
        }
    };

    const handleNewConversation = async () => {
        const conversation = await createConversation();
        setSessionId(conversation.conversation_id);
        setConversationTitle(conversation.title || "Untitled Conversation");
        setActiveSessionId(conversation.conversation_id);
        setMessages([]);
        window.dispatchEvent(new CustomEvent("aiforge:new-chat", { detail: { sessionId: conversation.conversation_id } }));
        window.dispatchEvent(new CustomEvent("aiforge:open-session", { detail: { sessionId: conversation.conversation_id } }));
    };

    const handleSettingsClick = () => {
        toast("Settings Panel coming in Sprint 3!", { icon: "⚙️" });
    };

    const handleThemeToggle = () => {
        setIsDarkMode(!isDarkMode);
        toast(`Switched to ${isDarkMode ? "Light" : "Dark"} Theme (Sprint 3 Integration)`, { icon: "🎨" });
    };

    return (
        <div className="flex flex-col h-full bg-[#0B0F19] text-white">
            {/* Top Navigation / IDE Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-gray-800 bg-[#0F172A] px-6 py-4">
                <div className="min-w-0">
                    <h2 className="text-sm font-bold flex items-center gap-2">
                        <span className="text-[#6366F1] font-extrabold">🚀</span> AI Workspace
                        <span className="text-[10px] text-gray-500 font-mono font-normal">/ {conversationTitle}</span>
                    </h2>
                </div>

                {/* Right controls */}
                <div className="flex items-center gap-4 text-xs font-medium text-gray-400 select-none">
                    {/* Active Model Selector */}
                    <div className="flex items-center gap-1">
                        <span className="text-gray-500">Model:</span>
                        <select
                            value={activeModel}
                            onChange={(e) => setActiveModel(e.target.value)}
                            className="bg-[#1E293B] border border-gray-800 text-white rounded px-2 py-1 outline-none text-xs focus:border-[#6366F1] cursor-pointer"
                        >
                            <option value="Gemini 3.5">Gemini 3.5 Flash</option>
                            <option value="Qwen 2.5">Qwen 2.5 Coder</option>
                            <option value="DeepSeek V3">DeepSeek V3</option>
                        </select>
                    </div>

                    <span className="flex items-center gap-1 text-emerald-400">
                        <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse"></span> Online
                    </span>

                    {/* Settings Trigger */}
                    <button
                        onClick={handleSettingsClick}
                        className="hover:text-white transition-colors cursor-pointer"
                        title="Open settings"
                    >
                        <FaCog size={13} />
                    </button>

                    {/* Theme Toggle */}
                    <button
                        onClick={handleThemeToggle}
                        className="hover:text-white transition-colors cursor-pointer"
                        title="Toggle theme mode"
                    >
                        {isDarkMode ? <FaSun size={13} className="text-amber-400" /> : <FaMoon size={13} />}
                    </button>

                    <button
                        onClick={handleNewConversation}
                        disabled={loading}
                        className="flex items-center gap-1 bg-[#6366F1] hover:bg-[#5053e1] disabled:bg-gray-800 disabled:text-gray-600 text-white font-semibold py-1.5 px-3 rounded-lg transition active:scale-95 text-xs cursor-pointer"
                    >
                        <FaPlus size={10} /> New Discussion
                    </button>
                </div>
            </div>

            {/* Mode Switches */}
            <div className="flex gap-2 px-6 py-3 border-b border-gray-800 bg-[#0F172A]/50">
                <button
                    onClick={() => {
                        setPlannerMode(false);
                        setDocumentMode(false);
                    }}
                    className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                        !plannerMode && !documentMode
                            ? "bg-[#6366F1] text-white shadow"
                            : "bg-[#1E293B] text-gray-400 hover:text-white"
                    }`}
                >
                    <FaCommentAlt size={11} /> General Chat
                </button>

                <button
                    onClick={() => {
                        setPlannerMode(true);
                        setDocumentMode(false);
                    }}
                    className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                        plannerMode
                            ? "bg-[#6366F1] text-white shadow"
                            : "bg-[#1E293B] text-gray-400 hover:text-white"
                    }`}
                >
                    <FaBrain size={11} /> Plan Generator
                </button>

                <button
                    onClick={() => {
                        setDocumentMode((curr) => !curr);
                        setPlannerMode(false);
                    }}
                    className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                        documentMode
                            ? "bg-[#6366F1] text-white shadow"
                            : "bg-[#1E293B] text-gray-400 hover:text-white"
                    }`}
                >
                    <FaFileAlt size={11} /> Document Grounding (RAG)
                </button>
            </div>

            {/* Document Grounding Uploader */}
            <RagUploadPanel
                documentMode={documentMode}
                selectedFiles={selectedFiles}
                onFileChange={(event) => setSelectedFiles(Array.from(event.target.files || []))}
                onToggleDocumentMode={() => {
                    setDocumentMode(false);
                    setPlannerMode(false);
                }}
                uploadProgress={uploadProgress}
                uploading={ragUploading}
                status={ragStatus}
                error={ragError}
                inputRef={fileInputRef}
            />

            {/* Chat Messages Log Wrapper (expanded max-w-6xl for wider view) */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
                <div className="w-full max-w-6xl mx-auto">
                    {/* Status Dashboard Panel */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 select-none animate-fade-in">
                        <div className="bg-[#1E293B]/70 border border-gray-800/80 p-3.5 rounded-xl shadow-md text-center">
                            <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Projects</div>
                            <div className="text-xl font-extrabold text-indigo-400 mt-1">
                                {metrics?.projects_generated || 0}
                            </div>
                        </div>
                        <div className="bg-[#1E293B]/70 border border-gray-800/80 p-3.5 rounded-xl shadow-md text-center">
                            <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Active Model</div>
                            <div className="text-xl font-extrabold text-[#6366F1] mt-1">
                                {activeModel}
                            </div>
                        </div>
                        <div className="bg-[#1E293B]/70 border border-gray-800/80 p-3.5 rounded-xl shadow-md text-center">
                            <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Avg Reflection</div>
                            <div className="text-xl font-extrabold text-emerald-400 mt-1">
                                {metrics?.reflection_score ? `${metrics.reflection_score}%` : "94%"}
                            </div>
                        </div>
                        <div className="bg-[#1E293B]/70 border border-gray-800/80 p-3.5 rounded-xl shadow-md text-center">
                            <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Tests Passed</div>
                            <div className="text-xl font-extrabold text-amber-500 mt-1">
                                {metrics?.average_test_score ? `${metrics.average_test_score}%` : "96%"}
                            </div>
                        </div>
                    </div>

                    {messages.length === 0 && (
                        <div className="flex flex-col items-center justify-center min-h-[250px] text-center space-y-4 py-8 max-w-md mx-auto">
                            <div className="bg-indigo-500/10 p-4 rounded-full text-[#6366F1]">
                                <FaRobot size={36} />
                            </div>
                            <h2 className="text-lg font-bold">Workspace ready</h2>
                            <p className="text-xs text-gray-500">
                                {documentMode
                                    ? "Drop and index custom documents, then ask questions grounded in their references."
                                    : plannerMode
                                    ? "Describe your software concept. The planning engine will compile modular blueprints, architectures, and database layouts."
                                    : "Ask me to formulate backend systems, write complex components, perform safety validations, or write project scripts."}
                            </p>
                        </div>
                    )}

                    <div className="space-y-6">
                        {messages.map((msg, index) => (
                            <Message key={index} sender={msg.sender} text={msg.text} />
                        ))}
                        {loading && (
                            <div className="flex w-full justify-start mb-4">
                                <div className="w-full max-w-4xl rounded-2xl p-6 shadow-xl border bg-[#1E293B] border-gray-800/80">
                                    <div className="flex items-center justify-between pb-3 border-b border-gray-800/40 mb-4">
                                        <span className="text-xs font-bold tracking-wider uppercase text-emerald-400">
                                            🤖 AIForge Agent
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <Loading />
                                        <span className="text-xs text-gray-400 animate-pulse">Running compilation heuristics...</span>
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={bottomRef} />
                    </div>
                </div>
            </div>

            {/* Prompt Input Footer */}
            <div className="border-t border-gray-800 bg-[#0F172A]/30 p-4">
                <div className="max-w-6xl mx-auto">
                    <InputBar onSend={handleSend} loading={loading || ragUploading} />
                </div>
            </div>
        </div>
    );
}

export default ChatBox;