import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function PlannerCard({ plan }) {

    if (!plan) return null;

    return (

        <div className="bg-[#444654] rounded-xl p-6 mt-6 text-white">

            <h2 className="text-2xl font-bold mb-5">

                📋 Project Plan

            </h2>

            <ReactMarkdown remarkPlugins={[remarkGfm]}>

                {plan}

            </ReactMarkdown>

        </div>

    );

}

export default PlannerCard;