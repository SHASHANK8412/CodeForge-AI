import axios from "axios";

const API = axios.create({
    baseURL: "http://127.0.0.1:8000",
});

export const sendMessage = async (message) => {
    try {
        const response = await API.post("/chat", {
            message: message,
        });

        return response.data.response;
    } catch (error) {
        console.error("API Error:", error);
        return "Something went wrong!";
    }
};