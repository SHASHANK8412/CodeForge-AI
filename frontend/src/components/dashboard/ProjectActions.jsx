import React, { useState } from 'react';
import { FaTimes, FaExclamationTriangle, FaEdit, FaArchive, FaTrash } from 'react-icons/fa';

export function RenameModal({ project, onSave, onClose }) {
  const [name, setName] = useState(project ? project.project_name : '');

  if (!project) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 font-sans">
      <div className="bg-slate-950 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-white">
          <FaTimes />
        </button>

        <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
          <FaEdit className="text-cyan-400" /> Rename Project
        </h3>

        <div className="space-y-4">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Project Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 font-sans"
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs font-semibold text-slate-300 hover:text-white transition"
            >
              Cancel
            </button>
            <button
              onClick={() => onSave(project.generation_id, name)}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-cyan-600/20"
            >
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function ArchiveModal({ project, onConfirm, onClose }) {
  if (!project) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 font-sans">
      <div className="bg-slate-950 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl relative text-center">
        <button onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-white">
          <FaTimes />
        </button>

        <div className="w-12 h-12 bg-amber-500/10 text-amber-400 rounded-2xl flex items-center justify-center text-xl mx-auto mb-3 border border-amber-500/20">
          <FaArchive />
        </div>

        <h3 className="text-base font-bold text-white mb-2">Archive this project?</h3>
        <p className="text-xs text-slate-300 mb-6">
          The project <strong className="text-white">{project.project_name}</strong> will be hidden from the active dashboard, but can be restored at any time.
        </p>

        <div className="flex justify-center gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs font-semibold text-slate-300 hover:text-white transition"
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm(project.generation_id)}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-amber-600/20"
          >
            Archive Project
          </button>
        </div>
      </div>
    </div>
  );
}

export function DeleteModal({ project, onConfirm, onClose }) {
  const [typedName, setTypedName] = useState('');

  if (!project) return null;

  const isConfirmed = typedName.trim() === project.project_name;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 font-sans">
      <div className="bg-slate-950 border border-rose-500/30 rounded-2xl max-w-md w-full p-6 shadow-2xl relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-white">
          <FaTimes />
        </button>

        <div className="flex items-center gap-3 mb-4 border-b border-slate-800 pb-3">
          <div className="w-10 h-10 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center justify-center text-lg">
            <FaExclamationTriangle />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-white">Delete Project Permanently?</h3>
            <p className="text-xs text-rose-400 font-medium">This action cannot be undone.</p>
          </div>
        </div>

        <p className="text-xs text-slate-300 mb-4">
          Type <strong className="text-white font-mono bg-slate-900 px-2 py-0.5 rounded">{project.project_name}</strong> to confirm deletion:
        </p>

        <input
          type="text"
          value={typedName}
          onChange={(e) => setTypedName(e.target.value)}
          placeholder={project.project_name}
          className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-rose-500 font-mono mb-6"
        />

        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs font-semibold text-slate-300 hover:text-white transition"
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm(project.generation_id)}
            disabled={!isConfirmed}
            className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-rose-600/20 disabled:opacity-40"
          >
            Delete Permanently
          </button>
        </div>
      </div>
    </div>
  );
}
