const API = "http://127.0.0.1:8000";


export async function generatePlan(prompt) {

    const response = await fetch(`${API}/plan`, {

        method: "POST",

        headers: {
            "Content-Type": "application/json",
        },

        body: JSON.stringify({
            message: prompt,
        }),

    });

    const data = await response.json();

    return data.plan;
}