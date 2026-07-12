import axios from "axios";
import { getActiveSessionId } from "../utils/chatStorage";

const API = axios.create({
    baseURL: "http://127.0.0.1:8000",
});

export const sendMessage = async (message, sessionId = getActiveSessionId()) => {

    const response = await API.post("/chat", {
        message,
        session_id: sessionId,
    });

    return response.data.response;
};