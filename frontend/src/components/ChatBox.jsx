import { useState, useEffect, useRef } from "react";
import InputBar from "./InputBar";
import Message from "./Message";
import Loading from "./Loading";

import { sendMessage } from "../services/api";
import { generatePlan } from "../services/plannerApi";
import { queryRagDocuments, uploadRagDocuments } from "../services/ragApi";
import {
    getActiveSessionId,
    getSavedMessages,
    resetChatSession,
    loadSessionMessages,
    saveMessages,
} from "../utils/chatStorage";

function ChatBox() {
    const initialSessionId = getActiveSessionId();
    const [sessionId, setSessionId] = useState(initialSessionId);
    // Load chat history
    const [messages, setMessages] = useState(() => {
        return getSavedMessages(initialSessionId);
    });

    const [loading, setLoading] = useState(false);
    const [ragUploading, setRagUploading] = useState(false);
    const [plannerMode, setPlannerMode] = useState(false);
    const [documentMode, setDocumentMode] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [ragStatus, setRagStatus] = useState("");

    const bottomRef = useRef(null);
    const fileInputRef = useRef(null);

    useEffect(() => {
        const handleNewChat = () => {
            const nextSessionId = resetChatSession();
            setSessionId(nextSessionId);
            setMessages([]);
            setLoading(false);
            window.dispatchEvent(new CustomEvent("aiforge:session-changed", { detail: { sessionId: nextSessionId } }));
        };

        const handleOpenSession = (event) => {
            const nextSessionId = event.detail?.sessionId;

            if (!nextSessionId) return;

            setSessionId(nextSessionId);
            setMessages(loadSessionMessages(nextSessionId));
            setLoading(false);
            window.dispatchEvent(new CustomEvent("aiforge:session-changed", { detail: { sessionId: nextSessionId } }));
        };

        window.addEventListener("aiforge:new-chat", handleNewChat);
        window.addEventListener("aiforge:open-session", handleOpenSession);

        return () => {
            window.removeEventListener("aiforge:new-chat", handleNewChat);
            window.removeEventListener("aiforge:open-session", handleOpenSession);
        };
    }, []);

    // Save chat history + Auto Scroll
    useEffect(() => {
        saveMessages(sessionId, messages);

        bottomRef.current?.scrollIntoView({
            behavior: "smooth",
        });
    }, [messages, loading, sessionId]);

    // Send Message
    const handleSend = async (text) => {
        if (!text.trim() || loading) return;

        // User Message
        setMessages((prev) => [
            ...prev,
            {
                sender: "user",
                text,
            },
        ]);

        setLoading(true);

        try {

            let reply;

            if (documentMode) {
                setRagStatus("");
                if (selectedFiles.length > 0) {
                    setRagUploading(true);
                    await uploadRagDocuments(selectedFiles);
                    setRagStatus(`Indexed ${selectedFiles.length} file(s).`);
                    setSelectedFiles([]);
                    if (fileInputRef.current) {
                        fileInputRef.current.value = "";
                    }
                }

                const ragResult = await queryRagDocuments(text);
                const sourceText = (ragResult.sources || [])
                    .map((source, index) => {
                        const location = [source.source, source.page !== "" && source.page !== null ? `page ${source.page}` : null]
                            .filter(Boolean)
                            .join(" • ");
                        return `- ${index + 1}. ${location || "source"}: ${source.snippet}`;
                    })
                    .join("\n");

                reply = `${ragResult.answer}\n\n### Sources\n${sourceText || "- No source metadata available"}`;
            } else if (plannerMode) {
                reply = await generatePlan(text, sessionId);
            } else {
                reply = await sendMessage(text, sessionId);
            }

            setMessages((prev) => [
                ...prev,
                {
                    sender: "ai",
                    text: typeof reply === "string" ? reply : reply?.response ?? String(reply),
                },
            ]);

        } catch (error) {

            console.error(error);

            setMessages((prev) => [
                ...prev,
                {
                    sender: "ai",
                    text: "❌ Something went wrong!",
                },
            ]);

        } finally {

            setRagUploading(false);
            setLoading(false);

        }
    };

    // Clear Chat
    const clearChat = () => {
        const nextSessionId = resetChatSession();
        setSessionId(nextSessionId);
        setMessages([]);
        window.dispatchEvent(new CustomEvent("aiforge:session-changed", { detail: { sessionId: nextSessionId } }));
    };

    return (
        <div className="flex flex-col h-full max-w-5xl mx-auto">

            {/* Header */}

            <div className="flex justify-between items-center border-b border-gray-700 py-4 px-6">

                <div>

                    <h1 className="text-3xl font-bold">
                        🚀 AIForge
                    </h1>

                    <p className="text-sm text-gray-400">
                        Powered by Qwen 2.5
                    </p>

                </div>

                <button
                    onClick={clearChat}
                    disabled={loading}
                    className="
                        bg-red-600
                        hover:bg-red-700
                        disabled:bg-gray-700
                        px-4
                        py-2
                        rounded-lg
                        transition
                    "
                >
                    Clear Chat
                </button>

            </div>

            {/* Planner Toggle */}

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

            {documentMode && (
                <div className="px-6 py-4 border-b border-gray-700 space-y-3 bg-[#262730]">
                    <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                        <label className="text-sm text-gray-300 font-medium">
                            Upload PDFs, text files, or markdown documents.
                        </label>
                        <input
                            ref={fileInputRef}
                            type="file"
                            multiple
                            accept=".pdf,.txt,.md"
                            onChange={(event) => setSelectedFiles(Array.from(event.target.files || []))}
                            className="text-sm text-gray-300"
                        />
                    </div>

                    {selectedFiles.length > 0 && (
                        <div className="text-sm text-amber-300">
                            Selected: {selectedFiles.map((file) => file.name).join(", ")}
                        </div>
                    )}

                    {ragStatus && (
                        <div className="text-sm text-green-300">
                            {ragStatus}
                        </div>
                    )}
                </div>
            )}

            {/* Messages */}

            <div
                className="
                    flex-1
                    overflow-y-auto
                    p-6
                    space-y-4
                "
            >

                {messages.length === 0 && (

                    <div className="text-center text-gray-400 mt-20">

                        <h2 className="text-4xl mb-4">
                            👋 Welcome to AIForge
                        </h2>

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

                    <Message
                        key={index}
                        sender={msg.sender}
                        text={msg.text}
                    />

                ))}

                {loading && <Loading />}

                <div ref={bottomRef}></div>

            </div>

            {/* Input */}

            <div className="border-t border-gray-700 p-4">

                <InputBar
                    onSend={handleSend}
                    loading={loading || ragUploading}
                />

            </div>

        </div>
    );
}

export default ChatBox;