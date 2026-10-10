import React, { useState } from 'react';
import { resetPassword } from '../services/auth';
import { FaLayerGroup, FaLock, FaCheck, FaSpinner, FaExclamationTriangle } from 'react-icons/fa';

export default function ResetPassword({ setView }) {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      await resetPassword('demo_token', newPassword);
      setSuccess(true);
    } catch (err) {
      setError(err.message || 'Failed to update password.');
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
          <h2 className="text-2xl font-black text-white tracking-tight">Reset Your Password</h2>
          <p className="text-xs text-slate-400 mt-1">Enter your new account password below</p>
        </div>

        {error && (
          <div className="p-3 bg-rose-950/60 border border-rose-500/30 rounded-xl text-xs text-rose-300 flex items-center gap-2">
            <FaExclamationTriangle className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success ? (
          <div className="p-4 bg-emerald-950/60 border border-emerald-500/30 rounded-xl text-xs text-slate-200 text-center space-y-3">
            <p className="text-emerald-400 font-bold">Password updated successfully.</p>
            <button
              onClick={() => setView ? setView('login') : (window.location.href = '/login')}
              className="px-6 py-2.5 bg-gradient-to-r from-cyan-500 to-indigo-600 text-white rounded-xl text-xs font-bold"
            >
              Sign In Now
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 text-xs font-sans">
            <div>
              <label className="text-slate-300 font-semibold block mb-1.5">New Password</label>
              <div className="relative">
                <FaLock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••••••••"
                  required
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>
            </div>

            <div>
              <label className="text-slate-300 font-semibold block mb-1.5">Confirm New Password</label>
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

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? <FaSpinner className="animate-spin" /> : <FaCheck />}
              <span>{loading ? 'Updating...' : 'Update Password'}</span>
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
