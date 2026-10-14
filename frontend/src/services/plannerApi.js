import { BACKEND_URL } from '../config/backend';
import { getActiveSessionId } from "../utils/chatStorage";

const API = `${BACKEND_URL}`;


export async function generatePlan(prompt, sessionId = getActiveSessionId()) {

    const response = await fetch(`${API}/generate`, {

        method: "POST",

        headers: {
            "Content-Type": "application/json",
        },

        body: JSON.stringify({
            prompt: prompt,
            session_id: sessionId,
        }),

    });

    const data = await response.json();

    return data;
}