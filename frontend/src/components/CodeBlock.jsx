import { useState } from "react";
import { FaCopy, FaCheck } from "react-icons/fa";

function CodeBlock({ code }) {
    const [copied, setCopied] = useState(false);

    const copyCode = () => {
        navigator.clipboard.writeText(code);

        setCopied(true);

        setTimeout(() => {
            setCopied(false);
        }, 2000);
    };

    return (
        <div style={{ position: "relative" }}>
            <button
                onClick={copyCode}
                style={{
                    position: "absolute",
                    right: 10,
                    top: 10,
                    cursor: "pointer",
                }}
            >
                {copied ? <FaCheck /> : <FaCopy />}
            </button>

            <pre>{code}</pre>
        </div>
    );
}

export default CodeBlock;