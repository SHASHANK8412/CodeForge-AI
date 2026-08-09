import React, { useState } from 'react';
import { useAuth } from '../auth/useAuth';
import { FaUser, FaLock, FaKey, FaShieldAlt, FaTrash, FaCheck, FaExclamationTriangle } from 'react-icons/fa';

export default function Settings({ setView, activeSubTab = 'profile' }) {
  const { user } = useAuth();
  const [tab, setTab] = useState(activeSubTab);
  const [name, setName] = useState(user?.name || 'Shashank');
  const [saved, setSaved] = useState(false);

  const handleSaveProfile = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6 selection:bg-cyan-500 selection:text-white">
      <div className="max-w-5xl mx-auto border-b border-slate-800 pb-4">
        <h1 className="text-2xl font-black text-white tracking-tight">Account & Security Settings</h1>
        <p className="text-xs text-slate-400 mt-1">Manage your AIForge user profile, security policies, and API keys.</p>
      </div>

      <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Navigation Sidebar */}
        <div className="space-y-1 font-sans text-xs">
          <button
            onClick={() => setTab('profile')}
            className={`w-full text-left px-3.5 py-2.5 rounded-xl font-bold transition flex items-center gap-2 ${
              tab === 'profile' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
            }`}
          >
            <FaUser /> Profile
          </button>
          <button
            onClick={() => setTab('security')}
            className={`w-full text-left px-3.5 py-2.5 rounded-xl font-bold transition flex items-center gap-2 ${
              tab === 'security' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
            }`}
          >
            <FaLock /> Security
          </button>
          <button
            onClick={() => setView ? setView('api-keys') : setTab('apikeys')}
            className={`w-full text-left px-3.5 py-2.5 rounded-xl font-bold transition flex items-center gap-2 ${
              tab === 'apikeys' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
            }`}
          >
            <FaKey /> API Keys
          </button>
          <button
            onClick={() => setTab('danger')}
            className={`w-full text-left px-3.5 py-2.5 rounded-xl font-bold transition flex items-center gap-2 ${
              tab === 'danger' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'text-slate-400 hover:bg-slate-900 hover:text-rose-400'
            }`}
          >
            <FaTrash /> Danger Zone
          </button>
        </div>

        {/* Tab Panel Content */}
        <div className="md:col-span-3 bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl space-y-6">
          {tab === 'profile' && (
            <form onSubmit={handleSaveProfile} className="space-y-4 text-xs font-sans">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-2">Profile Information</h3>

              {saved && (
                <div className="p-3 bg-emerald-950/60 border border-emerald-500/30 rounded-xl text-xs text-emerald-400 flex items-center gap-2">
                  <FaCheck /> Profile changes saved successfully.
                </div>
              )}

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 font-sans"
                />
              </div>

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Email Address</label>
                <input
                  type="email"
                  value={user?.email || 'user@example.com'}
                  disabled
                  className="w-full max-w-md bg-slate-900/50 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-500 font-mono cursor-not-allowed"
                />
                <p className="text-[11px] text-slate-500 mt-1">Email address is verified and managed by AIForge Auth.</p>
              </div>

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Account Created</label>
                <input
                  type="text"
                  value={user?.created_at || 'August 9, 2026'}
                  disabled
                  className="w-full max-w-md bg-slate-900/50 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-500 font-mono cursor-not-allowed"
                />
              </div>

              <button
                type="submit"
                className="px-6 py-2.5 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white rounded-xl font-bold transition shadow-lg shadow-cyan-500/20"
              >
                Save Changes
              </button>
            </form>
          )}

          {tab === 'security' && (
            <div className="space-y-6 text-xs font-sans">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-2">Security & Credentials</h3>

              <div className="space-y-4">
                <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-white">Password</h4>
                    <p className="text-slate-400 text-[11px]">Last changed: Recently</p>
                  </div>
                  <button
                    onClick={() => setView ? setView('forgot-password') : (window.location.href = '/forgot-password')}
                    className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-400 hover:text-white rounded-lg font-semibold transition"
                  >
                    Change Password
                  </button>
                </div>

                <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-white">Active Sessions</h4>
                    <p className="text-slate-400 text-[11px]">Current session: Windows Chrome Edge CDN</p>
                  </div>
                  <span className="px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-mono font-bold">Active</span>
                </div>

                <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-white">Two-Factor Authentication (2FA)</h4>
                    <p className="text-slate-400 text-[11px]">Add an extra layer of security with TOTP authentication apps.</p>
                  </div>
                  <span className="px-2.5 py-1 bg-slate-800 text-slate-500 rounded text-[10px] font-mono uppercase">Coming Soon</span>
                </div>
              </div>
            </div>
          )}

          {tab === 'danger' && (
            <div className="space-y-4 text-xs font-sans">
              <h3 className="text-sm font-bold text-rose-400 uppercase tracking-wider border-b border-rose-500/30 pb-2 flex items-center gap-2">
                <FaExclamationTriangle /> Danger Zone
              </h3>
              <p className="text-slate-300">
                Permanently delete your AIForge account and associated project code repositories.
              </p>
              <button className="px-4 py-2.5 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-xl transition shadow-lg shadow-rose-600/20">
                Delete Account
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
