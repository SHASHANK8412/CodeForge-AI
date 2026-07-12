import { getActiveSessionId } from "../utils/chatStorage";

const API = "http://127.0.0.1:8000";


export async function generatePlan(prompt, sessionId = getActiveSessionId()) {

    const response = await fetch(`${API}/plan`, {

        method: "POST",

        headers: {
            "Content-Type": "application/json",
        },

        body: JSON.stringify({
            message: prompt,
            session_id: sessionId,
        }),

    });

    const data = await response.json();

    return data.plan;
}