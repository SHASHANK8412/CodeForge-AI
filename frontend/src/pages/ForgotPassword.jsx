import React, { useState } from 'react';
import { requestPasswordReset } from '../services/auth';
import { FaLayerGroup, FaEnvelope, FaPaperPlane, FaSpinner, FaArrowLeft } from 'react-icons/fa';

export default function ForgotPassword({ setView }) {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) return;

    setLoading(true);
    await requestPasswordReset(email);
    setLoading(false);
    setSent(true);
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans flex items-center justify-center p-6 selection:bg-cyan-500 selection:text-white">
      <div className="w-full max-w-md bg-slate-950 border border-slate-800/80 rounded-2xl p-8 shadow-2xl space-y-6">
        <div className="text-center">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white text-xl mx-auto mb-3 shadow-lg shadow-cyan-500/20">
            <FaLayerGroup />
          </div>
          <h2 className="text-2xl font-black text-white tracking-tight">Forgot your password?</h2>
          <p className="text-xs text-slate-400 mt-1">Enter your email and we'll help you reset your password.</p>
        </div>

        {sent ? (
          <div className="p-4 bg-emerald-950/60 border border-emerald-500/30 rounded-xl text-xs text-slate-200 text-center space-y-3">
            <p>If an account exists for <strong className="text-emerald-400 font-mono">{email}</strong>, you will receive password reset instructions.</p>
            <button
              onClick={() => setView ? setView('login') : (window.location.href = '/login')}
              className="px-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-cyan-400 hover:text-white font-bold"
            >
              Back to Sign In
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 text-xs font-sans">
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

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? <FaSpinner className="animate-spin" /> : <FaPaperPlane />}
              <span>{loading ? 'Sending link...' : 'Send Reset Link'}</span>
            </button>
          </form>
        )}

        <div className="text-center pt-2 border-t border-slate-800/80 text-xs text-slate-400">
          <button
            onClick={() => setView ? setView('login') : (window.location.href = '/login')}
            className="text-slate-400 hover:text-white inline-flex items-center gap-1.5 font-semibold"
          >
            <FaArrowLeft /> Back to Login
          </button>
        </div>
      </div>
    </div>
  );
}
