import { useState, useEffect } from "react";
import { FaGraduationCap, FaLightbulb, FaCheckCircle, FaExclamationTriangle } from "react-icons/fa";
import { fetchReflection, fetchLessons } from "../services/projectApi";

function ReflectionDashboard() {
    const [reflection, setReflection] = useState(null);
    const [lessons, setLessons] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const loadReflectionData = async () => {
        setLoading(true);
        setError("");
        try {
            const [refData, lessonsData] = await Promise.all([
                fetchReflection().catch(() => null), // Fallback if no reflection history yet
                fetchLessons().catch(() => []),
            ]);
            setReflection(refData);
            setLessons(lessonsData);
        } catch (err) {
            console.error("Failed to load reflection dashboard data", err);
            setError("Failed to load reflection dashboard data.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadReflectionData();
    }, []);

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center p-8 bg-[#0B0F19] text-gray-400">
                <span className="animate-pulse">Loading reflection data...</span>
            </div>
        );
    }

    const score = reflection ? reflection.reflection_score : 0;
    const recommendations = reflection ? reflection.recommendations || [] : [];
    const bugsFound = reflection ? reflection.bugs_found : 0;
    const testsPassed = reflection ? reflection.tests_passed : 0;

    return (
        <div className="flex-1 overflow-y-auto bg-[#0B0F19] text-white p-6 space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">🧠 Reflection Hub</h1>
                <p className="text-gray-400 text-sm mt-1">
                    Continuous learning & code optimization derived from historical project generations.
                </p>
            </div>

            {error && (
                <div className="bg-red-900/20 border border-red-800 text-red-300 rounded-xl p-4 text-sm">
                    {error}
                </div>
            )}

            {/* Score and Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Score Radial Card */}
                <div className="bg-[#1e293b] border border-gray-800 p-6 rounded-2xl flex flex-col items-center justify-center text-center shadow-lg relative overflow-hidden">
                    <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
                        Latest Quality Score
                    </span>
                    <div className="relative w-36 h-36 flex items-center justify-center">
                        <svg className="absolute w-full h-full transform -rotate-90">
                            <circle
                                cx="72"
                                cy="72"
                                r="64"
                                className="stroke-gray-800 fill-none"
                                strokeWidth="8"
                            />
                            <circle
                                cx="72"
                                cy="72"
                                r="64"
                                className="stroke-[#6366F1] fill-none transition-all duration-1000 ease-out"
                                strokeWidth="8"
                                strokeDasharray={2 * Math.PI * 64}
                                strokeDashoffset={2 * Math.PI * 64 * (1 - (score || 85) / 100)}
                                strokeLinecap="round"
                            />
                        </svg>
                        <div className="text-center">
                            <span className="text-4xl font-extrabold text-white">{score || 85}</span>
                            <span className="text-gray-400 block text-xs mt-0.5">/ 100</span>
                        </div>
                    </div>
                    <span className="text-xs text-gray-500 mt-4">
                        Project: {reflection?.project_name || "N/A"}
                    </span>
                </div>

                {/* Statistics Cards */}
                <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="bg-[#1e293b] border border-gray-800 p-5 rounded-xl flex items-center gap-4 shadow">
                        <div className="p-3 bg-[#6366F1]/10 rounded-xl text-[#6366F1]">
                            <FaGraduationCap size={24} />
                        </div>
                        <div>
                            <div className="text-2xl font-bold">{lessons.length}</div>
                            <div className="text-xs text-gray-400">Total Lessons Recorded</div>
                        </div>
                    </div>

                    <div className="bg-[#1e293b] border border-gray-800 p-5 rounded-xl flex items-center gap-4 shadow">
                        <div className="p-3 bg-[#EF4444]/10 rounded-xl text-[#EF4444]">
                            <FaExclamationTriangle size={24} />
                        </div>
                        <div>
                            <div className="text-2xl font-bold">{bugsFound}</div>
                            <div className="text-xs text-gray-400">Bugs Detected Last Run</div>
                        </div>
                    </div>

                    <div className="bg-[#1e293b] border border-gray-800 p-5 rounded-xl flex items-center gap-4 shadow">
                        <div className="p-3 bg-[#10B981]/10 rounded-xl text-[#10B981]">
                            <FaCheckCircle size={24} />
                        </div>
                        <div>
                            <div className="text-2xl font-bold">{testsPassed}</div>
                            <div className="text-xs text-gray-400">Tests Passed Last Run</div>
                        </div>
                    </div>

                    <div className="bg-[#1e293b] border border-gray-800 p-5 rounded-xl flex items-center gap-4 shadow">
                        <div className="p-3 bg-amber-500/10 rounded-xl text-amber-500">
                            <FaLightbulb size={24} />
                        </div>
                        <div>
                            <div className="text-2xl font-bold">{recommendations.length}</div>
                            <div className="text-xs text-gray-400">Actionable Suggestions</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Recommendations List */}
            {recommendations.length > 0 && (
                <div className="bg-[#1e293b] border border-gray-800 rounded-2xl p-6 shadow-lg">
                    <h3 className="text-lg font-bold flex items-center gap-2 mb-4 text-amber-400">
                        <FaLightbulb /> Latest AI Recommendations
                    </h3>
                    <ul className="space-y-2">
                        {recommendations.map((rec, index) => (
                            <li key={index} className="flex gap-2 text-sm text-gray-300">
                                <span className="text-[#6366F1] font-bold">•</span>
                                <span>{rec}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Knowledge Base Lessons Table */}
            <div className="bg-[#1e293b] border border-gray-800 rounded-2xl p-6 shadow-lg">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-[#6366F1]">
                    <FaGraduationCap /> Persistent Knowledge Base ({lessons.length} Lessons)
                </h3>
                {lessons.length === 0 ? (
                    <div className="text-center text-sm text-gray-500 italic py-8">
                        No lessons learned recorded yet. Run a project generation to start capturing improvements.
                    </div>
                ) : (
                    <div className="space-y-4">
                        {lessons.map((lesson, index) => (
                            <div key={index} className="border-b border-gray-800 pb-4 last:border-b-0 last:pb-0">
                                <div className="flex justify-between items-start gap-4">
                                    <div className="space-y-1">
                                        <div className="text-sm font-semibold text-rose-400">
                                            Problem: {lesson.problem}
                                        </div>
                                        <div className="text-sm text-gray-300">
                                            <span className="font-semibold text-emerald-400">Lesson:</span> {lesson.lesson}
                                        </div>
                                    </div>
                                    <div className="flex flex-col items-end whitespace-nowrap text-xs text-gray-500">
                                        <span className="px-2 py-0.5 rounded bg-gray-800 text-gray-300 border border-gray-700">
                                            Seen: {lesson.count || 1}x
                                        </span>
                                        <span className="mt-1">Last: {lesson.last_seen || "N/A"}</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default ReflectionDashboard;
