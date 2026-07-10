function Loading() {
    return (
        <div className="flex justify-start">
            <div
                className="
                    bg-[#444654]
                    text-gray-200
                    rounded-2xl
                    px-5
                    py-4
                    shadow-lg
                    max-w-md
                "
            >
                <div className="text-green-400 font-semibold mb-2">
                    🤖 AIForge
                </div>

                <div className="flex items-center gap-2">
                    <span>Thinking</span>

                    <div className="flex gap-1">
                        <span className="w-2 h-2 rounded-full bg-green-400 animate-bounce"></span>
                        <span
                            className="w-2 h-2 rounded-full bg-green-400 animate-bounce"
                            style={{ animationDelay: "0.2s" }}
                        ></span>
                        <span
                            className="w-2 h-2 rounded-full bg-green-400 animate-bounce"
                            style={{ animationDelay: "0.4s" }}
                        ></span>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Loading;