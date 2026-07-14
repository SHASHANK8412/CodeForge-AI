import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function PlannerCard({ plan }) {

    if (!plan) return null;

    const isStructuredResponse = typeof plan === "object" && plan !== null;

    return (

        <div className="bg-[#444654] rounded-xl p-6 mt-6 text-white">

            <h2 className="text-2xl font-bold mb-5">📋 AIForge Output</h2>

            {isStructuredResponse ? (
                <div className="space-y-6">
                    <section>
                        <h3 className="text-lg font-semibold mb-2">Generated Code</h3>
                        <pre className="bg-[#2d2f39] rounded-lg p-4 overflow-x-auto whitespace-pre-wrap">{plan.generated_code}</pre>
                    </section>

                    <section>
                        <h3 className="text-lg font-semibold mb-2">Reviewer Feedback</h3>
                        <pre className="bg-[#2d2f39] rounded-lg p-4 overflow-x-auto whitespace-pre-wrap">{plan.reviewed_code}</pre>
                    </section>

                    <section>
                        <h3 className="text-lg font-semibold mb-2">Testing Report</h3>
                        <pre className="bg-[#2d2f39] rounded-lg p-4 overflow-x-auto whitespace-pre-wrap">{plan.testing_report}</pre>
                    </section>

                    <section>
                        <h3 className="text-lg font-semibold mb-2">Explanation</h3>
                        <pre className="bg-[#2d2f39] rounded-lg p-4 overflow-x-auto whitespace-pre-wrap">{plan.explanation}</pre>
                    </section>
                </div>
            ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{plan}</ReactMarkdown>
            )}

        </div>

    );

}

export default PlannerCard;