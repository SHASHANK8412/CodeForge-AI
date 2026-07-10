import { useState } from "react";

function InputBar({ onSend }) {
    const [message, setMessage] = useState("");

    const handleSend = () => {
        if (!message.trim()) return;

        onSend(message);
        setMessage("");
    };

    return (
        <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
            <input
                type="text"
                value={message}
                placeholder="Ask AIForge..."
                onChange={(e) => setMessage(e.target.value)}
                style={{
                    flex: 1,
                    padding: "12px",
                    fontSize: "16px",
                }}
            />

            <button onClick={handleSend}>
                Send
            </button>
        </div>
    );
}

export default InputBar;