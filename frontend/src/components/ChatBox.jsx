import { useState, useEffect, useRef } from "react";
import InputBar from "./InputBar";
import Message from "./Message";
import Loading from "./Loading";

import { sendMessage } from "../services/api";
import { generatePlan } from "../services/plannerApi";

function ChatBox() {
    // Load chat history
    const [messages, setMessages] = useState(() => {
        const savedMessages = localStorage.getItem("messages");
        return savedMessages ? JSON.parse(savedMessages) : [];
    });

    const [loading, setLoading] = useState(false);
    const [plannerMode, setPlannerMode] = useState(false);

    const bottomRef = useRef(null);

    // Save chat history + Auto Scroll
    useEffect(() => {
        localStorage.setItem("messages", JSON.stringify(messages));

        bottomRef.current?.scrollIntoView({
            behavior: "smooth",
        });
    }, [messages, loading]);

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

            if (plannerMode) {
                reply = await generatePlan(text);
            } else {
                reply = await sendMessage(text);
            }

            setMessages((prev) => [
                ...prev,
                {
                    sender: "ai",
                    text: reply,
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

            setLoading(false);

        }
    };

    // Clear Chat
    const clearChat = () => {
        localStorage.removeItem("messages");
        setMessages([]);
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

            <div className="flex gap-3 px-6 py-4 border-b border-gray-700">

                <button
                    onClick={() => setPlannerMode(false)}
                    className={`px-4 py-2 rounded-lg transition ${
                        !plannerMode
                            ? "bg-green-600 text-white"
                            : "bg-gray-700 text-gray-300"
                    }`}
                >
                    💬 Chat Mode
                </button>

                <button
                    onClick={() => setPlannerMode(true)}
                    className={`px-4 py-2 rounded-lg transition ${
                        plannerMode
                            ? "bg-blue-600 text-white"
                            : "bg-gray-700 text-gray-300"
                    }`}
                >
                    📋 Planner Mode
                </button>

            </div>

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

                            {plannerMode
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
                    loading={loading}
                />

            </div>

        </div>
    );
}

export default ChatBox;