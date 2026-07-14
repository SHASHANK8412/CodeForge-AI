const SESSION_KEY = "aiforge_active_conversation_id";

function createSessionId() {
	if (window.crypto?.randomUUID) {
		return window.crypto.randomUUID();
	}

	return `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function getActiveSessionId() {
	const savedSessionId = localStorage.getItem(SESSION_KEY);

	if (savedSessionId) {
		return savedSessionId;
	}

	const sessionId = createSessionId();
	localStorage.setItem(SESSION_KEY, sessionId);
	return sessionId;
}

export function loadSessionMessages(sessionId) {
	localStorage.setItem(SESSION_KEY, sessionId);
	return [];
}

export function setActiveSessionId(sessionId) {
	if (sessionId) {
		localStorage.setItem(SESSION_KEY, sessionId);
		return sessionId;
	}

	localStorage.removeItem(SESSION_KEY);
	return "";
}

export function clearActiveSessionId() {
	localStorage.removeItem(SESSION_KEY);
}

export function resetChatSession() {
	localStorage.removeItem(SESSION_KEY);
	return createSessionId();
}

export function getChatSessions() {
	return [];
}

export function getSavedMessages() {
	return [];
}

export function saveMessages() {}

export function clearSessionMessages() {}
