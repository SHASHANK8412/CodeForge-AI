import { useState, useMemo, memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { FaCopy, FaCheck, FaCheckDouble, FaThumbsUp, FaThumbsDown, FaRedo } from "react-icons/fa";

// Sub-component to render clean syntax-highlighted code blocks with Copy buttons
function CodeWrapper({ children, language }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(String(children).trim());
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="my-4 rounded-xl overflow-hidden border border-gray-800 bg-[#0F172A] shadow-xl">
            <div className="flex justify-between items-center px-4 py-2 bg-[#1E293B] text-[10px] text-gray-400 border-b border-gray-800/60 font-mono">
                <span className="font-semibold text-indigo-400 uppercase tracking-wider">{language}</span>
                <button
                    onClick={handleCopy}
                    className="flex items-center gap-1.5 hover:text-white transition-colors py-1 px-2 rounded hover:bg-gray-800 cursor-pointer"
                >
                    {copied ? <FaCheck className="text-emerald-400" /> : <FaCopy />}
                    <span>{copied ? "Copied!" : "Copy"}</span>
                </button>
            </div>
            <div className="overflow-x-auto text-sm">
                <SyntaxHighlighter
                    style={oneDark}
                    language={language}
                    PreTag="div"
                    customStyle={{
                        margin: 0,
                        background: "transparent",
                        padding: "16px",
                        fontSize: "13px",
                        lineHeight: "1.5",
                    }}
                >
                    {String(children).replace(/\n$/, "")}
                </SyntaxHighlighter>
            </div>
        </div>
    );
}

function Message({ sender, text }) {
    const isUser = sender === "user";
    const [msgCopied, setMsgCopied] = useState(false);
    const [feedback, setFeedback] = useState(null); // 'like' | 'dislike' | null

    const timeString = useMemo(() => {
        const d = new Date();
        return `Today • ${d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}`;
    }, []);

    const copyEntireMessage = () => {
        navigator.clipboard.writeText(text);
        setMsgCopied(true);
        setTimeout(() => setMsgCopied(false), 2000);
    };

    const handleFeedback = (type) => {
        setFeedback((prev) => (prev === type ? null : type));
    };

    return (
        <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"} mb-4`}>
            <div
                className={`
                    w-full
                    max-w-4xl
                    rounded-2xl
                    p-6
                    shadow-xl
                    transition-all
                    duration-200
                    border
                    ${
                        isUser
                            ? "bg-indigo-600/10 border-indigo-500/20 text-indigo-50"
                            : "bg-[#1E293B] border-gray-800/80 text-gray-100"
                    }
                `}
            >
                {/* Header tag and Timestamp */}
                <div className="flex items-center justify-between pb-3 border-b border-gray-800/40 mb-4">
                    <div className="flex items-center gap-2">
                        <span
                            className={`
                                text-xs
                                font-bold
                                tracking-wider
                                uppercase
                                ${isUser ? "text-indigo-300" : "text-emerald-400"}
                            `}
                        >
                            {isUser ? "👤 You" : "🤖 AIForge Agent"}
                        </span>
                    </div>
                    <span className="text-[10px] text-gray-500 font-mono">
                        {timeString}
                    </span>
                </div>

                {/* Markdown text rendering */}
                <div className="prose prose-invert max-w-none text-sm leading-relaxed text-gray-300">
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                            code({ inline, className, children, ...props }) {
                                const match = /language-(\w+)/.exec(className || "");
                                return !inline && match ? (
                                    <CodeWrapper language={match[1]} {...props}>
                                        {children}
                                    </CodeWrapper>
                                ) : (
                                    <code
                                        className="bg-[#0B0F19] text-indigo-300 px-1.5 py-0.5 rounded font-mono text-xs border border-gray-800"
                                        {...props}
                                    >
                                        {children}
                                    </code>
                                );
                            },
                        }}
                    >
                        {text}
                    </ReactMarkdown>
                </div>

                {/* Footer panel with actions for AI message */}
                {!isUser && (
                    <div className="flex items-center justify-between mt-5 pt-3 border-t border-gray-800/40 text-[10px] text-gray-500">
                        {/* Copy & Regenerate Actions */}
                        <div className="flex items-center gap-4">
                            <button
                                onClick={copyEntireMessage}
                                className="flex items-center gap-1.5 hover:text-white transition-colors cursor-pointer"
                                title="Copy entire response"
                            >
                                {msgCopied ? <FaCheckDouble className="text-emerald-400" /> : <FaCopy />}
                                <span>{msgCopied ? "Copied" : "Copy"}</span>
                            </button>
                            <button
                                className="flex items-center gap-1.5 hover:text-white transition-colors cursor-pointer"
                                title="Regenerate this response"
                            >
                                <FaRedo size={9} />
                                <span>Regenerate</span>
                            </button>
                        </div>

                        {/* Likes/Feedback Actions */}
                        <div className="flex items-center gap-3">
                            <button
                                onClick={() => handleFeedback("like")}
                                className={`transition-colors cursor-pointer ${
                                    feedback === "like" ? "text-emerald-400 hover:text-emerald-500" : "hover:text-gray-300"
                                }`}
                                title="Helpful response"
                            >
                                <FaThumbsUp size={12} />
                            </button>
                            <button
                                onClick={() => handleFeedback("dislike")}
                                className={`transition-colors cursor-pointer ${
                                    feedback === "dislike" ? "text-rose-400 hover:text-rose-500" : "hover:text-gray-300"
                                }`}
                                title="Unhelpful response"
                            >
                                <FaThumbsDown size={12} />
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default memo(Message);