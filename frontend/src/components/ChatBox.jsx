import { useState } from "react";
import InputBar from "./InputBar";
import Message from "./Message";
import { sendMessage } from "../services/api";

function ChatBox() {
    const [messages, setMessages] = useState([]);

    const handleSend = async (text) => {

        setMessages((prev) => [
            ...prev,
            {
                sender: "user",
                text,
            },
        ]);

        const reply = await sendMessage(text);

        setMessages((prev) => [
            ...prev,
            {
                sender: "ai",
                text: reply,
            },
        ]);
    };

    return (
        <div
            style={{
                width: "900px",
                margin: "40px auto",
            }}
        >
            <h1>🚀 AIForge</h1>

            {messages.map((msg, index) => (
                <Message
                    key={index}
                    sender={msg.sender}
                    text={msg.text}
                />
            ))}

            <InputBar onSend={handleSend} />
        </div>
    );
}

export default ChatBox;