import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

function Message({ sender, text }) {
    const isUser = sender === "user";

    return (
        <div
            className={`flex ${
                isUser ? "justify-end" : "justify-start"
            }`}
        >
            <div
                className={`
                    max-w-4xl
                    rounded-2xl
                    px-5
                    py-4
                    shadow-lg
                    ${
                        isUser
                            ? "bg-blue-600 text-white"
                            : "bg-[#444654] text-gray-100"
                    }
                `}
            >
                <div
                    className={`
                        text-sm
                        font-semibold
                        mb-3
                        ${
                            isUser
                                ? "text-blue-100"
                                : "text-green-400"
                        }
                    `}
                >
                    {isUser ? "👤 You" : "🤖 AIForge"}
                </div>

                <div className="prose prose-invert max-w-none">
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                            code({
                                inline,
                                className,
                                children,
                                ...props
                            }) {
                                const match =
                                    /language-(\w+)/.exec(className || "");

                                return !inline && match ? (
                                    <SyntaxHighlighter
                                        style={oneDark}
                                        language={match[1]}
                                        PreTag="div"
                                        customStyle={{
                                            borderRadius: "12px",
                                            padding: "18px",
                                            marginTop: "12px",
                                            marginBottom: "12px",
                                            fontSize: "15px",
                                        }}
                                        {...props}
                                    >
                                        {String(children).replace(/\n$/, "")}
                                    </SyntaxHighlighter>
                                ) : (
                                    <code
                                        className="bg-gray-800 px-1 py-0.5 rounded"
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
            </div>
        </div>
    );
}

export default Message;