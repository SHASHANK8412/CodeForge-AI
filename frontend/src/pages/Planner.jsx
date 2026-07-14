import { useState } from "react";

import PlannerCard from "../components/PlannerCard";

import { generatePlan } from "../services/plannerApi";

function Planner() {

    const [prompt, setPrompt] = useState("");

    const [plan, setPlan] = useState(null);

    const [loading, setLoading] = useState(false);

    async function handleGenerate() {

        if (!prompt.trim()) return;

        setLoading(true);

        try {

            const result = await generatePlan(prompt);

            setPlan(result);

        } finally {

            setLoading(false);

        }

    }

    return (

        <div className="max-w-5xl mx-auto p-8">

            <h1 className="text-4xl font-bold">

                🚀 AIForge Planner

            </h1>

            <textarea

                value={prompt}

                onChange={(e)=>setPrompt(e.target.value)}

                placeholder="Describe your software project..."

                rows={5}

                className="w-full mt-6 p-4 rounded-xl bg-[#40414F] text-white"

            />

            <button

                onClick={handleGenerate}

                className="mt-5 bg-green-600 px-6 py-3 rounded-xl"

            >

                {loading ? "Generating..." : "Generate Plan"}

            </button>

            <PlannerCard plan={plan}/>

        </div>

    );

}

export default Planner;