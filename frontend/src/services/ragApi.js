import axios from "axios";

const API = axios.create({
    baseURL: "http://127.0.0.1:8000",
});

export async function uploadRagDocuments(files) {
    const formData = new FormData();

    files.forEach((file) => {
        formData.append("files", file);
    });

    const response = await API.post("/rag/upload", formData, {
        headers: {
            "Content-Type": "multipart/form-data",
        },
    });

    return response.data;
}

export async function queryRagDocuments(question) {
    const response = await API.post("/rag/query", {
        question,
    });

    return response.data;
}