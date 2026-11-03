import React, { createContext, useState, useEffect } from 'react';
import { fetchCurrentUser, loginUser, registerUser, logoutUser } from '../services/auth';

export const AuthContext = createContext({
  user: null,
  loading: true,
  login: async () => {},
  register: async () => {},
  logout: async () => {}
});

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const initAuth = async () => {
      setLoading(true);
      // While the backend cannot be reached, keep the session and retry every 3 s (it may be starting up).
      for (;;) {
        try {
          const curr = await fetchCurrentUser();
          if (!cancelled) setUser(curr);
          break;
        } catch {
          await new Promise((resolve) => setTimeout(resolve, 3000));
          if (cancelled) return;
        }
      }
      if (!cancelled) setLoading(false);
    };

    initAuth();

    // Any API call answered 401 (expired or missing token) signs the user out of the UI.
    const onUnauthorized = () => setUser(null);
    window.addEventListener('aiforge:unauthorized', onUnauthorized);
    return () => {
      cancelled = true;
      window.removeEventListener('aiforge:unauthorized', onUnauthorized);
    };
  }, []);

  const login = async (email, password) => {
    const res = await loginUser(email, password);
    if (res.user) {
      setUser(res.user);
    }
    return res;
  };

  const register = async (name, email, password) => {
    const res = await registerUser(name, email, password);
    if (res.user) {
      setUser(res.user);
    }
    return res;
  };

  const logout = async () => {
    await logoutUser();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
