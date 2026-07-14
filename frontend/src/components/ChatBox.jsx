import { useEffect, useRef, useState } from "react";
import InputBar from "./InputBar";
import Loading from "./Loading";
import Message from "./Message";
import RagUploadPanel from "./RagUploadPanel";
import { sendMessage } from "../services/api";
import { createConversation, getConversationHistory } from "../services/conversationApi";
import { generatePlan } from "../services/plannerApi";
import { queryRagDocuments, uploadRagDocuments } from "../services/ragApi";
import { getActiveSessionId, setActiveSessionId } from "../utils/chatStorage";


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

    return (
        <div className="flex flex-col h-full max-w-5xl mx-auto">
            <div className="flex justify-between items-center border-b border-gray-700 py-4 px-6">
                <div>
                    <h1 className="text-3xl font-bold">🚀 AIForge</h1>
                    <p className="text-sm text-gray-400">{conversationTitle}</p>
                </div>

                <button
                    onClick={handleNewConversation}
                    disabled={loading}
                    className="bg-red-600 hover:bg-red-700 disabled:bg-gray-700 px-4 py-2 rounded-lg transition"
                >
                    New Chat
                </button>
            </div>

            <div className="flex flex-wrap gap-3 px-6 py-4 border-b border-gray-700">
                <button
                    onClick={() => {
                        setPlannerMode(false);
                        setDocumentMode(false);
                    }}
                    className={`px-4 py-2 rounded-lg transition ${
                        !plannerMode && !documentMode
                            ? "bg-green-600 text-white"
                            : "bg-gray-700 text-gray-300"
                    }`}
                >
                    💬 Chat Mode
                </button>

                <button
                    onClick={() => setPlannerMode(true)}
                    disabled={documentMode}
                    className={`px-4 py-2 rounded-lg transition ${
                        plannerMode
                            ? "bg-blue-600 text-white"
                            : "bg-gray-700 text-gray-300"
                    }`}
                >
                    📋 Planner Mode
                </button>

                <button
                    onClick={() => {
                        setDocumentMode((current) => !current);
                        setPlannerMode(false);
                    }}
                    className={`px-4 py-2 rounded-lg transition ${
                        documentMode
                            ? "bg-amber-500 text-black"
                            : "bg-gray-700 text-gray-300"
                    }`}
                >
                    📚 Document Mode
                </button>
            </div>

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

            <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.length === 0 && (
                    <div className="text-center text-gray-400 mt-20">
                        <h2 className="text-4xl mb-4">👋 Welcome to AIForge</h2>
                        <p>
                            {documentMode
                                ? "Upload documents and ask questions grounded in the indexed content."
                                : plannerMode
                                ? "Describe your software idea and AIForge will generate a complete project plan."
                                : "Ask me to write code, debug errors, explain concepts, or build projects."}
                        </p>
                    </div>
                )}

                {messages.map((msg, index) => (
                    <Message key={index} sender={msg.sender} text={msg.text} />
                ))}

                {loading && <Loading />}
                <div ref={bottomRef} />
            </div>

            <div className="border-t border-gray-700 p-4">
                <InputBar onSend={handleSend} loading={loading || ragUploading} />
            </div>
        </div>
    );
}

export default ChatBox;