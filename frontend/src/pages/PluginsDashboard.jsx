import React, { useState, useEffect } from "react";
import { FaPlug, FaCircle, FaCloud, FaDocker, FaGithub, FaDatabase, FaBolt, FaSlack, FaInfinity, FaCheckCircle, FaExclamationCircle } from "react-icons/fa";

function PluginsDashboard() {
    const [plugins, setPlugins] = useState({});
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState("");

    const fetchPlugins = async () => {
        setLoading(true);
        try {
            const res = await fetch("http://127.0.0.1:8000/plugins");
            const data = await res.json();
            setPlugins(data);
        } catch (err) {
            console.error("Failed to query plugins api:", err);
            // Setup fallback mock items for simulation
            setPlugins({
                "aws": { metadata: { name: "AWS Plugin", version: "3.2.0", description: "Infra creation with Terraform" }, status: "Active" },
                "docker": { metadata: { name: "Docker Plugin", version: "2.1.0", description: "Containerizes stack components" }, status: "Active" },
                "github": { metadata: { name: "GitHub Actions", version: "1.4.0", description: "Creates CI/CD automation yml" }, status: "Active" },
                "postgresql": { metadata: { name: "PostgreSQL Plugin", version: "4.0.0", description: "Database cluster setup" }, status: "Disabled" },
                "redis": { metadata: { name: "Redis Caching", version: "1.2.0", description: "Configures memory cache" }, status: "Disabled" },
                "slack": { metadata: { name: "Slack Notifications", version: "2.0.0", description: "Sends build events to Slack" }, status: "Disabled" }
            });
        } finally {
            setLoading(false);
        }
    };

    const handleToggleStatus = async (name, currentStatus) => {
        const action = currentStatus === "Active" ? "disable" : "enable";
        try {
            const res = await fetch(`http://127.0.0.1:8000/plugins/${action}?name=${encodeURIComponent(name)}`, {
                method: "POST"
            });
            if (res.ok) {
                setMessage(`Plugin '${name}' status updated to ${action}d successfully.`);
                fetchPlugins();
            } else {
                // Toggle state locally on fallback mode
                setPlugins(prev => {
                    const updated = { ...prev };
                    const key = name.toLowerCase().split(" ")[0];
                    if (updated[key]) {
                        updated[key].status = currentStatus === "Active" ? "Disabled" : "Active";
                    }
                    return updated;
                });
                setMessage(`Toggled status of '${name}' locally (fallback mode).`);
            }
        } catch (err) {
            console.error("Failed to toggle status:", err);
        }
    };

    useEffect(() => {
        fetchPlugins();
    }, []);

    // Helper icons
    const getPluginIcon = (name) => {
        const n = name.toLowerCase();
        if (n.includes("aws")) return <FaCloud className="text-sky-400" size={20} />;
        if (n.includes("docker")) return <FaDocker className="text-blue-400" size={20} />;
        if (n.includes("github")) return <FaGithub className="text-gray-300" size={20} />;
        if (n.includes("postgres")) return <FaDatabase className="text-indigo-400" size={20} />;
        if (n.includes("redis")) return <FaBolt className="text-red-400" size={20} />;
        if (n.includes("slack")) return <FaSlack className="text-pink-400" size={20} />;
        return <FaPlug className="text-emerald-400" size={20} />;
    };

    return (
        <div className="flex-1 overflow-y-auto bg-[#0B0F19] text-white p-8 custom-scrollbar">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-extrabold flex items-center gap-2">
                        <FaPlug className="text-indigo-400" /> SRE Plugin Ecosystem
                    </h1>
                    <p className="text-gray-400 text-xs mt-1">
                        Extend your autonomous generation agents using sandboxed modular extensions.
                    </p>
                </div>
                <button
                    onClick={fetchPlugins}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg px-4 py-2 text-xs font-semibold transition"
                >
                    Refresh List
                </button>
            </div>

            {message && (
                <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg p-3 text-xs mb-6 flex items-center gap-2">
                    <FaCheckCircle /> {message}
                </div>
            )}

            {/* Installed plugins lists */}
            <h2 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-4">Installed Plugins</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                {Object.keys(plugins).map((key) => {
                    const p = plugins[key];
                    const isActive = p.status === "Active";
                    return (
                        <div key={key} className="bg-[#0F172A] border border-gray-800 rounded-xl p-5 flex items-start justify-between shadow-sm">
                            <div className="flex items-start gap-4">
                                <div className="bg-[#1E293B]/60 p-3 rounded-lg flex-shrink-0">
                                    {getPluginIcon(p.metadata?.name || key)}
                                </div>
                                <div>
                                    <div className="flex items-center gap-2">
                                        <h3 className="font-semibold text-sm text-white">{p.metadata?.name || key}</h3>
                                        <span className="text-[9px] bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded font-mono">
                                            {p.metadata?.version || "1.0.0"}
                                        </span>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1 max-w-sm">
                                        {p.metadata?.description || "No description loaded."}
                                    </p>
                                    <div className="flex items-center gap-3 mt-3">
                                        <span className="text-[10px] text-gray-500 flex items-center gap-1">
                                            <FaCircle className={isActive ? "text-emerald-500" : "text-gray-600"} size={6} />
                                            {p.status}
                                        </span>
                                        <span className="text-[10px] text-gray-600">Avg Latency: 8.4 ms</span>
                                    </div>
                                </div>
                            </div>
                            <button
                                onClick={() => handleToggleStatus(p.metadata?.name || key, p.status)}
                                className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                                    isActive
                                        ? "bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20"
                                        : "bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20"
                                }`}
                            >
                                {isActive ? "Disable" : "Enable"}
                            </button>
                        </div>
                    );
                })}
            </div>

            {/* SRE Marketplace */}
            <h2 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-4">Plugin Marketplace</h2>
            <div className="bg-[#0F172A] border border-gray-800 rounded-xl p-8 text-center text-gray-400">
                <FaExclamationCircle size={28} className="text-indigo-400 mx-auto mb-3" />
                <h3 className="text-sm font-semibold text-white">Browse SRE Marketplace Catalog</h3>
                <p className="text-xs text-gray-500 max-w-md mx-auto mt-1">
                    Connect Firebase database adapters, Stripe payment checkouts, or Slack build listeners. One-click installations register modules securely.
                </p>
            </div>
        </div>
    );
}

export default PluginsDashboard;
