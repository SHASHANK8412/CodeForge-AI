function Loading() {
    return (
        <div className="flex gap-1">
            <span className="w-2 h-2 rounded-full bg-[#6366F1] animate-bounce"></span>
            <span
                className="w-2 h-2 rounded-full bg-[#6366F1] animate-bounce"
                style={{ animationDelay: "0.15s" }}
            ></span>
            <span
                className="w-2 h-2 rounded-full bg-[#6366F1] animate-bounce"
                style={{ animationDelay: "0.3s" }}
            ></span>
        </div>
    );
}

export default Loading;
