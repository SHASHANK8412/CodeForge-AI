import { useState, useEffect } from "react";
import { FaBoxes, FaClock, FaCheckCircle, FaStar, FaBrain } from "react-icons/fa";
import { fetchMetrics } from "../services/projectApi";

function MetricsDashboard() {
    const [metrics, setMetrics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const loadMetrics = async () => {
        setLoading(true);
        setError("");
        try {
            const data = await fetchMetrics();
            setMetrics(data);
        } catch (err) {
            console.error("Failed to load metrics data", err);
            setError("Failed to load metrics dashboard data.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadMetrics();
    }, []);

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center p-8 bg-[#0B0F19] text-gray-400">
                <span className="animate-pulse">Loading analytics...</span>
            </div>
        );
    }

    const cards = [
        {
            title: "Projects Generated",
            value: metrics?.projects_generated || 0,
            description: "Total completed pipelines",
            icon: <FaBoxes />,
            color: "text-indigo-400",
            bg: "bg-indigo-500/10",
        },
        {
            title: "Average Score",
            value: `${metrics?.reflection_score || 85}%`,
            description: "Agent self-reflection rating",
            icon: <FaStar />,
            color: "text-amber-400",
            bg: "bg-amber-500/10",
        },
        {
            title: "Tests Passed",
            value: `${metrics?.average_test_score || 0}%`,
            description: "Average code coverage / pass rate",
            icon: <FaCheckCircle />,
            color: "text-emerald-400",
            bg: "bg-emerald-500/10",
        },
        {
            title: "Knowledge Size",
            value: `${metrics?.knowledge_size || 0} Lessons`,
            description: "Learned heuristics database",
            icon: <FaBrain />,
            color: "text-purple-400",
            bg: "bg-purple-500/10",
        },
    ];

    return (
        <div className="flex-1 overflow-y-auto bg-[#0B0F19] text-white p-6 space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">📊 Metrics Dashboard</h1>
                <p className="text-gray-400 text-sm mt-1">
                    System-wide productivity statistics and agent assembly quality over time.
                </p>
            </div>

            {error && (
                <div className="bg-red-900/20 border border-red-800 text-red-300 rounded-xl p-4 text-sm">
                    {error}
                </div>
            )}

            {/* Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {cards.map((card, idx) => (
                    <div key={idx} className="bg-[#1e293b] border border-gray-800 p-5 rounded-2xl shadow-lg relative overflow-hidden transition-all duration-300 hover:border-gray-700">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                    {card.title}
                                </p>
                                <h3 className="text-3xl font-extrabold text-white mt-2">
                                    {card.value}
                                </h3>
                            </div>
                            <div className={`p-3 rounded-xl ${card.color} ${card.bg}`}>
                                {card.icon}
                            </div>
                        </div>
                        <p className="text-xs text-gray-500 mt-4">
                            {card.description}
                        </p>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Common Bugs list */}
                <div className="bg-[#1e293b] border border-gray-800 rounded-2xl p-6 shadow-lg">
                    <h3 className="text-lg font-bold mb-4 text-rose-400 flex items-center gap-2">
                        ⚠️ Most Recurrent Pipeline Anomalies
                    </h3>
                    {(!metrics?.common_bugs || metrics.common_bugs.length === 0) ? (
                        <div className="text-center text-sm text-gray-500 italic py-8">
                            No recurrent errors reported yet.
                        </div>
                    ) : (
                        <ul className="space-y-3">
                            {metrics.common_bugs.map((bug, idx) => (
                                <li key={idx} className="bg-[#0B0F19]/40 border border-gray-800/50 rounded-lg p-3 text-sm flex gap-3">
                                    <span className="text-rose-500 font-bold">{idx + 1}.</span>
                                    <span className="text-gray-300">{bug}</span>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                {/* Top Lessons list */}
                <div className="bg-[#1e293b] border border-gray-800 rounded-2xl p-6 shadow-lg">
                    <h3 className="text-lg font-bold mb-4 text-emerald-400 flex items-center gap-2">
                        💡 Key Heuristic Directives Applied
                    </h3>
                    {(!metrics?.top_lessons || metrics.top_lessons.length === 0) ? (
                        <div className="text-center text-sm text-gray-500 italic py-8">
                            No directives recorded yet.
                        </div>
                    ) : (
                        <ul className="space-y-3">
                            {metrics.top_lessons.map((lesson, idx) => (
                                <li key={idx} className="bg-[#0B0F19]/40 border border-gray-800/50 rounded-lg p-3 text-sm flex gap-3">
                                    <span className="text-emerald-500 font-bold">{idx + 1}.</span>
                                    <span className="text-gray-300">{lesson}</span>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </div>
        </div>
    );
}

export default MetricsDashboard;
