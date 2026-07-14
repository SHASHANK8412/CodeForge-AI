import axios from "axios";
import { getActiveSessionId } from "../utils/chatStorage";
import { sendConversationMessage } from "./conversationApi";

const API = axios.create({
    baseURL: "http://127.0.0.1:8000",
});

export const sendMessage = async (message, sessionId = getActiveSessionId()) => {
    const response = await sendConversationMessage(sessionId || null, message);
    return response;
};