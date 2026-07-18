import { useState } from "react";

import Home from "./pages/Home";
import ProjectGenerator from "./pages/ProjectGenerator";

function App() {

    const [view, setView] = useState("chat");

    return (
        <div className="min-h-screen bg-[#343541]">

            <div className="flex gap-2 p-3 bg-[#202123] border-b border-gray-700">
                <button
                    onClick={() => setView("chat")}
                    className={`px-4 py-2 rounded-lg text-sm font-medium ${
                        view === "chat"
                            ? "bg-green-600 text-white"
                            : "text-gray-300 hover:bg-[#2a2b32]"
                    }`}
                >
                    💬 Chat
                </button>
                <button
                    onClick={() => setView("project")}
                    className={`px-4 py-2 rounded-lg text-sm font-medium ${
                        view === "project"
                            ? "bg-green-600 text-white"
                            : "text-gray-300 hover:bg-[#2a2b32]"
                    }`}
                >
                    🏗️ Project Generator
                </button>
            </div>

            {view === "chat" ? <Home /> : <ProjectGenerator />}

        </div>
    );
}

export default App;
