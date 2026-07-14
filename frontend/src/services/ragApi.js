import axios from "axios";

const API = axios.create({
    baseURL: "http://127.0.0.1:8000",
});

export async function uploadRagDocuments(files, onProgress) {
    const formData = new FormData();

    files.forEach((file) => {
        formData.append("files", file);
    });

    const response = await API.post("/upload", formData, {
        headers: {
            "Content-Type": "multipart/form-data",
        },
        onUploadProgress: onProgress,
    });

    return response.data;
}

export async function queryRagDocuments(question) {
    const response = await API.post("/query", {
        question,
    });

    return response.data;
}