import React, { useState } from 'react';
import { useAuth } from '../auth/useAuth';
import { FaLayerGroup, FaEnvelope, FaLock, FaEye, FaEyeSlash, FaArrowRight, FaSpinner, FaExclamationTriangle } from 'react-icons/fa';

export default function Login({ setView }) {
  const { login } = useAuth();
  const [email, setEmail] = useState('user@example.com');
  const [password, setPassword] = useState('password123');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in all fields.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      await login(email, password);
      if (setView) setView('dashboard');
      else window.location.href = '/dashboard';
    } catch (err) {
      setError(err.message || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans flex items-center justify-center p-6 selection:bg-cyan-500 selection:text-white">
      <div className="w-full max-w-md bg-slate-950 border border-slate-800/80 rounded-2xl p-8 shadow-2xl space-y-6">
        {/* Logo */}
        <div className="text-center">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white text-xl mx-auto mb-3 shadow-lg shadow-cyan-500/20">
            <FaLayerGroup />
          </div>
          <h2 className="text-2xl font-black text-white tracking-tight">Welcome back</h2>
          <p className="text-xs text-slate-400 mt-1">Sign in to your AIForge developer workspace</p>
        </div>

        {error && (
          <div className="p-3 bg-rose-950/60 border border-rose-500/30 rounded-xl text-xs text-rose-300 flex items-center gap-2">
            <FaExclamationTriangle className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs font-sans">
          <div>
            <label className="text-slate-300 font-semibold block mb-1.5">Email</label>
            <div className="relative">
              <FaEnvelope className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@example.com"
                required
                className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-slate-300 font-semibold">Password</label>
              <button
                type="button"
                onClick={() => setView ? setView('forgot-password') : (window.location.href = '/forgot-password')}
                className="text-[11px] text-cyan-400 hover:underline"
              >
                Forgot password?
              </button>
            </div>
            <div className="relative">
              <FaLock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••••"
                required
                className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-10 py-2.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
              >
                {showPassword ? <FaEyeSlash /> : <FaEye />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? <FaSpinner className="animate-spin" /> : <FaArrowRight />}
            <span>{loading ? 'Signing in...' : 'Sign In'}</span>
          </button>
        </form>

        <div className="text-center pt-2 border-t border-slate-800/80 text-xs text-slate-400">
          Don't have an account?{' '}
          <button
            onClick={() => setView ? setView('register') : (window.location.href = '/register')}
            className="text-cyan-400 font-bold hover:underline"
          >
            Sign up
          </button>
        </div>
      </div>
    </div>
  );
}
