const API = "http://127.0.0.1:8000";

/**
 * Calls the end-to-end project generation pipeline and waits for the full
 * (non-streaming) result. Kept for backward compatibility.
 *
 * @param {string} prompt - e.g. "Build an E-Commerce Website"
 * @returns {Promise<{
 *   plan: string,
 *   architecture: string,
 *   frontend: string,
 *   backend: string,
 *   database: string,
 *   documentation: string,
 *   tests: string,
 *   review: string,
 *   github: string,
 *   error: string,
 * }>}
 */
export async function generateProject(prompt) {

    const response = await fetch(`${API}/generate-project`, {

        method: "POST",

        headers: {
            "Content-Type": "application/json",
        },

        body: JSON.stringify({ prompt }),

    });

    if (!response.ok) {
        throw new Error(`Project generation failed with status ${response.status}`);
    }

    const data = await response.json();

    return data;
}

/**
 * Calls the streaming (Server-Sent Events) version of the pipeline so the
 * UI can show live progress instead of freezing for several minutes.
 *
 * @param {string} prompt
 * @param {(event: { stage: string, percent: number, output: object }) => void} onProgress
 *   Called once per completed stage (and once more with stage "completed").
 * @returns {Promise<object>} the final merged result (same shape as generateProject).
 */
export async function generateProjectStream(prompt, onProgress) {

    const response = await fetch(`${API}/generate-project/stream`, {

        method: "POST",

        headers: {
            "Content-Type": "application/json",
        },

        body: JSON.stringify({ prompt }),

    });

    if (!response.ok || !response.body) {
        throw new Error(`Project generation failed with status ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = "";
    let finalResult = null;

    while (true) {

        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const rawEvents = buffer.split("\n\n");
        buffer = rawEvents.pop() || "";

        for (const rawEvent of rawEvents) {

            const line = rawEvent.trim();
            if (!line.startsWith("data:")) continue;

            const jsonText = line.slice(5).trim();
            if (!jsonText) continue;

            const event = JSON.parse(jsonText);

            if (onProgress) onProgress(event);

            if (event.stage === "completed") {
                finalResult = event.output;
            }

            if (event.stage === "error") {
                throw new Error(event.output?.error || "Project generation failed.");
            }

        }

    }

    return finalResult;
}

/**
 * Fetches all generated projects.
 */
export async function fetchProjects() {
    const response = await fetch(`${API}/projects`);
    if (!response.ok) {
        throw new Error(`Failed to fetch projects: ${response.status}`);
    }
    return response.json();
}

/**
 * Fetches files list recursively for a project.
 */
export async function fetchProjectFiles(projectName) {
    const response = await fetch(`${API}/project/${encodeURIComponent(projectName)}/files`);
    if (!response.ok) {
        throw new Error(`Failed to fetch project files: ${response.status}`);
    }
    return response.json();
}

/**
 * Fetches code content for a specific file inside a project.
 */
export async function fetchProjectFileContent(projectName, relativePath) {
    const response = await fetch(
        `${API}/project/${encodeURIComponent(projectName)}/file?path=${encodeURIComponent(relativePath)}`
    );
    if (!response.ok) {
        throw new Error(`Failed to fetch file content: ${response.status}`);
    }
    const data = await response.json();
    return data.content || "";
}

/**
 * Fetches the latest reflection.
 */
export async function fetchReflection() {
    const response = await fetch(`${API}/reflection`);
    if (!response.ok) {
        throw new Error(`Failed to fetch reflection: ${response.status}`);
    }
    return response.json();
}

/**
 * Fetches all lessons.
 */
export async function fetchLessons() {
    const response = await fetch(`${API}/lessons`);
    if (!response.ok) {
        throw new Error(`Failed to fetch lessons: ${response.status}`);
    }
    return response.json();
}

/**
 * Fetches dashboard trend metrics.
 */
export async function fetchMetrics() {
    const response = await fetch(`${API}/metrics`);
    if (!response.ok) {
        throw new Error(`Failed to fetch metrics: ${response.status}`);
    }
    return response.json();
}


