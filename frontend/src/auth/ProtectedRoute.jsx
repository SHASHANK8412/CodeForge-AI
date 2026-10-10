import React from 'react';
import { useAuth } from './useAuth';
import { FaSpinner, FaLock } from 'react-icons/fa';

export default function ProtectedRoute({ children, onRedirectLogin }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans flex flex-col items-center justify-center p-6 space-y-4">
        <FaSpinner className="w-8 h-8 text-cyan-400 animate-spin" />
        <h3 className="text-base font-bold tracking-wide">Checking your session...</h3>
        <p className="text-xs text-slate-500 font-mono">Authenticating with AIForge security token...</p>
      </div>
    );
  }

  if (!user) {
    if (onRedirectLogin) {
      onRedirectLogin();
      return null;
    }
    return (
      <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans flex flex-col items-center justify-center p-6 space-y-4 text-center">
        <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center text-xl">
          <FaLock />
        </div>
        <h3 className="text-lg font-bold">Authentication Required</h3>
        <p className="text-xs text-slate-400 max-w-sm">
          Please sign in to access protected projects, code workspaces, quality reports, and deployments.
        </p>
        <button
          onClick={() => onRedirectLogin && onRedirectLogin()}
          className="px-6 py-2.5 bg-gradient-to-r from-cyan-500 to-indigo-600 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-cyan-500/20"
        >
          Sign In to AIForge
        </button>
      </div>
    );
  }

  return children;
}
