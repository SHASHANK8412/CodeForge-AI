function Message({ sender, text }) {
    return (
        <div
            style={{
                margin: "15px 0",
                padding: "12px",
                borderRadius: "10px",
                background: sender === "user" ? "#d9fdd3" : "#f1f1f1",
            }}
        >
            <strong>{sender === "user" ? "You" : "AIForge"}</strong>

            <p>{text}</p>
        </div>
    );
}

export default Message;     