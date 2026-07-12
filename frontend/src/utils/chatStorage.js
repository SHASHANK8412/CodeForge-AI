const SESSION_KEY = "aiforge_session_id";
const MESSAGES_PREFIX = "aiforge_messages:";
const SESSION_INDEX_KEY = "aiforge_session_index";

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

export function startNewSession() {
	const sessionId = createSessionId();
	localStorage.setItem(SESSION_KEY, sessionId);
	return sessionId;
}

export function getChatStorageKey(sessionId) {
	return `${MESSAGES_PREFIX}${sessionId}`;
}

function getSessionIdsFromStorage() {
	return Object.keys(localStorage)
		.filter((key) => key.startsWith(MESSAGES_PREFIX))
		.map((key) => key.replace(MESSAGES_PREFIX, ""));
}

function getSessionIndex() {
	const savedIndex = localStorage.getItem(SESSION_INDEX_KEY);
	return savedIndex ? JSON.parse(savedIndex) : {};
}

function saveSessionIndex(index) {
	localStorage.setItem(SESSION_INDEX_KEY, JSON.stringify(index));
}

export function getChatSessions() {
	const index = getSessionIndex();

	return getSessionIdsFromStorage()
		.map((sessionId) => {
			const messages = getSavedMessages(sessionId);
			const firstUserMessage = messages.find((message) => message.sender === "user");
			const metadata = index[sessionId] || {};

			return {
				sessionId,
				messageCount: messages.length,
				label:
					firstUserMessage?.text?.trim().slice(0, 42) ||
					`Chat ${sessionId.slice(0, 8)}`,
				updatedAt: metadata.updatedAt || 0,
			};
		})
		.sort((left, right) => right.updatedAt - left.updatedAt);
}

export function getSavedMessages(sessionId) {
	const storageKey = getChatStorageKey(sessionId);
	const savedMessages = localStorage.getItem(storageKey);
	return savedMessages ? JSON.parse(savedMessages) : [];
}

export function saveMessages(sessionId, messages) {
	const storageKey = getChatStorageKey(sessionId);
	localStorage.setItem(storageKey, JSON.stringify(messages));

	const index = getSessionIndex();
	const firstUserMessage = messages.find((message) => message.sender === "user");
	index[sessionId] = {
		updatedAt: Date.now(),
		label:
			firstUserMessage?.text?.trim().slice(0, 42) ||
			`Chat ${sessionId.slice(0, 8)}`,
	};
	saveSessionIndex(index);
}

export function clearSessionMessages(sessionId) {
	localStorage.removeItem(getChatStorageKey(sessionId));

	const index = getSessionIndex();
	delete index[sessionId];
	saveSessionIndex(index);
}

export function loadSessionMessages(sessionId) {
	localStorage.setItem(SESSION_KEY, sessionId);
	return getSavedMessages(sessionId);
}

export function resetChatSession() {
	const previousSessionId = localStorage.getItem(SESSION_KEY);

	if (previousSessionId) {
		clearSessionMessages(previousSessionId);
	}

	return startNewSession();
}
