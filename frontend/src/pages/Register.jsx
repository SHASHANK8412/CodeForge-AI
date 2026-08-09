import React, { useState } from 'react';
import { useAuth } from '../auth/useAuth';
import { FaLayerGroup, FaUser, FaEnvelope, FaLock, FaCheck, FaSpinner, FaExclamationTriangle } from 'react-icons/fa';

export default function Register({ setView }) {
  const { register } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [agreed, setAgreed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name || !email || !password || !confirmPassword) {
      setError('Please fill in all required fields.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (!agreed) {
      setError('You must agree to the Terms and Privacy Policy.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      await register(name, email, password);
      if (setView) setView('dashboard');
      else window.location.href = '/dashboard';
    } catch (err) {
      setError(err.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans flex items-center justify-center p-6 selection:bg-cyan-500 selection:text-white">
      <div className="w-full max-w-md bg-slate-950 border border-slate-800/80 rounded-2xl p-8 shadow-2xl space-y-6">
        <div className="text-center">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white text-xl mx-auto mb-3 shadow-lg shadow-cyan-500/20">
            <FaLayerGroup />
          </div>
          <h2 className="text-2xl font-black text-white tracking-tight">Create your account</h2>
          <p className="text-xs text-slate-400 mt-1">Start building autonomous software with AIForge</p>
        </div>

        {error && (
          <div className="p-3 bg-rose-950/60 border border-rose-500/30 rounded-xl text-xs text-rose-300 flex items-center gap-2">
            <FaExclamationTriangle className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs font-sans">
          <div>
            <label className="text-slate-300 font-semibold block mb-1.5">Full Name</label>
            <div className="relative">
              <FaUser className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Shashank"
                required
                className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-sans"
              />
            </div>
          </div>

          <div>
            <label className="text-slate-300 font-semibold block mb-1.5">Email Address</label>
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
            <label className="text-slate-300 font-semibold block mb-1.5">Password</label>
            <div className="relative">
              <FaLock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••••"
                required
                className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="text-slate-300 font-semibold block mb-1.5">Confirm Password</label>
            <div className="relative">
              <FaLock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••••••••"
                required
                className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
          </div>

          <label className="flex items-center gap-2 text-slate-300 cursor-pointer pt-1">
            <input
              type="checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
              className="rounded bg-slate-900 border-slate-800 text-cyan-500 focus:ring-0"
            />
            <span>I agree to the Terms and Privacy Policy</span>
          </label>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? <FaSpinner className="animate-spin" /> : <FaCheck />}
            <span>{loading ? 'Creating account...' : 'Create Account'}</span>
          </button>
        </form>

        <div className="text-center pt-2 border-t border-slate-800/80 text-xs text-slate-400">
          Already have an account?{' '}
          <button
            onClick={() => setView ? setView('login') : (window.location.href = '/login')}
            className="text-cyan-400 font-bold hover:underline"
          >
            Sign in
          </button>
        </div>
      </div>
    </div>
  );
}
