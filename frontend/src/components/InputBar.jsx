import { useState } from "react";
import { FaPaperPlane } from "react-icons/fa";

function InputBar({ onSend, loading }) {
    const [message, setMessage] = useState("");

    const handleSend = () => {
        if (!message.trim() || loading) return;

        onSend(message);
        setMessage("");
    };

    return (
        <div className="flex items-center gap-3 w-full">
            <input
                type="text"
                value={message}
                placeholder="Message AIForge..."
                disabled={loading}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(e) => {
                    if (e.key === "Enter") {
                        handleSend();
                    }
                }}
                className="
                    flex-1
                    bg-[#40414F]
                    text-white
                    placeholder-gray-400
                    rounded-xl
                    px-5
                    py-4
                    outline-none
                    border
                    border-gray-700
                    focus:border-green-500
                    transition-all
                    disabled:opacity-60
                "
            />

            <button
                onClick={handleSend}
                disabled={loading}
                className="
                    flex
                    items-center
                    justify-center
                    gap-2
                    bg-green-600
                    hover:bg-green-700
                    disabled:bg-gray-700
                    disabled:cursor-not-allowed
                    text-white
                    px-6
                    py-4
                    rounded-xl
                    font-semibold
                    transition-all
                "
            >
                {loading ? (
                    <>
                        <span className="animate-pulse">Thinking...</span>
                    </>
                ) : (
                    <>
                        <FaPaperPlane />
                        Send
                    </>
                )}
            </button>
        </div>
    );
}

export default InputBar;