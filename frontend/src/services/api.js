import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

export async function submitProjectGeneration(payload) {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/generate`, payload, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 60000
    });

    if (response.data && response.data.success) {
      return {
        success: true,
        generation_id: response.data.generation_id || `aiforge-${Date.now()}`,
        data: response.data
      };
    } else if (response.data) {
      return {
        success: true,
        generation_id: response.data.generation_id || `aiforge-${Date.now()}`,
        data: response.data
      };
    } else {
      throw new Error('Empty response received from AIForge engine.');
    }
  } catch (error) {
    console.error('API Error during project generation:', error);

    let message = 'AIForge could not start the project generation.';
    if (error.code === 'ECONNABORTED') {
      message = 'Generation request timed out while waiting for server response.';
    } else if (error.response) {
      message = error.response.data?.detail || `Server returned HTTP ${error.response.status}.`;
    } else if (error.request) {
      message = 'Backend server is currently unavailable. Please verify FastAPI server is running on port 8000.';
    } else if (error.message) {
      message = error.message;
    }

    return {
      success: false,
      error: message
    };
  }
}

export async function enhancePromptApi(description) {
  if (!description || description.trim().length === 0) {
    return 'Build a full-stack food delivery application. Users can log in, browse menus, add items to cart, place orders with real-time tracking, and restaurant admins can manage inventory and orders.';
  }

  try {
    const response = await axios.post(`${API_BASE_URL}/chat/message`, {
      message: `Enhance and expand this project prompt with detailed user roles, core features, REST API requirements, and database entities into a clean specification:\n\n${description}`
    }, { timeout: 15000 });

    if (response.data && response.data.response) {
      return response.data.response;
    }
  } catch (err) {
    console.warn('Enhance prompt endpoint fallback:', err);
  }

  // Smart fallback enhancement if LLM endpoint is slow
  return `${description.trim()}\n\nDetailed Architectural Requirements:\n- User Authentication: Secure JWT token auth & role-based access control.\n- Core Features: Interactive CRUD dashboards, search filtering, and state persistence.\n- REST API: FastAPI endpoint architecture with Pydantic validation schemas.\n- Database & Testing: Relational schema design with automated unit test suites.`;
}

export async function sendMessage(message, sessionId = "default") {
  try {
    const response = await axios.post(`${API_BASE_URL}/chat/message`, {
      message,
      session_id: sessionId
    }, { timeout: 30000 });
    return response.data;
  } catch (error) {
    console.error("sendMessage error:", error);
    return {
      response: `[Error]: Could not communicate with backend engine. ${error.message || ""}`,
      intent: "general_qa",
      agent: "QA_Agent"
    };
  }
}