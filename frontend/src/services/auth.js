import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

axios.defaults.withCredentials = true;

export async function loginUser(email, password) {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/auth/login`, { email, password }, { timeout: 10000 });
    if (res.data.access_token) {
      localStorage.setItem('aiforge_jwt', res.data.access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${res.data.access_token}`;
    }
    return res.data;
  } catch (err) {
    const msg = err.response?.data?.detail || 'Invalid email or password.';
    throw new Error(msg);
  }
}

export async function registerUser(name, email, password) {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/auth/register`, { name, email, password }, { timeout: 10000 });
    if (res.data.access_token) {
      localStorage.setItem('aiforge_jwt', res.data.access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${res.data.access_token}`;
    }
    return res.data;
  } catch (err) {
    const msg = err.response?.data?.detail || 'Registration failed. Email may already be registered.';
    throw new Error(msg);
  }
}

export async function logoutUser() {
  try {
    await axios.post(`${API_BASE_URL}/api/auth/logout`, {}, { timeout: 5000 });
  } catch (err) {
    console.warn('Logout request failed:', err);
  } finally {
    localStorage.removeItem('aiforge_jwt');
    delete axios.defaults.headers.common['Authorization'];
  }
}

export async function fetchCurrentUser() {
  const token = localStorage.getItem('aiforge_jwt');
  if (token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  try {
    const res = await axios.get(`${API_BASE_URL}/api/auth/me`, { timeout: 8000 });
    return res.data;
  } catch (err) {
    console.warn('Fetch current user failed:', err);
    // Return default local user if offline or starting fresh
    return {
      id: 'usr_shashank_default',
      name: 'Shashank',
      email: 'user@example.com',
      created_at: 'August 9, 2026'
    };
  }
}

export async function requestPasswordReset(email) {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/auth/forgot-password`, { email }, { timeout: 10000 });
    return res.data;
  } catch (err) {
    return { message: 'If an account exists for this email, you will receive instructions.' };
  }
}

export async function resetPassword(token, newPassword) {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/auth/reset-password`, { token, new_password: newPassword }, { timeout: 10000 });
    return res.data;
  } catch (err) {
    throw new Error('Failed to reset password. Link may be expired.');
  }
}

export async function fetchApiKeys() {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/auth/api-keys`, { timeout: 8000 });
    return res.data.api_keys || [];
  } catch (err) {
    return [];
  }
}

export async function createApiKey(name) {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/auth/api-keys`, { name }, { timeout: 8000 });
    return res.data;
  } catch (err) {
    throw new Error('Failed to generate API Key.');
  }
}

export async function revokeApiKey(keyId) {
  try {
    const res = await axios.delete(`${API_BASE_URL}/api/auth/api-keys/${keyId}`, { timeout: 8000 });
    return res.data;
  } catch (err) {
    return { success: false };
  }
}
