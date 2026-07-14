import axios from "axios";

const API = axios.create({
    baseURL: "http://127.0.0.1:8000",
});

export async function createConversation({ title = null, firstMessage = null } = {}) {
    const response = await API.post("/chat/new", {
        title,
        first_message: firstMessage,
    });

    return response.data.conversation;
}

export async function listConversations({ limit = 100, offset = 0, search = "" } = {}) {
    const response = await API.get("/chat/list", {
        params: {
            limit,
            offset,
            search: search || undefined,
        },
    });

    return response.data.conversations || [];
}

export async function getConversationHistory(conversationId, limit = 100) {
    const response = await API.get(`/chat/history/${conversationId}`, {
        params: {
            limit,
        },
    });

    return response.data;
}

export async function renameConversation(conversationId, title) {
    const response = await API.put(`/chat/title/${conversationId}`, {
        title,
    });

    return response.data.conversation;
}

export async function deleteConversation(conversationId) {
    const response = await API.delete(`/chat/${conversationId}`);
    return response.data;
}

export async function sendConversationMessage(conversationId, message) {
    const response = await API.post("/chat/message", {
        conversation_id: conversationId,
        message,
    });

    return response.data;
}