import React from 'react';
import { FaCheckCircle, FaExclamationTriangle, FaTimes } from 'react-icons/fa';

export default function ToastNotifications({ notification, onClose }) {
  if (!notification) return null;

  const isError = notification.type === 'error';

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-bounce font-sans">
      <div className={`p-4 rounded-xl border shadow-2xl flex items-center gap-3 text-xs max-w-sm ${
        isError ? 'bg-rose-950 border-rose-500/40 text-rose-200' : 'bg-slate-950 border-emerald-500/40 text-slate-100'
      }`}>
        {isError ? (
          <FaExclamationTriangle className="w-4 h-4 text-rose-400 shrink-0" />
        ) : (
          <FaCheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
        )}

        <span className="flex-1 leading-snug">{notification.text}</span>

        <button onClick={onClose} className="p-1 text-slate-400 hover:text-white">
          <FaTimes className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}
